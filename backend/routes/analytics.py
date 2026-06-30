from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.configuration.database import get_db
from backend.controllers.analytics_controller import AnalyticsController
from backend.schemas.response import APIResponse

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/predictions", response_model=APIResponse)
def get_predictions(beat_name: str, db: Session = Depends(get_db)) -> APIResponse:
    # Controller Layer is invoked
    controller = AnalyticsController(db)
    return controller.get_predictions(beat_name)
