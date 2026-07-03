from sqlalchemy.orm import Session
from services.network_service import NetworkService
from schemas.response import APIResponse

class NetworkController:
    def __init__(self, db: Session):
        self.network_service = NetworkService(db)

    def get_network(self, case_id: int) -> APIResponse:
        data = self.network_service.get_association_network(case_id)
        return APIResponse(
            status="Project Initialized",
            message="Association network built successfully",
            data=data
        )
