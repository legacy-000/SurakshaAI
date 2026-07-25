"""Crime forecasting & early-warning."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from .. import models as m

router = APIRouter(prefix="/api/forecasting", tags=["forecasting"])


@router.get("/predictions")
def predictions(db: Session = Depends(get_db), risk_level: str | None = None,
                crime_type: str | None = None, district: str | None = None):
    if settings.quickml_endpoint_key:
        from ..services.forecast import get_forecast
        forecast = get_forecast(crime_type=crime_type, district=district)
        if forecast:
            results = []
            for f in forecast:
                level = "High" if f["predicted_count"] > 5 else "Medium" if f["predicted_count"] > 2 else "Low"
                if risk_level and level != risk_level:
                    continue
                results.append({
                    "id": None,
                    "target_area": district or "All Districts",
                    "crime_type": crime_type or "All Types",
                    "probability": min(f["predicted_count"] / 10, 1.0),
                    "risk_level": level,
                    "window_start": f["date"],
                    "window_end": None,
                    "contributing_factors": None,
                    "predicted_count": f["predicted_count"],
                    "lower_bound": f["lower_bound"],
                    "upper_bound": f["upper_bound"],
                    "source": "quickml_prophet",
                })
            if results:
                return results

    if settings.use_catalyst:
        from ..catalyst_store import get_store
        store = get_store()
        # risk_level is user input going into ZCQL — whitelist rather than
        # interpolate, the value set is fixed and small.
        where = ""
        if risk_level in ("High", "Medium", "Low", "Critical"):
            where = f"WHERE risk_level = '{risk_level}'"
        elif risk_level:
            return []
        rows = store.query(f"SELECT * FROM predictions {where}")
        rows.sort(key=lambda p: p.get("probability") or 0, reverse=True)
        return [{"id": p.get("ROWID"), "target_area": p.get("target_area"),
                 "crime_type": p.get("crime_type"), "probability": p.get("probability"),
                 "risk_level": p.get("risk_level"),
                 "window_start": p.get("forecast_window_start"),
                 "window_end": p.get("forecast_window_end"),
                 "contributing_factors": p.get("contributing_factors"),
                 "source": "datastore"} for p in rows]

    q = db.query(m.Prediction)
    if risk_level:
        q = q.filter(m.Prediction.risk_level == risk_level)
    rows = q.order_by(m.Prediction.probability.desc()).all()
    return [{"id": p.id, "target_area": p.target_area, "crime_type": p.crime_type,
             "probability": p.probability, "risk_level": p.risk_level,
             "window_start": p.forecast_window_start.isoformat() if p.forecast_window_start else None,
             "window_end": p.forecast_window_end.isoformat() if p.forecast_window_end else None,
             "contributing_factors": p.contributing_factors,
             "source": "datastore"} for p in rows]
