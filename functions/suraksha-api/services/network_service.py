from sqlalchemy.orm import Session
from ai_engine.graph.network_analyzer import NetworkAnalyzer
from models.datastore_models import CaseMaster, Accused
from typing import Dict, Any

class NetworkService:
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.analyzer = NetworkAnalyzer()
        self._case_model = CaseMaster()
        self._accused_model = Accused()

    def get_association_network(self, case_id: int) -> Dict[str, Any]:
        cases = self._case_model.get_all()
        accused = self._accused_model.get_all()
        network_data = self.analyzer.build_network_graph(
            nodes=cases or [], edges=accused or []
        )
        return {"case_id": case_id, "network": network_data}
