from functions.forecast.forecaster import Forecaster
from functions.forecast.alert_engine import AlertEngine
from models.dto import ForecastRequestDTO

def test_forecast_generation():
    forecaster = Forecaster()
    req = ForecastRequestDTO(district_id=18, crime_sub_head_id=10)
    result = forecaster.forecast(req)
    assert result.run_id is not None
    assert len(result.forecast) == 30
    assert result.metrics["mae"] > 0

def test_alert_evaluation():
    engine = AlertEngine()
    alerts = engine.evaluate(district_id=18)
    if alerts:
        assert alerts[0].alert_id is not None
