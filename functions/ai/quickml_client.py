import logging

logger = logging.getLogger(__name__)

GLM_MODEL_ID = "crm-di-glm47b_30b_it"


class QuickMLClient:
    def __init__(self, catalyst_app=None):
        self._catalyst_app = catalyst_app
        self.model_id = GLM_MODEL_ID

    @property
    def is_available(self):
        return self._catalyst_app is not None

    def _get_access_token(self) -> str:
        if not self._catalyst_app:
            return ""
        try:
            cred = self._catalyst_app.credential
            if not cred:
                return ""
            token_res = cred.token()
            if isinstance(token_res, tuple):
                if len(token_res) > 1:
                    # CatalystCredential returns (class_name, token_value)
                    # CookieCredential returns (cookie, csrf_header)
                    return token_res[1]
                return token_res[0]
            return str(token_res)
        except Exception as e:
            logger.error("Failed to get Catalyst access token: %s", e)
            return ""

    def chat(self, messages: list[dict], temperature: float = 0.1, max_tokens: int = 4096) -> dict:
        if not self.is_available:
            # Local mock mode fallback for testing and offline development
            return {
                "text": "SELECT COUNT(*) FROM CaseMaster WHERE CrimeRegisteredDate >= '2024-01-01' LIMIT 100;",
                "model": self.model_id,
                "full_response": {}
            }

        try:
            import requests

            project_id = "55029000000013055"
            org_id = "60076341598"

            if self._catalyst_app and hasattr(self._catalyst_app, "config"):
                project_id = self._catalyst_app.config.get("project_id", project_id)

            url = f"https://api.catalyst.zoho.in/quickml/v1/project/{project_id}/glm/chat"
            token = self._get_access_token()

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
                "CATALYST-ORG": org_id
            }

            data = {
                "model": self.model_id,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": False,
                "chat_template_kwargs": {
                    "enable_thinking": False
                }
            }

            logger.info("Sending chat request to GLM API at %s", url)
            response = requests.post(url, json=data, headers=headers, timeout=60)
            
            if response.status_code != 200:
                logger.error("GLM API request failed with status %d: %s", response.status_code, response.text)
                return {"error": "GLM_INFERENCE_FAILED", "message": f"API returned status {response.status_code}: {response.text}"}

            res_json = response.json()
            content = ""
            if isinstance(res_json, dict):
                content = res_json.get("response", "")
                if not content:
                    choices = res_json.get("choices", [])
                    if choices:
                        content = choices[0].get("message", {}).get("content", "")

            return {"text": content, "model": self.model_id, "full_response": res_json}

        except Exception as e:
            logger.error("QuickML GLM chat inference failed: %s", e)
            return {"error": "QUICKML_INFERENCE_FAILED", "message": str(e)}

    def get_embeddings(self, text: str) -> list[float]:
        if not self.is_available:
            return [0.1] * 384

        try:
            model = self._catalyst_app.quick_ml().model(self.model_id)
            response = model.predict({"task": "embedding", "text": text})
            if isinstance(response, dict):
                return response.get("data", [0.0] * 384)
            return [0.0] * 384
        except Exception as e:
            logger.error("Embedding failed: %s", e)
            return [0.0] * 384
