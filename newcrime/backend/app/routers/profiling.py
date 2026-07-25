"""Criminology-based offender profiling & risk scoring."""
from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..deps import get_ctx, mask_pii
from .. import models as m

router = APIRouter(prefix="/api/profiling", tags=["profiling"])


@router.get("/offenders")
def offenders(request: Request, db: Session = Depends(get_db), band: str | None = None,
              habitual: bool | None = None, limit: int = 50):
    pii = get_ctx(request).can_view_pii

    if settings.use_catalyst:
        from ..catalyst_store import get_store
        store = get_store()
        profiles = store.query("SELECT * FROM behavior_profiles ORDER BY risk_score DESC")
        if band:
            profiles = [p for p in profiles if p.get("risk_band") == band]
        if habitual is not None:
            profiles = [p for p in profiles if bool(p.get("is_habitual")) == habitual]
        profiles = profiles[:limit]
        accused_map = {a.get("ROWID"): a for a in store.query("SELECT * FROM accused")}
        case_links = store.query("SELECT * FROM case_accused")
        link_counts: dict = Counter(l.get("accused_id") for l in case_links)
        out = []
        for p in profiles:
            aid = p.get("accused_id")
            a = accused_map.get(aid, {})
            out.append({"id": aid, "name": mask_pii(a.get("full_name", ""), pii),
                        "age": a.get("age"), "gender": a.get("gender"),
                        "district": a.get("district"), "status": a.get("status"),
                        "priors": a.get("previous_convictions"), "cases": link_counts.get(aid, 0),
                        "risk_score": round(float(p.get("risk_score", 0))),
                        "risk_band": p.get("risk_band"), "habitual": p.get("is_habitual"),
                        "propensity": p.get("propensity_tags"), "traits": p.get("behavioral_traits"),
                        "modus_operandi": p.get("modus_operandi")})
        return out

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
    if settings.use_catalyst:
        from ..catalyst_store import get_store
        store = get_store()
        counts = store.aggregate("behavior_profiles", "risk_band")
        order = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}
        return sorted([{"label": k, "value": v} for k, v in counts.items()],
                      key=lambda x: order.get(x["label"], 9))

    band = (db.query(m.BehaviorProfile.risk_band, func.count(m.BehaviorProfile.id))
            .group_by(m.BehaviorProfile.risk_band).all())
    order = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}
    return sorted([{"label": r[0], "value": r[1]} for r in band],
                  key=lambda x: order.get(x["label"], 9))


@router.get("/offender/{accused_id}")
def offender_detail(accused_id: int, request: Request, db: Session = Depends(get_db)):
    pii = get_ctx(request).can_view_pii

    if settings.use_catalyst:
        from ..catalyst_store import get_store
        store = get_store()
        a = store.get("accused", accused_id)
        if not a:
            raise HTTPException(404, "accused not found")
        profs = store.query(f"SELECT * FROM behavior_profiles WHERE accused_id = {accused_id}")
        p = profs[0] if profs else {}
        links = store.query(f"SELECT * FROM case_accused WHERE accused_id = {accused_id}")
        case_ids = [l.get("case_id") for l in links]
        cases_data = []
        for cid in case_ids:
            c = store.get("cases", cid)
            if c:
                cases_data.append(c)
        return {
            "id": accused_id, "name": mask_pii(a.get("full_name", ""), pii),
            "aliases": mask_pii(a.get("aliases", ""), pii),
            "age": a.get("age"), "pii_masked": not pii,
            "gender": a.get("gender"), "district": a.get("district"),
            "address": mask_pii(a.get("address", ""), pii),
            "occupation": a.get("occupation"), "education": a.get("education"),
            "socio_economic": a.get("socio_economic"), "urban_rural": a.get("urban_rural"),
            "migrant": a.get("migrant"), "status": a.get("status"),
            "priors": a.get("previous_convictions"),
            "profile": {"risk_score": round(float(p.get("risk_score", 0))),
                        "risk_band": p.get("risk_band", "Low"),
                        "habitual": p.get("is_habitual", False),
                        "traits": p.get("behavioral_traits", ""),
                        "propensity": p.get("propensity_tags", ""),
                        "modus_operandi": p.get("modus_operandi", "")},
            "cases": [{"id": c.get("ROWID"), "fir_number": c.get("fir_number"),
                       "title": c.get("title"), "crime_type": c.get("crime_type"),
                       "status": c.get("status"), "date": c.get("occurrence_date")}
                      for c in cases_data],
        }

    a = db.get(m.Accused, accused_id)
    if not a:
        raise HTTPException(404, "accused not found")
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
