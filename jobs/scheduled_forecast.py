from functions.forecast.forecaster import Forecaster
from functions.forecast.alert_engine import AlertEngine
from models.dto import ForecastRequestDTO


class ScheduledForecastJob:
    def __init__(self):
        self.forecaster = Forecaster()

    def run(self, district_ids: list[int] = None):
        districts = district_ids or [1, 18, 3, 4]
        for d_id in districts:
            req = ForecastRequestDTO(
                district_id=d_id, crime_sub_head_id=10,
                training_window_days=365, forecast_horizon_days=30
            )
            result = self.forecaster.forecast(req)
            print(f"[ScheduledForecast] District {d_id}: run_id={result.run_id}")
