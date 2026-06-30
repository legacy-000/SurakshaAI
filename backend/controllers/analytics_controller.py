from sqlalchemy.orm import Session
from backend.services.analytics_service import AnalyticsService
from backend.schemas.response import APIResponse

class AnalyticsController:
    def __init__(self, db: Session):
        self.analytics_service = AnalyticsService(db)

    def get_predictions(self, beat_name: str) -> APIResponse:
        data = self.analytics_service.get_forecasts(beat_name)
        return APIResponse(
            status="Project Initialized",
            message="Forecasting analytics retrieved successfully",
            data=data
        )
