import logging
from common.models.dto import QueryRequestDTO

logger = logging.getLogger(__name__)


class DatabaseAgent:
    def __init__(self, chat_handler=None, db_client=None):
        self._chat = chat_handler
        self._db = db_client

    def run(self, query: str) -> dict:
        if self._chat:
            req = QueryRequestDTO(message=query)
            result = self._chat.handle_query(req)
            evidence = [e.model_dump() for e in result.evidence_refs] if result.evidence_refs else []
            return {"data": result.content_text, "evidence": evidence, "sql": result.sql_text}
        return {"data": f"Database query mock: {query}", "evidence": [], "sql": None}
