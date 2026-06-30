from sqlalchemy.orm import Session
from backend.services.report_service import ReportService
from backend.schemas.response import APIResponse
from typing import Dict, Any

class ReportController:
    def __init__(self, db: Session):
        self.report_service = ReportService(db)

    def generate_report(self, report_config: Dict[str, Any]) -> APIResponse:
        data = self.report_service.compile_crime_report(report_config)
        return APIResponse(
            status="Project Initialized",
            message="Precinct crime report generated successfully",
            data=data
        )
