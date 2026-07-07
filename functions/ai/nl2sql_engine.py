from functions.ai.quickml_client import QuickMLClient
from functions.sql.sql_validator import SQLValidator


class NL2SQLEngine:
    def __init__(self):
        self.quickml = QuickMLClient()
        self.validator = SQLValidator()

    def generate_sql(self, query: str, context: list = None) -> dict:
        prompt = self._build_prompt(query, context)
        result = self.quickml.infer(prompt, temperature=0.1)
        sql_text = result.get("text", "")

        sql_text = self._extract_sql(sql_text)
        validation = self.validator.validate(sql_text)
        if not validation.get("is_valid", False):
            return {"error": "SQLGEN_001", "sql_text": sql_text, "validation": validation}

        return {"sql_text": sql_text, "validation": validation, "model": result.get("model")}

    def _build_prompt(self, query: str, context: list) -> str:
        prompt = "Convert to SQL: " + query
        if context:
            prompt += "\nContext: " + str([m.content_text for m in context[-3:]])
        return prompt

    def _extract_sql(self, text: str) -> str:
        if "SELECT" in text.upper() or "select" in text:
            lines = text.split("\n")
            sql_lines = []
            capture = False
            for line in lines:
                if "SELECT" in line.upper() or "select" in line.lower():
                    capture = True
                if capture:
                    sql_lines.append(line)
            return "\n".join(sql_lines)
        return text
