import uuid
from datetime import datetime


class ProvenanceTracker:
    def __init__(self):
        self._provenance = {}

    def track(self, query_id: str, user_id: str, sql_text: str, source_tables: list[str]):
        record = {
            "provenance_id": str(uuid.uuid4()),
            "query_id": query_id,
            "user_id": user_id,
            "sql_text": sql_text,
            "source_tables": source_tables,
            "timestamp": datetime.now().isoformat()
        }
        self._provenance[query_id] = record
        return record

    def get_provenance(self, query_id: str) -> dict:
        return self._provenance.get(query_id, {})
