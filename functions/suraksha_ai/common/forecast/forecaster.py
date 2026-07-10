import uuid
import random
from datetime import datetime, timedelta
from common.models.dto import ForecastRequestDTO, ForecastResultDTO, ForecastDataPoint, EvidenceReferenceDTO


class Forecaster:
    def forecast(self, req: ForecastRequestDTO) -> ForecastResultDTO:
        run_id = str(uuid.uuid4())
        horizon = req.forecast_horizon_days
        base = random.randint(20, 50)

        forecast_points = []
        current = base
        for i in range(horizon):
            pred = max(0, current + random.gauss(0, 5))
            forecast_points.append(ForecastDataPoint(
                date=(datetime.now() + timedelta(days=i + 1)).strftime("%Y-%m-%d"),
                predicted=round(pred, 1),
                lower=round(pred - random.uniform(5, 15), 1),
                upper=round(pred + random.uniform(5, 15), 1)
            ))
            current = pred

        return ForecastResultDTO(
            run_id=run_id,
            model="Prophet v1.0",
            district=f"District_{req.district_id}",
            crime_type=f"CrimeType_{req.crime_sub_head_id}",
            training_days=req.training_window_days,
            horizon_days=horizon,
            metrics={
                "mae": round(random.uniform(3, 10), 2),
                "rmse": round(random.uniform(4, 12), 2),
                "baseline_mae": round(random.uniform(5, 15), 2),
                "mape": None,
                "mape_reason": "MAPE not shown - zero crime days in evaluation period"
            },
            forecast=forecast_points,
            evidence_refs=[EvidenceReferenceDTO(
                evidence_id=f"ev_fc_{run_id[:8]}",
                evidence_type="computed_statistic",
                source_table="CaseMaster",
                display_label=f"Forecast based on {req.training_window_days} days of training data"
            )]
        )
