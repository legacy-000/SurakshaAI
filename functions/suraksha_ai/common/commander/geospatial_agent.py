import logging
from common.models.dto import HotspotRequestDTO

logger = logging.getLogger(__name__)


class GeospatialAgent:
    def __init__(self, hotspot_detector=None):
        self._detector = hotspot_detector

    def run(self, query: str) -> dict:
        if self._detector:
            req = HotspotRequestDTO(district_id=18, crime_sub_head_id=None, eps_km=1.0, min_cases=5)
            result = self._detector.detect(req)
            clusters = [{"cluster_id": c.cluster_id, "centroid_lat": c.centroid_lat,
                         "centroid_lng": c.centroid_lng, "case_count": c.case_count,
                         "radius_km": c.radius_km, "crime_type": c.crime_type}
                        for c in result.clusters]
            return {"data": {"clusters": clusters, "total": result.total_cases_analyzed}, "evidence": []}
        return {"data": {"clusters": [], "note": f"Geospatial analysis mock: {query}"}, "evidence": []}
