"""Pluggable LLM client.

Default provider is `mock`: a deterministic, offline narrator that turns
structured query results into natural-language answers. No API key required.

To wire a real model later, set LLM_PROVIDER + the matching key in .env and
implement the request inside CatalystClient / OpenAIClient below. The rest of
the app talks only to the LLMClient.complete() interface, so nothing else
changes when you swap providers.
"""
from __future__ import annotations

import re

from ..config import settings


class LLMClient:
    provider = "base"
    available = False

    def complete(self, system: str, prompt: str, **kw) -> str:
        raise NotImplementedError

    def narrate(self, question: str, findings: str, language: str = "en") -> str:
        """Turn structured findings into a natural answer."""
        raise NotImplementedError


class MockLLM(LLMClient):
    """Offline fallback — templated, deterministic natural language."""
    provider = "mock"
    available = True

    def complete(self, system: str, prompt: str, **kw) -> str:
        return prompt

    def narrate(self, question: str, findings: str, language: str = "en") -> str:
        # findings is already a human-readable answer built by the NLQ engine;
        # the mock layer just returns it. A real LLM would rephrase/expand it.
        return findings


class CatalystClient(LLMClient):
    """Catalyst LLM serving (GLM 4.7 / Qwen 3.6) via QuickML.

    Catalyst exposes chat models through QuickML's LLM-serving endpoints, not
    through Zia — Zia only offers vision and text-analytics services. The model
    is called with QuickML's generic predict(endpoint_key, input_data).
    """
    provider = "catalyst"

    def __init__(self):
        # Reachable either through the in-function SDK (project credentials)
        # or a plain REST URL with a QuickML-scoped OAuth token.
        self.available = bool(settings.glm_endpoint_url or settings.use_catalyst)
        # Last GLM failure, surfaced by /api/health. Without this a broken GLM
        # is indistinguishable from a working one that just fell back to mock.
        self.last_error: str | None = None

    @staticmethod
    def _extract_text(resp) -> str:
        """Pull the generated text out of a QuickML LLM response.

        The exact envelope varies by serving config, so probe the common
        shapes rather than assuming one and silently returning junk.
        """
        if isinstance(resp, str):
            return resp
        if not isinstance(resp, dict):
            return str(resp)
        for key in ("output", "generated_text", "text", "response", "content", "answer"):
            val = resp.get(key)
            if isinstance(val, str) and val.strip():
                return val
        choices = resp.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                msg = first.get("message")
                if isinstance(msg, dict) and msg.get("content"):
                    return str(msg["content"])
                if first.get("text"):
                    return str(first["text"])
        data = resp.get("data")
        if isinstance(data, dict):
            return CatalystClient._extract_text(data)
        return ""

    def complete(self, system: str, prompt: str, **kw) -> str:
        """Returns "" on failure — never the prompt, which callers would
        otherwise hand back to the user as if it were a generated answer."""
        if not self.available:
            return ""
        payload = {
            "model": settings.glm_model_id,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": kw.get("max_tokens", 800),
            "temperature": kw.get("temperature", 0.2),
            "stream": False,
            # This model emits its chain-of-thought into `response` unless
            # thinking is off, which makes generate_query's JSON unparseable.
            "chat_template_kwargs": {"enable_thinking": False},
        }
        headers = {"Content-Type": "application/json",
                   "CATALYST-ORG": settings.catalyst_org_id}
        try:
            resp = self._via_sdk(payload, headers)
            if resp is None:
                resp = self._via_rest(payload, headers)
            text = self._extract_text(resp)
            if not text:
                self.last_error = f"unrecognised LLM response envelope: {str(resp)[:200]}"
            return text
        except Exception as e:
            self.last_error = f"{type(e).__name__}: {e}"[:300]
            return ""

    @staticmethod
    def _via_sdk(payload, headers):
        """Preferred inside a Catalyst function: the SDK authenticates as the
        project, which carries QuickML access an OAuth refresh token lacks.
        Returns None when the SDK isn't usable so the caller can fall back."""
        try:
            from ..catalyst_ctx import init_sdk
            from zcatalyst_sdk._constants import CatalystService
            from zcatalyst_sdk._http_client import AuthorizedHttpClient
            client = AuthorizedHttpClient(init_sdk())
        except Exception:
            return None
        resp = client.request(method="POST", path="/glm/chat", json=payload,
                              headers=headers,
                              catalyst_service=CatalystService.QUICK_ML)
        return getattr(resp, "response_json", None) or {}

    @staticmethod
    def _via_rest(payload, headers):
        import json
        import urllib.error
        import urllib.request

        from ..catalyst_store import get_store

        if not settings.glm_endpoint_url:
            raise RuntimeError("no GLM route: SDK unavailable and "
                               "GLM_ENDPOINT_URL unset")
        hdrs = dict(headers)
        hdrs["Authorization"] = f"Bearer {get_store()._get_token()}"
        req = urllib.request.Request(
            settings.glm_endpoint_url,
            data=json.dumps(payload).encode("utf-8"), method="POST",
            headers=hdrs)
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")[:250]
            raise RuntimeError(f"GLM HTTP {e.code}: {body}") from None

    def narrate(self, question: str, findings: str, language: str = "en") -> str:
        if not self.available:
            return findings
        lang = "Kannada" if language == "kn" else "English"
        sys_prompt = (
            "You are a police crime-intelligence analyst for Karnataka Police. "
            f"Rephrase the findings into a concise, professional answer in {lang}. "
            "Do not invent facts. Use the data provided."
        )
        return (self.complete(sys_prompt, f"Question: {question}\n\nFindings:\n{findings}")
                or findings)

    def generate_query(self, question: str, schema_context: str) -> dict:
        import json
        resp = self.complete(schema_context, question, temperature=0.1)
        if not resp:
            return {"intent": "unknown", "zcql": "",
                    "reasoning": f"GLM unavailable: {self.last_error or 'no response'}"}
        # GLM often wraps JSON in ```json fences despite the instruction.
        cleaned = re.sub(r"^\s*```(?:json)?|```\s*$", "", resp.strip())
        try:
            return json.loads(cleaned)
        except (json.JSONDecodeError, TypeError):
            return {"intent": "unknown", "zcql": "", "reasoning": resp}


class OpenAIClient(LLMClient):
    """Slot for OpenAI. Falls back to mock until an API key is set."""
    provider = "openai"

    def __init__(self):
        self.available = bool(settings.openai_api_key)
        self.last_error: str | None = None

    def complete(self, system: str, prompt: str, **kw) -> str:
        if not self.available:
            return ""
        try:
            from openai import OpenAI  # optional dependency
            client = OpenAI(api_key=settings.openai_api_key)
            resp = client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": prompt}],
                temperature=0.2,
            )
            return resp.choices[0].message.content or ""
        except Exception as e:
            self.last_error = f"{type(e).__name__}: {e}"[:300]
            return ""

    def narrate(self, question: str, findings: str, language: str = "en") -> str:
        if not self.available:
            return findings
        lang = "Kannada" if language == "kn" else "English"
        sys = ("You are a police crime-intelligence analyst. Rephrase the findings "
               f"into a concise, professional answer in {lang}. Do not invent facts.")
        return (self.complete(sys, f"Question: {question}\n\nFindings:\n{findings}")
                or findings)


_INSTANCES = {"mock": MockLLM, "catalyst": CatalystClient, "openai": OpenAIClient}


def get_llm() -> LLMClient:
    cls = _INSTANCES.get(settings.llm_provider, MockLLM)
    inst = cls()
    # if a real provider is selected but not configured, degrade to mock
    if not getattr(inst, "available", False):
        return MockLLM()
    return inst
