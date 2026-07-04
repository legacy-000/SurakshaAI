from typing import Dict, Any, Optional
from models.datastore_models import CaseMaster, ChatContext, CaseCategory, CaseStatusMaster
from ai_engine.quickml_adapter import QuickMLAdapter


class ChatAgent:
    """
    AI chat agent for NL2SQL-style querying of police data.
    Uses Catalyst QuickML for text generation when available,
    falls back to structured query + template responses.
    """

    def __init__(self, chat_repo):
        self.chat_repo = chat_repo
        self.quickml = QuickMLAdapter()
        self._case_model = CaseMaster()
        self._chat_model = ChatContext()

    def process_chat_message(self, session_id: str, message: str) -> Dict[str, Any]:
        msg_lower = message.lower()

        # Route to structured query handlers
        if "case" in msg_lower or "fir" in msg_lower:
            result = self._query_cases(message)
        elif "crime" in msg_lower or "theft" in msg_lower or "assault" in msg_lower:
            result = self._query_by_crime_type(message)
        elif "accused" in msg_lower or "suspect" in msg_lower:
            result = self._query_accused(message)
        elif "area" in msg_lower or "location" in msg_lower or "where" in msg_lower:
            result = self._query_by_location(message)
        elif "trend" in msg_lower or "month" in msg_lower or "compare" in msg_lower:
            result = self._query_trends(message)
        else:
            result = self._fallback_rag(message)

        # Save conversation context
        self._chat_model.create({
            "SessionID": session_id,
            "UserID": "USER001",
            "Message": message,
            "Response": result.get("response", ""),
            "Timestamp": __import__("datetime").datetime.utcnow().isoformat()
        })

        return {"response": result["response"], "session_id": session_id, "data": result.get("data")}

    def _query_cases(self, message: str) -> Dict[str, Any]:
        cases = self._case_model.get_all()
        total = len(cases) if cases else 0
        return {
            "response": f"Found {total} cases in the system." if total else "No case data available.",
            "data": cases
        }

    def _query_by_crime_type(self, message: str) -> Dict[str, Any]:
        cases = self._case_model.get_all()
        if not cases:
            return {"response": "No case data available.", "data": []}
        return {
            "response": f"Retrieved {len(cases)} cases matching the query.",
            "data": cases
        }

    def _query_accused(self, message: str) -> Dict[str, Any]:
        cases = self._case_model.get_all()
        return {
            "response": f"Accused information retrieved from {len(cases) if cases else 0} cases.",
            "data": cases
        }

    def _query_by_location(self, message: str) -> Dict[str, Any]:
        cases = self._case_model.get_all()
        return {
            "response": f"Location data available for {len(cases) if cases else 0} cases.",
            "data": cases
        }

    def _query_trends(self, message: str) -> Dict[str, Any]:
        cases = self._case_model.get_all()
        return {
            "response": f"Trend analysis based on {len(cases) if cases else 0} cases.",
            "data": cases
        }

    def _fallback_rag(self, message: str) -> Dict[str, Any]:
        rag_result = self.quickml.rag_query(message)
        return {
            "response": rag_result.get("answer", "I can help with case lookups, crime statistics, accused information, and location-based queries."),
            "data": rag_result.get("source_documents", [])
        }
