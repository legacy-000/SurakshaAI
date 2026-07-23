"""Sociological / socio-demographic crime insights."""
from fastapi import APIRouter, Depends
from sqlalchemy import func, case
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models as m

router = APIRouter(prefix="/api/socio", tags=["socio"])


@router.get("/gender")
def gender(db: Session = Depends(get_db)):
    rows = (db.query(m.Accused.gender, func.count(m.Accused.id))
            .group_by(m.Accused.gender).all())
    return [{"label": r[0] or "Unknown", "value": r[1]} for r in rows]


@router.get("/age-bands")
def age_bands(db: Session = Depends(get_db)):
    band = case(
        (m.Accused.age < 18, "<18"),
        (m.Accused.age < 25, "18-24"),
        (m.Accused.age < 35, "25-34"),
        (m.Accused.age < 45, "35-44"),
        (m.Accused.age < 60, "45-59"),
        else_="60+",
    )
    rows = db.query(band, func.count(m.Accused.id)).group_by(band).all()
    order = ["<18", "18-24", "25-34", "35-44", "45-59", "60+"]
    d = {r[0]: r[1] for r in rows}
    return [{"label": b, "value": d.get(b, 0)} for b in order]


@router.get("/socio-economic")
def socio_economic(db: Session = Depends(get_db)):
    rows = (db.query(m.Accused.socio_economic, func.count(m.Accused.id))
            .group_by(m.Accused.socio_economic).all())
    order = {"Low": 0, "Lower-Mid": 1, "Middle": 2, "Upper-Mid": 3, "High": 4}
    return sorted([{"label": r[0], "value": r[1]} for r in rows],
                  key=lambda x: order.get(x["label"], 9))


@router.get("/education")
def education(db: Session = Depends(get_db)):
    rows = (db.query(m.Accused.education, func.count(m.Accused.id))
            .group_by(m.Accused.education).all())
    order = {"Illiterate": 0, "Primary": 1, "Secondary": 2, "PUC": 3, "Graduate": 4, "Post-Graduate": 5}
    return sorted([{"label": r[0], "value": r[1]} for r in rows],
                  key=lambda x: order.get(x["label"], 9))


@router.get("/urban-rural")
def urban_rural(db: Session = Depends(get_db)):
    rows = (db.query(m.Accused.urban_rural, func.count(m.Accused.id))
            .group_by(m.Accused.urban_rural).all())
    return [{"label": r[0], "value": r[1]} for r in rows]


@router.get("/risk-factors")
def risk_factors(db: Session = Depends(get_db)):
    """Correlate social indicators with average offender risk (illustrative)."""
    total = db.query(func.count(m.Accused.id)).scalar() or 1
    migrant = db.query(func.count(m.Accused.id)).filter(m.Accused.migrant.is_(True)).scalar() or 0
    unemployed = db.query(func.count(m.Accused.id)).filter(m.Accused.occupation == "Unemployed").scalar() or 0
    low_edu = db.query(func.count(m.Accused.id)).filter(
        m.Accused.education.in_(["Illiterate", "Primary"])).scalar() or 0
    low_ses = db.query(func.count(m.Accused.id)).filter(
        m.Accused.socio_economic.in_(["Low", "Lower-Mid"])).scalar() or 0

    def avg_risk(filt):
        v = (db.query(func.avg(m.BehaviorProfile.risk_score))
             .join(m.Accused, m.Accused.id == m.BehaviorProfile.accused_id)
             .filter(filt).scalar())
        return round(v or 0, 1)

    return {
        "factors": [
            {"factor": "Migrant background", "share": round(migrant / total * 100, 1),
             "avg_risk": avg_risk(m.Accused.migrant.is_(True))},
            {"factor": "Unemployment", "share": round(unemployed / total * 100, 1),
             "avg_risk": avg_risk(m.Accused.occupation == "Unemployed")},
            {"factor": "Low education", "share": round(low_edu / total * 100, 1),
             "avg_risk": avg_risk(m.Accused.education.in_(["Illiterate", "Primary"]))},
            {"factor": "Low socio-economic", "share": round(low_ses / total * 100, 1),
             "avg_risk": avg_risk(m.Accused.socio_economic.in_(["Low", "Lower-Mid"]))},
        ],
        "baseline_avg_risk": avg_risk(m.Accused.id.isnot(None)),
    }


@router.get("/crime-by-demographic")
def crime_by_demographic(db: Session = Depends(get_db)):
    """Top crime type per socio-economic band (via case<->accused links)."""
    rows = (db.query(m.Accused.socio_economic, m.Case.crime_type, func.count(m.Case.id))
            .join(m.CaseAccused, m.CaseAccused.accused_id == m.Accused.id)
            .join(m.Case, m.Case.id == m.CaseAccused.case_id)
            .group_by(m.Accused.socio_economic, m.Case.crime_type).all())
    agg: dict[str, dict[str, int]] = {}
    for ses, ct, n in rows:
        agg.setdefault(ses, {})[ct] = n
    out = []
    for ses, cts in agg.items():
        top = sorted(cts.items(), key=lambda x: -x[1])[:3]
        out.append({"socio_economic": ses, "top_crimes": [{"crime": c, "count": n} for c, n in top]})
    return out
