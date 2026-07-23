"""Criminology-based offender profiling & risk scoring."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_ctx, mask_pii
from .. import models as m

router = APIRouter(prefix="/api/profiling", tags=["profiling"])


@router.get("/offenders")
def offenders(request: Request, db: Session = Depends(get_db), band: str | None = None,
              habitual: bool | None = None, limit: int = 50):
    pii = get_ctx(request).can_view_pii
    q = (db.query(m.Accused, m.BehaviorProfile)
         .join(m.BehaviorProfile, m.BehaviorProfile.accused_id == m.Accused.id))
    if band:
        q = q.filter(m.BehaviorProfile.risk_band == band)
    if habitual is not None:
        q = q.filter(m.BehaviorProfile.is_habitual.is_(habitual))
    rows = q.order_by(m.BehaviorProfile.risk_score.desc()).limit(limit).all()
    return [{"id": a.id, "name": mask_pii(a.full_name, pii), "age": a.age, "gender": a.gender,
             "district": a.district, "status": a.status,
             "priors": a.previous_convictions, "cases": len(a.case_links),
             "risk_score": round(p.risk_score), "risk_band": p.risk_band,
             "habitual": p.is_habitual, "propensity": p.propensity_tags,
             "traits": p.behavioral_traits, "modus_operandi": p.modus_operandi}
            for a, p in rows]


@router.get("/distribution")
def distribution(db: Session = Depends(get_db)):
    band = (db.query(m.BehaviorProfile.risk_band, func.count(m.BehaviorProfile.id))
            .group_by(m.BehaviorProfile.risk_band).all())
    order = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}
    return sorted([{"label": r[0], "value": r[1]} for r in band],
                  key=lambda x: order.get(x["label"], 9))


@router.get("/offender/{accused_id}")
def offender_detail(accused_id: int, request: Request, db: Session = Depends(get_db)):
    a = db.get(m.Accused, accused_id)
    if not a:
        raise HTTPException(404, "accused not found")
    pii = get_ctx(request).can_view_pii
    p = a.profile
    cases = [ca.case for ca in a.case_links]
    return {
        "id": a.id, "name": mask_pii(a.full_name, pii), "aliases": mask_pii(a.aliases, pii),
        "age": a.age, "pii_masked": not pii,
        "gender": a.gender, "district": a.district, "address": mask_pii(a.address, pii),
        "occupation": a.occupation, "education": a.education,
        "socio_economic": a.socio_economic, "urban_rural": a.urban_rural,
        "migrant": a.migrant, "status": a.status,
        "priors": a.previous_convictions,
        "profile": {"risk_score": round(p.risk_score) if p else 0,
                    "risk_band": p.risk_band if p else "Low",
                    "habitual": p.is_habitual if p else False,
                    "traits": p.behavioral_traits if p else "",
                    "propensity": p.propensity_tags if p else "",
                    "modus_operandi": p.modus_operandi if p else ""},
        "cases": [{"id": c.id, "fir_number": c.fir_number, "title": c.title,
                   "crime_type": c.crime_type, "status": c.status,
                   "date": c.occurrence_date.isoformat() if c.occurrence_date else None}
                  for c in cases],
    }
