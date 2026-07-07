class QuickMLClient:
    def __init__(self):
        self.model_id = "quickml-llama-3.1-70b"

    def infer(self, prompt: str, temperature: float = 0.1, max_tokens: int = 4096) -> dict:
        result = self._call_model(prompt, temperature, max_tokens)
        return result

    def _call_model(self, prompt: str, temperature: float, max_tokens: int) -> dict:
        return {
            "text": "SELECT COUNT(*) FROM CaseMaster WHERE CrimeRegisteredDate >= '2024-01-01' LIMIT 100;",
            "model": self.model_id
        }

    def get_embeddings(self, text: str) -> list[float]:
        return [0.1] * 384
