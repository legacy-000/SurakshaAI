import time
import threading
import logging

logger = logging.getLogger(__name__)

GLM_MODEL_ID = "crm-di-glm47b_30b_it"
GLM_URL = "https://api.catalyst.zoho.in/quickml/v1/project/55029000000013055/glm/chat"
RAG_URL = "https://api.catalyst.zoho.in/quickml/v1/project/55029000000013055/rag/answer"
CATALYST_ORG = "60076341598"


class QuickMLClient:
    def __init__(self, catalyst_app=None):
        self._catalyst_app = catalyst_app
        self.model_id = GLM_MODEL_ID
        self._cached_token = None
        self._token_expiry = 0.0
        self._token_lock = threading.Lock()
        self._refresh_thread_started = False

        if self._catalyst_app:
            self._start_refresh_thread()

    @property
    def is_available(self):
        return self._catalyst_app is not None

    def _start_refresh_thread(self):
        with self._token_lock:
            if self._refresh_thread_started:
                return
            self._refresh_thread_started = True
            t = threading.Thread(target=self._auto_refresh_loop, daemon=True, name="quickml_token_refresh")
            t.start()

    def _auto_refresh_loop(self):
        while True:
            try:
                # Standard Zoho OAuth token is valid for 1 hour. Refresh 5 minutes before (55 mins = 3300s).
                time.sleep(3300)
                logger.info("Initiating background refresh of Zoho OAuth token...")
                self._get_access_token(force_refresh=True)
            except Exception as e:
                logger.warning("Background token auto-refresh encountered error: %s", e)
                time.sleep(60)

    def _get_access_token(self, force_refresh: bool = False) -> str:
        if not self._catalyst_app:
            return ""

        with self._token_lock:
            now = time.time()
            if self._cached_token and now < self._token_expiry and not force_refresh:
                return self._cached_token

            try:
                cred = self._catalyst_app.credential
                if not cred:
                    return ""
                token_res = cred.token()
                token_str = ""
                if isinstance(token_res, tuple):
                    if len(token_res) > 1:
                        token_str = token_res[1]
                    else:
                        token_str = token_res[0]
                else:
                    token_str = str(token_res)

                if token_str:
                    self._cached_token = token_str
                    self._token_expiry = now + 3600  # Token typically valid for 1 hour
                    return token_str
            except Exception as e:
                logger.error("Failed to get Catalyst access token: %s", e)
                if self._cached_token:
                    logger.warning("Graceful degradation: using expired cached token")
                    return self._cached_token
            return ""

    def chat(self, messages: list[dict], temperature: float = 0.1,
             max_tokens: int = 4096, tools: list[dict] = None,
             tool_choice: str = "auto") -> dict:
        if not self.is_available:
            return {"error": "QUICKML_NOT_AVAILABLE",
                    "message": "Catalyst app context not initialized. Inference is unavailable."}

        try:
            import requests

            token = self._get_access_token()
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Zoho-oauthtoken {token}",
                "CATALYST-ORG": CATALYST_ORG,
            }

            data = {
                "model": self.model_id,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": False,
                "chat_template_kwargs": {"enable_thinking": False},
            }
            if tools:
                data["tools"] = tools
                data["tool_choice"] = tool_choice

            logger.info("GLM chat: %d messages, tools=%s", len(messages), "yes" if tools else "no")
            response = requests.post(GLM_URL, json=data, headers=headers, timeout=10)

            if response.status_code != 200:
                logger.error("GLM API returned status %d: %s",
                             response.status_code, response.text[:500])
                return {"error": "GLM_INFERENCE_FAILED",
                        "message": f"API returned status {response.status_code}"}

            res_json = response.json()

            # Extract tool_calls if present
            tool_calls = None
            content = ""
            if isinstance(res_json, dict):
                content = res_json.get("response", "")
                choices = res_json.get("choices", [])
                if choices:
                    msg = choices[0].get("message", {})
                    content = msg.get("content", content)
                    tool_calls = msg.get("tool_calls")

            result = {
                "text": content or "",
                "model": self.model_id,
                "full_response": res_json,
            }
            if tool_calls:
                result["tool_calls"] = tool_calls
                result["has_tool_call"] = True

            return result

        except Exception as e:
            logger.error("GLM inference failed: %s", e)
            return {"error": "QUICKML_INFERENCE_FAILED", "message": str(e)}

    def get_embeddings(self, text: str) -> list[float]:
        if not self.is_available:
            raise RuntimeError("Catalyst app context not initialized. Embedding is unavailable.")
        try:
            model = self._catalyst_app.quick_ml().model(self.model_id)
            response = model.predict({"task": "embedding", "text": text})
            if isinstance(response, dict):
                return response.get("data", [0.0] * 384)
            return [0.0] * 384
        except Exception as e:
            logger.error("Embedding failed: %s", e)
            return [0.0] * 384
