from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from configuration.database import get_db
from controllers.report_controller import ReportController
from schemas.response import APIResponse
from typing import Dict, Any

router = APIRouter(prefix="/report", tags=["Precinct Reports"])

@router.post("/generate", response_model=APIResponse)
def generate_report(config: Dict[str, Any], db: Session = Depends(get_db)) -> APIResponse:
    # Controller Layer is invoked
    controller = ReportController(db)
    return controller.generate_report(config)
