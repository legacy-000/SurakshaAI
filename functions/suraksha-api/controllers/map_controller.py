from sqlalchemy.orm import Session
from services.map_service import MapService
from schemas.response import APIResponse
from typing import List

class MapController:
    def __init__(self, db: Session):
        self.map_service = MapService(db)

    def get_map_layers(self, coordinates: List[float], radius: float) -> APIResponse:
        data = self.map_service.get_spatial_crime_layers(coordinates, radius)
        return APIResponse(
            status="Project Initialized",
            message="Map layers compiled successfully",
            data=data
        )
