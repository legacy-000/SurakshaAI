import uuid
from datetime import datetime
from models.dto import InvestigationDTO, SavedGraphDTO


class InvestigationManager:
    def __init__(self):
        self._investigations = {}

    def create(self, title: str, description: str = "", user_id: str = "") -> InvestigationDTO:
        inv = InvestigationDTO(
            investigation_id=str(uuid.uuid4()),
            title=title, description=description,
            status="open", created_at=datetime.now().isoformat(),
            case_count=0, query_count=0,
        )
        self._investigations[inv.investigation_id] = {
            "dto": inv, "cases": [], "queries": [], "graphs": []
        }
        return inv

    def get(self, investigation_id: str) -> dict:
        record = self._investigations.get(investigation_id)
        if not record:
            return None
        dto = record["dto"]
        return {"investigation_id": dto.investigation_id, "title": dto.title,
                "description": dto.description, "status": dto.status,
                "created_at": dto.created_at, "cases": record["cases"],
                "queries": record["queries"],
                "graphs": [g.model_dump() for g in record["graphs"]]}

    def list_all(self) -> list:
        return [self.get(i) for i in self._investigations]

    def add_case(self, investigation_id: str, case_master_id: int, notes: str = "") -> bool:
        record = self._investigations.get(investigation_id)
        if not record:
            return False
        record["cases"].append({"case_master_id": case_master_id, "notes": notes})
        dto = record["dto"]
        dto.case_count = len(record["cases"])
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
