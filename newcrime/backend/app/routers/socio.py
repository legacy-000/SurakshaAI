"""Sociological / socio-demographic crime insights."""
from collections import Counter

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, case
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from .. import models as m
from ..deps import get_ctx

router = APIRouter(prefix="/api/socio", tags=["socio"])


def _accused_all(ctx):
    """Accused within the caller's territory only."""
    from ..catalyst_store import get_store
    return ctx.scope_rows(get_store().query("SELECT * FROM accused"))


@router.get("/gender")
def gender(request: Request, db: Session = Depends(get_db)):
    if settings.use_catalyst:
        counts = Counter(a.get("gender") or "Unknown" for a in _accused_all(get_ctx(request)))
        return [{"label": k, "value": v} for k, v in counts.items()]

    rows = (db.query(m.Accused.gender, func.count(m.Accused.id))
            .group_by(m.Accused.gender).all())
    return [{"label": r[0] or "Unknown", "value": r[1]} for r in rows]


@router.get("/age-bands")
def age_bands(request: Request, db: Session = Depends(get_db)):
    if settings.use_catalyst:
        order = ["<18", "18-24", "25-34", "35-44", "45-59", "60+"]
        d: dict[str, int] = {b: 0 for b in order}
        for a in _accused_all(get_ctx(request)):
            age = int(a.get("age") or 0)
            if age < 18:
                d["<18"] += 1
            elif age < 25:
                d["18-24"] += 1
            elif age < 35:
                d["25-34"] += 1
            elif age < 45:
                d["35-44"] += 1
            elif age < 60:
                d["45-59"] += 1
            else:
                d["60+"] += 1
        return [{"label": b, "value": d[b]} for b in order]

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
def socio_economic(request: Request, db: Session = Depends(get_db)):
    if settings.use_catalyst:
        counts = Counter(a.get("socio_economic") for a in _accused_all(get_ctx(request)))
        order = {"Low": 0, "Lower-Mid": 1, "Middle": 2, "Upper-Mid": 3, "High": 4}
        return sorted([{"label": k, "value": v} for k, v in counts.items()],
                      key=lambda x: order.get(x["label"], 9))

    rows = (db.query(m.Accused.socio_economic, func.count(m.Accused.id))
            .group_by(m.Accused.socio_economic).all())
    order = {"Low": 0, "Lower-Mid": 1, "Middle": 2, "Upper-Mid": 3, "High": 4}
    return sorted([{"label": r[0], "value": r[1]} for r in rows],
                  key=lambda x: order.get(x["label"], 9))


@router.get("/education")
def education(request: Request, db: Session = Depends(get_db)):
    if settings.use_catalyst:
        counts = Counter(a.get("education") for a in _accused_all(get_ctx(request)))
        order = {"Illiterate": 0, "Primary": 1, "Secondary": 2, "PUC": 3,
                 "Graduate": 4, "Post-Graduate": 5}
        return sorted([{"label": k, "value": v} for k, v in counts.items()],
                      key=lambda x: order.get(x["label"], 9))

    rows = (db.query(m.Accused.education, func.count(m.Accused.id))
            .group_by(m.Accused.education).all())
    order = {"Illiterate": 0, "Primary": 1, "Secondary": 2, "PUC": 3, "Graduate": 4, "Post-Graduate": 5}
    return sorted([{"label": r[0], "value": r[1]} for r in rows],
                  key=lambda x: order.get(x["label"], 9))


@router.get("/urban-rural")
def urban_rural(request: Request, db: Session = Depends(get_db)):
    if settings.use_catalyst:
        counts = Counter(a.get("urban_rural") for a in _accused_all(get_ctx(request)))
        return [{"label": k, "value": v} for k, v in counts.items()]

    rows = (db.query(m.Accused.urban_rural, func.count(m.Accused.id))
            .group_by(m.Accused.urban_rural).all())
    return [{"label": r[0], "value": r[1]} for r in rows]


@router.get("/risk-factors")
def risk_factors(request: Request, db: Session = Depends(get_db)):
    if settings.use_catalyst:
        from ..catalyst_store import get_store
        store = get_store()
        accused = _accused_all(get_ctx(request))
        profiles = store.query("SELECT * FROM behavior_profiles")
        prof_map = {p.get("accused_id"): float(p.get("risk_score", 0)) for p in profiles}
        total = len(accused) or 1

        def avg_risk(subset):
            scores = [prof_map.get(a.get("ROWID"), 0) for a in subset]
            return round(sum(scores) / max(len(scores), 1), 1)

        migrant = [a for a in accused if a.get("migrant")]
        unemployed = [a for a in accused if a.get("occupation") == "Unemployed"]
        low_edu = [a for a in accused if a.get("education") in ("Illiterate", "Primary")]
        low_ses = [a for a in accused if a.get("socio_economic") in ("Low", "Lower-Mid")]
        all_scores = [prof_map.get(a.get("ROWID"), 0) for a in accused]
        baseline = round(sum(all_scores) / max(len(all_scores), 1), 1)
        return {
            "factors": [
                {"factor": "Migrant background", "share": round(len(migrant) / total * 100, 1),
                 "avg_risk": avg_risk(migrant)},
                {"factor": "Unemployment", "share": round(len(unemployed) / total * 100, 1),
                 "avg_risk": avg_risk(unemployed)},
                {"factor": "Low education", "share": round(len(low_edu) / total * 100, 1),
                 "avg_risk": avg_risk(low_edu)},
                {"factor": "Low socio-economic", "share": round(len(low_ses) / total * 100, 1),
                 "avg_risk": avg_risk(low_ses)},
            ],
            "baseline_avg_risk": baseline,
        }

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
def crime_by_demographic(request: Request, db: Session = Depends(get_db)):
    if settings.use_catalyst:
        from ..catalyst_store import get_store
        store = get_store()
        accused = _accused_all(get_ctx(request))
        links = store.query("SELECT * FROM case_accused")
        cases = store.query("SELECT * FROM cases")
        case_map = {c.get("ROWID"): c for c in cases}
        accused_map = {a.get("ROWID"): a for a in accused}
        agg: dict[str, dict[str, int]] = {}
        for l in links:
            a = accused_map.get(l.get("accused_id"))
            if a is None:
                continue  # accused outside territory — would leak as "Unknown"
            c = case_map.get(l.get("case_id"), {})
            ses = a.get("socio_economic", "Unknown")
            ct = c.get("crime_type", "Unknown")
            agg.setdefault(ses, {})[ct] = agg.get(ses, {}).get(ct, 0) + 1
        out = []
        for ses, cts in agg.items():
            top = sorted(cts.items(), key=lambda x: -x[1])[:3]
            out.append({"socio_economic": ses, "top_crimes": [{"crime": c, "count": n} for c, n in top]})
        return out

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
