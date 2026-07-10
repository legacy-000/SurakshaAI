from common.ai.quickml_client import QuickMLClient
from common.ai.rag_retriever import SchemaRAGRetriever
from common.sql.sql_validator import SQLValidator

SYSTEM_PROMPT_PATH = "functions/ai/prompts/nl2sql_system_v1.txt"


class NL2SQLEngine:
    def __init__(self, catalyst_app=None):
        self.quickml = QuickMLClient(catalyst_app)
        self.rag = SchemaRAGRetriever(catalyst_app)
        self.validator = SQLValidator()

    def generate_sql(self, query: str, context: list = None) -> dict:
        system_prompt = self._load_system_prompt()
        schema_context = self.rag.retrieve_schema(top_k=8)
        examples = self.rag.retrieve_examples(query, top_k=3)

        if schema_context.get("error"):
            return {"error": "RAG_FAILED", "message": schema_context["message"]}

        conversation_history = ""
        if context:
            history_msgs = [m for m in context if hasattr(m, "content_text")][-6:]
            for m in history_msgs:
                role = "user" if getattr(m, "message_type", "") == "user" else "assistant"
                conversation_history += f"{role}: {m.content_text}\n"

        user_prompt = self._build_user_prompt(query, schema_context, examples, conversation_history)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        result = self.quickml.chat(messages, temperature=0.1, max_tokens=4096)
        if result.get("error"):
            return result

        sql_text = self._extract_sql(result.get("text", ""))
        if not sql_text.strip():
            return {
                "error": "SQLGEN_EMPTY",
                "message": f"Model returned empty SQL text. Raw response: {result.get('full_response')}",
                "raw_response": result.get("text", "")
            }
        validation = self.validator.validate(sql_text)
        if not validation.get("is_valid", False):
            return {
                "error": "SQLGEN_001",
                "sql_text": sql_text,
                "validation": validation,
                "raw_response": result.get("text", ""),
            }

        return {
            "sql_text": sql_text,
            "validation": validation,
            "model": result.get("model"),
            "raw_response": result.get("text", ""),
        }

    def _load_system_prompt(self) -> str:
        try:
            with open(SYSTEM_PROMPT_PATH, "r") as f:
                return f.read()
        except FileNotFoundError:
            return self._default_system_prompt()

    def _default_system_prompt(self) -> str:
        return "You are a SQL generator for Karnataka State Police FIR database. Only SELECT queries. Never modify data."

    def _build_user_prompt(self, query: str, schema: dict, examples: list[dict], history: str) -> str:
        parts = [f"Question: {query}"]

        tables = schema.get("table_descriptions", [])
        if tables:
            parts.append("\nRelevant tables:")
            for t in tables:
                parts.append(f"  - {t.get('name')}: {t.get('description')}")

        columns = schema.get("column_descriptions", [])
        if columns:
            parts.append("\nKey columns:")
            for c in columns[:10]:
                parts.append(f"  - {c.get('table')}.{c.get('column')} ({c.get('type')})")

        if examples:
            parts.append("\nSimilar examples:")
            for ex in examples[:2]:
                parts.append(f"  Q: {ex.get('natural_language')}")
                parts.append(f"  SQL: {ex.get('sql')}")

        if history:
            parts.append(f"\nConversation history:\n{history}")

        return "\n".join(parts)

    def _extract_sql(self, text: str) -> str:
        cleaned = text.replace("```sql", "").replace("```SQL", "").replace("```", "").strip()
        # Remove trailing/leading semicolons if needed
        return cleaned.strip()
