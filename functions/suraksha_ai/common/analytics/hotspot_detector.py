import random
import math
from common.models.dto import HotspotRequestDTO, HotspotResultDTO, HotspotClusterDTO, EvidenceReferenceDTO


class HotspotDetector:
    def detect(self, req: HotspotRequestDTO) -> HotspotResultDTO:
        karnataka_centroids = {
            1: (12.9716, 77.5946), 18: (12.2958, 76.6394),
            3: (15.3647, 75.1240), 4: (12.9141, 74.8560)
        }
        center = karnataka_centroids.get(req.district_id, (12.9716, 77.5946))

        clusters = []
        for i in range(random.randint(1, 4)):
            offset_lat = random.uniform(-0.05, 0.05)
            offset_lng = random.uniform(-0.05, 0.05)
            clusters.append(HotspotClusterDTO(
                cluster_id=i + 1,
                centroid_lat=round(center[0] + offset_lat, 4),
                centroid_lng=round(center[1] + offset_lng, 4),
                case_count=random.randint(5, 20),
                radius_km=round(random.uniform(0.3, 1.5), 2),
                crime_type=["Theft", "Assault", "Robbery", "Burglary"][i % 4],
                case_ids=[random.randint(1, 500) for _ in range(5)]
            ))

        return HotspotResultDTO(
            query_id="hotspot_mock_id",
            clusters=clusters,
            cases_without_gps=random.randint(5, 30),
            total_cases_analyzed=random.randint(100, 500),
            algorithm="DBSCAN",
            algorithm_params={"eps": req.eps_km, "min_samples": req.min_cases, "metric": "haversine"}
        )
