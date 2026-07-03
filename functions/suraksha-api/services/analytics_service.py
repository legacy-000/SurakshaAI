from sqlalchemy.orm import Session
from ai_engine.forecasting.predictor import CrimePredictor
from typing import Dict, Any

class AnalyticsService:
    """
    Coordinates crime analytics, predictions, and hotspot detection.
    """
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.predictor = CrimePredictor()

    def get_forecasts(self, beat_name: str) -> Dict[str, Any]:
        # Service Layer coordinates calls to CrimePredictor (AI Layer)
        prediction = self.predictor.predict_hotspots(historical_data=[])
        return {
            "area": beat_name,
            "predictions": prediction
        }
