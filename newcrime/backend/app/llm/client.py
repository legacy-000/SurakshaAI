"""Pluggable LLM client.

Default provider is `mock`: a deterministic, offline narrator that turns
structured query results into natural-language answers. No API key required.

To wire a real model later, set LLM_PROVIDER + the matching key in .env and
implement the request inside CatalystClient / OpenAIClient below. The rest of
the app talks only to the LLMClient.complete() interface, so nothing else
changes when you swap providers.
"""
from __future__ import annotations

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
    """Slot for Zoho Catalyst LLM. Falls back to mock until configured."""
    provider = "catalyst"

    def __init__(self):
        self.available = bool(settings.catalyst_api_key and settings.catalyst_endpoint)

    def complete(self, system: str, prompt: str, **kw) -> str:
        if not self.available:
            return prompt
        # TODO: call Catalyst endpoint with settings.catalyst_api_key.
        raise NotImplementedError("Wire Catalyst LLM call here.")

    def narrate(self, question: str, findings: str, language: str = "en") -> str:
        if not self.available:
            return findings
        return self.complete("You are a crime-intelligence analyst.", findings)


class OpenAIClient(LLMClient):
    """Slot for OpenAI. Falls back to mock until an API key is set."""
    provider = "openai"

    def __init__(self):
        self.available = bool(settings.openai_api_key)

    def complete(self, system: str, prompt: str, **kw) -> str:
        if not self.available:
            return prompt
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
        except Exception:
            return prompt

    def narrate(self, question: str, findings: str, language: str = "en") -> str:
        if not self.available:
            return findings
        lang = "Kannada" if language == "kn" else "English"
        sys = ("You are a police crime-intelligence analyst. Rephrase the findings "
               f"into a concise, professional answer in {lang}. Do not invent facts.")
        return self.complete(sys, f"Question: {question}\n\nFindings:\n{findings}")


_INSTANCES = {"mock": MockLLM, "catalyst": CatalystClient, "openai": OpenAIClient}


def get_llm() -> LLMClient:
    cls = _INSTANCES.get(settings.llm_provider, MockLLM)
    inst = cls()
    # if a real provider is selected but not configured, degrade to mock
    if not getattr(inst, "available", False):
        return MockLLM()
    return inst
