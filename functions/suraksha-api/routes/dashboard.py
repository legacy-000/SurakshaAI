from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from configuration.database import get_db
from controllers.dashboard_controller import DashboardController
from schemas.response import APIResponse

router = APIRouter(prefix="/dashboard", tags=["Dashboard Info"])

@router.get("/summary", response_model=APIResponse)
def get_dashboard_summary(db: Session = Depends(get_db)) -> APIResponse:
    # Controller Layer is invoked
    controller = DashboardController(db)
    return controller.get_dashboard_summary()
