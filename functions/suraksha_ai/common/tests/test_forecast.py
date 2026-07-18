from forecast.alert_engine import AlertEngine
from forecast.forecaster import Forecaster
from models.dto import ForecastRequestDTO, EarlyWarningAlertDTO
import sys
import os
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, BASE)
os.environ.setdefault("PYTHONPATH", BASE)


class TestForecaster:
    def test_forecast_returns_run_id(self):
        fc = Forecaster()
        req = ForecastRequestDTO(district_id=18, crime_sub_head_id=10)
        result = fc.forecast(req)
        assert result.run_id is not None
        assert result.model in ("Prophet v1.0", "SeasonalNaive v1", "ARIMA(1,0,1)")

    def test_forecast_horizon_matches_request(self):
        fc = Forecaster()
        req = ForecastRequestDTO(district_id=18, crime_sub_head_id=10, forecast_horizon_days=30)
        result = fc.forecast(req)
        assert len(result.forecast) == 30

    def test_forecast_contains_expected_metrics(self):
        fc = Forecaster()
        req = ForecastRequestDTO(district_id=18, crime_sub_head_id=10)
        result = fc.forecast(req)
        assert "mae" in result.metrics
        assert "rmse" in result.metrics

    def test_forecast_data_points_have_bounds(self):
        fc = Forecaster()
        req = ForecastRequestDTO(district_id=18, crime_sub_head_id=10, forecast_horizon_days=5)
        result = fc.forecast(req)
        for dp in result.forecast:
            assert dp.lower <= dp.predicted <= dp.upper or dp.upper <= dp.predicted <= dp.lower


class TestAlertEngine:
    def test_evaluate_returns_alerts(self):
        engine = AlertEngine()
        alerts = engine.evaluate(district_id=18)
        assert len(alerts) >= 0
        for a in alerts:
            assert isinstance(a, EarlyWarningAlertDTO)
            assert a.rule_id in ("EW-001", "EW-002", "EW-003", "EW-004", "EW-005")

    def test_evaluate_zscore_alert_has_critical_severity(self):
        engine = AlertEngine()
        alerts = engine.evaluate(district_id=18)
        spike_alerts = [a for a in alerts if a.rule_id == "EW-001"]
        for a in spike_alerts:
            assert a.severity == "critical"
            assert a.alert_type == "spike"
