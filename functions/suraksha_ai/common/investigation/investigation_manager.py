import uuid
from datetime import datetime
from common.models.dto import InvestigationDTO, SavedGraphDTO


class InvestigationManager:
    def __init__(self):
        self._investigations = {}

    def create(self, title: str, description: str = "", user_id: str = "") -> InvestigationDTO:
        inv = InvestigationDTO(
            investigation_id=str(uuid.uuid4()),
            title=title, description=description,
            created_at=datetime.now().isoformat()
        )
        self._investigations[inv.investigation_id] = {
            "dto": inv, "cases": [], "queries": [], "graphs": []
        }
        return inv

    def get(self, investigation_id: str) -> InvestigationDTO:
        record = self._investigations.get(investigation_id)
        return record["dto"] if record else None

    def list_all(self) -> list[InvestigationDTO]:
        return [r["dto"] for r in self._investigations.values()]

    def add_case(self, investigation_id: str, case_master_id: int, notes: str = "") -> bool:
        record = self._investigations.get(investigation_id)
        if not record:
            return False
        record["cases"].append({"case_master_id": case_master_id, "notes": notes})
        return True

    def add_query(self, investigation_id: str, query_id: str) -> bool:
        record = self._investigations.get(investigation_id)
        if not record:
            return False
        record["queries"].append({"query_id": query_id})
        return True

    def add_graph(self, investigation_id: str, graph_data: dict, label: str) -> SavedGraphDTO:
        record = self._investigations.get(investigation_id)
        if not record:
            return None
        saved = SavedGraphDTO(
            saved_graph_id=str(uuid.uuid4()),
            label=label,
            node_count=len(graph_data.get("nodes", [])),
            edge_count=len(graph_data.get("edges", [])),
            created_at=datetime.now().isoformat()
        )
        record["graphs"].append(saved)
        return saved
