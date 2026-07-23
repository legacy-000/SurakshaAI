"""Case (FIR) browsing + investigator decision support."""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_ctx, mask_pii
from .. import models as m

router = APIRouter(prefix="/api/cases", tags=["cases"])


@router.get("")
def list_cases(db: Session = Depends(get_db),
               q: str | None = None, crime_type: str | None = None,
               district: str | None = None, status: str | None = None,
               limit: int = 50, offset: int = 0):
    query = db.query(m.Case)
    if q:
        query = query.filter(or_(m.Case.title.ilike(f"%{q}%"),
                                 m.Case.fir_number.ilike(f"%{q}%"),
                                 m.Case.location_name.ilike(f"%{q}%")))
    if crime_type:
        query = query.filter(m.Case.crime_type == crime_type)
    if district:
        query = query.filter(m.Case.district == district)
    if status:
        query = query.filter(m.Case.status == status)
    total = query.count()
    rows = query.order_by(m.Case.occurrence_date.desc()).offset(offset).limit(limit).all()
    return {"total": total, "items": [_row(c) for c in rows]}


@router.get("/filters")
def filters(db: Session = Depends(get_db)):
    return {
        "crime_types": [r[0] for r in db.query(m.Case.crime_type).distinct().all()],
        "districts": [r[0] for r in db.query(m.Case.district).distinct().all()],
        "statuses": [r[0] for r in db.query(m.Case.status).distinct().all()],
    }


@router.get("/{case_id}")
def case_detail(case_id: int, request: Request, db: Session = Depends(get_db)):
    c = db.get(m.Case, case_id)
    if not c:
        raise HTTPException(404, "case not found")
    pii = get_ctx(request).can_view_pii
    inv = c.investigation
    return {
        **_row(c),
        "description": c.description, "modus_operandi": c.modus_operandi,
        "station": c.station, "location_name": c.location_name,
        "latitude": c.latitude, "longitude": c.longitude,
        "pii_masked": not pii,
        "accused": [{"id": ca.accused.id, "name": mask_pii(ca.accused.full_name, pii),
                     "role": ca.role_in_crime, "status": ca.accused.status}
                    for ca in c.accused_links],
        "victims": [{"id": cv.victim.id, "name": mask_pii(cv.victim.full_name, pii),
                     "age": cv.victim.age, "gender": cv.victim.gender}
                    for cv in c.victim_links],
        "investigation": {"officer": inv.officer.name if inv and inv.officer else None,
                          "status": inv.status if inv else None,
                          "progress": inv.progress if inv else 0,
                          "summary": inv.summary if inv else None,
                          "leads": inv.leads_details if inv else None} if inv else None,
        "timeline": [{"title": e.event_title, "type": e.event_type,
                      "description": e.description,
                      "timestamp": e.event_timestamp.isoformat() if e.event_timestamp else None}
                     for e in sorted(c.events, key=lambda x: x.event_timestamp or c.created_at)],
    }


@router.get("/{case_id}/similar")
def similar_cases(case_id: int, db: Session = Depends(get_db)):
    """Decision support: find past cases with the same MO / crime type / district."""
    c = db.get(m.Case, case_id)
    if not c:
        raise HTTPException(404, "case not found")
    rows = (db.query(m.Case).filter(m.Case.id != c.id)
            .filter(m.Case.crime_type == c.crime_type)
            .order_by((m.Case.district == c.district).desc(),
                      (m.Case.modus_operandi == c.modus_operandi).desc(),
                      m.Case.occurrence_date.desc()).limit(6).all())

    def score(o):
        s = 40
        if o.district == c.district: s += 30
        if o.modus_operandi == c.modus_operandi: s += 30
        return s
    return {"reference": _row(c),
            "similar": [{**_row(o), "match_score": score(o),
                         "outcome": o.status} for o in rows]}


def _row(c: m.Case):
    return {"id": c.id, "fir_number": c.fir_number, "title": c.title,
            "crime_type": c.crime_type, "crime_head": c.crime_head, "status": c.status,
            "severity": c.severity, "district": c.district,
            "is_financial": c.is_financial, "loss_amount": c.loss_amount,
            "occurrence_date": c.occurrence_date.isoformat() if c.occurrence_date else None}
