"""Crime forecasting & early-warning."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models as m

router = APIRouter(prefix="/api/forecasting", tags=["forecasting"])


@router.get("/predictions")
def predictions(db: Session = Depends(get_db), risk_level: str | None = None):
    q = db.query(m.Prediction)
    if risk_level:
        q = q.filter(m.Prediction.risk_level == risk_level)
    rows = q.order_by(m.Prediction.probability.desc()).all()
    return [{"id": p.id, "target_area": p.target_area, "crime_type": p.crime_type,
             "probability": p.probability, "risk_level": p.risk_level,
             "window_start": p.forecast_window_start.isoformat() if p.forecast_window_start else None,
             "window_end": p.forecast_window_end.isoformat() if p.forecast_window_end else None,
             "contributing_factors": p.contributing_factors} for p in rows]
