from sqlalchemy.orm import Session
from models.datastore_models import CaseMaster
from typing import Dict, Any, List


class MapService:
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self._case_model = CaseMaster()

    def get_spatial_crime_layers(self, coordinates: List[float], radius_meters: float) -> Dict[str, Any]:
        cases = self._case_model.get_all() or []
        markers = []
        for c in cases:
            lat = c.get("Latitude")
            lng = c.get("Longitude")
            if lat and lng:
                markers.append({
                    "id": c.get("CaseMasterID"),
                    "lat": float(lat),
                    "lng": float(lng),
                    "crime_type": c.get("CrimeMajorHeadID"),
                    "status": c.get("CaseStatusID"),
                    "date": c.get("CrimeRegisteredDate", "")
                })
        return {"center": coordinates, "radius": radius_meters, "crime_markers": markers}
