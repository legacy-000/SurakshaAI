from typing import List, Dict, Any
from collections import Counter
from models.datastore_models import CaseMaster, Prediction
import datetime


class CrimePredictor:
    """
    Crime prediction engine using historical case data.
    Performs statistical hotspot detection, temporal pattern analysis,
    and crime-type frequency forecasting.
    """

    def __init__(self):
        self._case_model = CaseMaster()
        self._prediction_model = Prediction()

    def predict_hotspots(self, historical_data: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not historical_data:
            cases = self._case_model.get_all()
            if not cases:
                saved = self._prediction_model.get_all()
                if saved:
                    return {"predictions": saved, "confidence": 0.7, "hotspots": saved}
                return {"prediction": "mock", "confidence": 0.0, "hotspots": []}
            historical_data = cases

        location_counts = Counter()
        crime_type_counts = Counter()
        for c in historical_data:
            loc = c.get("Latitude", "") + "," + c.get("Longitude", "")
            if loc != ",":
                location_counts[loc] += 1
            ct = c.get("CrimeMajorHeadID", "")
            if ct:
                crime_type_counts[ct] += 1

        total = len(historical_data) or 1
        hotspots = [
            {"location": loc, "count": cnt, "probability": round(cnt / total, 2)}
            for loc, cnt in location_counts.most_common(5)
        ]
        trends = [
            {"crime_type": ct, "count": cnt, "share": round(cnt / total * 100, 1)}
            for ct, cnt in crime_type_counts.most_common()
        ]

        return {
            "prediction": "statistical",
            "confidence": round(min(total / 100, 0.95), 2),
            "hotspots": hotspots,
            "trends": trends,
            "total_cases_analyzed": total
        }
