from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from configuration.database import get_db
from controllers.network_controller import NetworkController
from schemas.response import APIResponse

router = APIRouter(prefix="/network", tags=["Network Analysis"])

@router.get("/case/{case_id}", response_model=APIResponse)
def get_network(case_id: int, db: Session = Depends(get_db)) -> APIResponse:
    # Controller Layer is invoked
    controller = NetworkController(db)
    return controller.get_network(case_id)
