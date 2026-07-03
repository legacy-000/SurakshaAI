from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from configuration.database import get_db
from controllers.map_controller import MapController
from schemas.response import APIResponse
from typing import List

router = APIRouter(prefix="/map", tags=["Geospatial Maps"])

@router.get("/layers", response_model=APIResponse)
def get_map_layers(lat: float, lng: float, radius: float, db: Session = Depends(get_db)) -> APIResponse:
    # Controller Layer is invoked
    controller = MapController(db)
    return controller.get_map_layers([lat, lng], radius)
