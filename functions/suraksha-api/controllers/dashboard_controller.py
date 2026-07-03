from sqlalchemy.orm import Session
from services.dashboard_service import DashboardService
from schemas.response import APIResponse

class DashboardController:
    def __init__(self, db: Session):
        self.dashboard_service = DashboardService(db)

    def get_dashboard_summary(self) -> APIResponse:
        data = self.dashboard_service.get_summary_metrics()
        return APIResponse(
            status="Project Initialized",
            message="Dashboard KPI summary compiled successfully",
            data=data
        )
