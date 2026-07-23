"""Crime pattern & trend analytics + dashboard KPIs."""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_ctx
from .. import models as m

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/overview")
def overview(db: Session = Depends(get_db)):
    total = db.query(func.count(m.Case.id)).scalar() or 0
    open_cases = db.query(func.count(m.Case.id)).filter(
        m.Case.status.in_(["Open", "Under Investigation"])).scalar() or 0
    solved = db.query(func.count(m.Case.id)).filter(
        m.Case.status.in_(["Chargesheeted", "Closed"])).scalar() or 0
    accused = db.query(func.count(m.Accused.id)).scalar() or 0
    high_risk = db.query(func.count(m.BehaviorProfile.id)).filter(
        m.BehaviorProfile.risk_band.in_(["High", "Critical"])).scalar() or 0
    loss = db.query(func.sum(m.Case.loss_amount)).scalar() or 0
    alerts = db.query(func.count(m.Alert.id)).filter(m.Alert.resolved.is_(False)).scalar() or 0
    return {"total_cases": total, "open_cases": open_cases, "solved_cases": solved,
            "clearance_rate": round(solved / total * 100, 1) if total else 0,
            "total_accused": accused, "high_risk_offenders": high_risk,
            "total_loss": loss, "active_alerts": alerts}


@router.get("/by-type")
def by_type(db: Session = Depends(get_db)):
    rows = (db.query(m.Case.crime_type, func.count(m.Case.id))
            .group_by(m.Case.crime_type).order_by(func.count(m.Case.id).desc()).all())
    return [{"label": r[0], "value": r[1]} for r in rows]


@router.get("/by-head")
def by_head(db: Session = Depends(get_db)):
    rows = (db.query(m.Case.crime_head, func.count(m.Case.id))
            .group_by(m.Case.crime_head).order_by(func.count(m.Case.id).desc()).all())
    return [{"label": r[0], "value": r[1]} for r in rows]


@router.get("/trend")
def trend(db: Session = Depends(get_db), crime_type: str | None = None):
    q = db.query(func.strftime("%Y-%m", m.Case.occurrence_date), func.count(m.Case.id))
    if crime_type:
        q = q.filter(m.Case.crime_type == crime_type)
    rows = q.group_by(func.strftime("%Y-%m", m.Case.occurrence_date)) \
            .order_by(func.strftime("%Y-%m", m.Case.occurrence_date)).all()
    return [{"label": r[0], "value": r[1]} for r in rows if r[0]]


@router.get("/hotspots")
def hotspots(db: Session = Depends(get_db), crime_type: str | None = None):
    q = db.query(m.Case.district, func.count(m.Case.id))
    if crime_type:
        q = q.filter(m.Case.crime_type == crime_type)
    rows = q.group_by(m.Case.district).order_by(func.count(m.Case.id).desc()).all()
    return [{"label": r[0], "value": r[1]} for r in rows]


@router.get("/geo")
def geo_points(db: Session = Depends(get_db), crime_type: str | None = None, limit: int = 400):
    q = db.query(m.Case)
    if crime_type:
        q = q.filter(m.Case.crime_type == crime_type)
    rows = q.limit(limit).all()
    return [{"lat": c.latitude, "lon": c.longitude, "crime_type": c.crime_type,
             "district": c.district, "severity": c.severity, "fir": c.fir_number}
            for c in rows if c.latitude and c.longitude]


@router.get("/district-map")
def district_map(request: Request, db: Session = Depends(get_db), crime_type: str | None = None):
    """Per-district centroid + incident density for the Karnataka heat map."""
    ctx = get_ctx(request)
    df = ctx.district_filter()
    q = db.query(
        m.Case.district,
        func.count(m.Case.id),
        func.avg(m.Case.latitude),
        func.avg(m.Case.longitude),
        func.sum(m.Case.loss_amount),
    )
    if crime_type:
        q = q.filter(m.Case.crime_type == crime_type)
    rows = q.group_by(m.Case.district).all()
    out = []
    for dist, count, lat, lon, loss in rows:
        # top crime for the district
        top = (db.query(m.Case.crime_type, func.count(m.Case.id))
               .filter(m.Case.district == dist)
               .group_by(m.Case.crime_type)
               .order_by(func.count(m.Case.id).desc()).first())
        out.append({"district": dist, "count": count, "lat": lat, "lon": lon,
                    "loss": loss or 0, "top_crime": top[0] if top else None,
                    "in_scope": (df is None or dist == df)})
    return {"scope_district": df, "districts": out}
def temporal(db: Session = Depends(get_db)):
    """Seasonal / weekday signature (by month-of-year and day-of-week)."""
    by_month = (db.query(func.strftime("%m", m.Case.occurrence_date), func.count(m.Case.id))
                .group_by(func.strftime("%m", m.Case.occurrence_date)).all())
    by_dow = (db.query(func.strftime("%w", m.Case.occurrence_date), func.count(m.Case.id))
              .group_by(func.strftime("%w", m.Case.occurrence_date)).all())
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    dows = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    return {
        "by_month": [{"label": months[int(r[0]) - 1], "value": r[1]} for r in by_month if r[0]],
        "by_weekday": [{"label": dows[int(r[0])], "value": r[1]} for r in by_dow if r[0] is not None],
    }


@router.get("/patterns")
def patterns(db: Session = Depends(get_db)):
    rows = db.query(m.CrimePattern).order_by(m.CrimePattern.case_count.desc()).all()
    return [{"id": p.id, "name": p.pattern_name, "crime_type": p.crime_type,
             "district": p.district, "temporal": p.temporal_signature,
             "mo_tags": p.modus_operandi_tags, "case_count": p.case_count,
             "description": p.description} for p in rows]
