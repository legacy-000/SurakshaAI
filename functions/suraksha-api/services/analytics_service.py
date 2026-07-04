from sqlalchemy.orm import Session
from ai_engine.forecasting.predictor import CrimePredictor
from models.datastore_models import CaseMaster, Prediction
from typing import Dict, Any

class AnalyticsService:
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.predictor = CrimePredictor()
        self._case_model = CaseMaster()

    def get_forecasts(self, beat_name: str) -> Dict[str, Any]:
        cases = self._case_model.get_all()
        prediction = self.predictor.predict_hotspots(historical_data=cases or [])
        return {"area": beat_name, "predictions": prediction}
