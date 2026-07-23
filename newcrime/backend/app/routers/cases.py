"""Case (FIR) browsing, creation, chargesheet + investigator decision support."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Form
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


@router.post("")
async def create_fir(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    fir_number = (form.get("fir_number") or "").strip()
    title = (form.get("title") or "").strip()
    if not title:
        raise HTTPException(400, "title is required")

    if fir_number:
        existing = db.query(m.Case).filter(m.Case.fir_number == fir_number).first()
        if existing:
            raise HTTPException(409, f"FIR {fir_number} already exists")
    else:
        count = db.query(func.count(m.Case.id)).scalar() or 0
        district_code = (form.get("district") or "UNK")[:3].upper()
        fir_number = f"FIR/{datetime.utcnow().year}/{district_code}/{1000 + count + 1}"

    occ_date = None
    if form.get("occurrence_date"):
        try:
            occ_date = datetime.fromisoformat(str(form.get("occurrence_date")))
        except ValueError:
            pass

    loss = 0.0
    if form.get("loss_amount"):
        try:
            loss = float(str(form.get("loss_amount")))
        except ValueError:
            pass

    case = m.Case(
        fir_number=fir_number,
        title=title,
        description=str(form.get("description") or ""),
        crime_type=str(form.get("crime_type") or ""),
        crime_head=str(form.get("crime_head") or ""),
        modus_operandi=str(form.get("modus_operandi") or ""),
        status="Open",
        severity=str(form.get("severity") or "Medium"),
        district=str(form.get("district") or ""),
        station=str(form.get("station") or ""),
        location_name=str(form.get("location_name") or ""),
        is_financial=str(form.get("is_financial")).lower() in ("true", "1", "yes"),
        loss_amount=loss,
        occurrence_date=occ_date,
        reported_date=datetime.utcnow(),
    )
    db.add(case)
    db.flush()

    event = m.TimelineEvent(
        case_id=case.id, event_title="FIR Registered",
        description=f"FIR {fir_number} registered", event_type="FIR",
        event_timestamp=datetime.utcnow(),
    )
    db.add(event)
    db.commit()
    db.refresh(case)
    return {"ok": True, "case": _row(case)}


@router.put("/{case_id}")
async def update_case(case_id: int, request: Request, db: Session = Depends(get_db)):
    c = db.get(m.Case, case_id)
    if not c:
        raise HTTPException(404, "case not found")

    form = await request.form()
    for field in ("title", "description", "crime_type", "crime_head", "modus_operandi",
                  "severity", "district", "station", "location_name", "status"):
        val = form.get(field)
        if val is not None and str(val).strip():
            setattr(c, field, str(val).strip())

    if form.get("loss_amount"):
        try:
            c.loss_amount = float(str(form.get("loss_amount")))
        except ValueError:
            pass

    db.commit()
    db.refresh(c)
    return {"ok": True, "case": _row(c)}


@router.post("/{case_id}/chargesheet")
async def generate_chargesheet(case_id: int, request: Request, db: Session = Depends(get_db)):
    c = db.get(m.Case, case_id)
    if not c:
        raise HTTPException(404, "case not found")

    ctx = get_ctx(request)

    accused = [{"id": ca.accused.id, "name": ca.accused.full_name,
                "role": ca.role_in_crime, "status": ca.accused.status}
               for ca in c.accused_links]
    victims = [{"id": cv.victim.id, "name": cv.victim.full_name,
                "age": cv.victim.age, "gender": cv.victim.gender}
               for cv in c.victim_links]
    witnesses = [{"id": w.id, "name": w.name, "reliability": w.reliability}
                 for w in db.query(m.Witness).filter(m.Witness.case_id == case_id).all()]
    evidence = [{"id": e.id, "filename": e.original_name, "category": e.category}
                for e in db.query(m.EvidenceDocument).filter(m.EvidenceDocument.case_id == case_id).all()]
    inv = c.investigation

    sections = _infer_sections(c.crime_type)

    chargesheet = {
        "case_id": case_id,
        "fir_number": c.fir_number,
        "title": c.title,
        "crime_type": c.crime_type,
        "district": c.district,
        "station": c.station,
        "occurrence_date": c.occurrence_date.isoformat() if c.occurrence_date else None,
        "reported_date": c.reported_date.isoformat() if c.reported_date else None,
        "investigating_officer": inv.officer.name if inv and inv.officer else None,
        "investigation_summary": inv.summary if inv else None,
        "accused": accused,
        "victims": victims,
        "witnesses": witnesses,
        "evidence": evidence,
        "applicable_sections": sections,
        "status": "Draft",
        "generated_at": datetime.utcnow().isoformat(),
        "generated_by": ctx.name,
    }

    event = m.TimelineEvent(
        case_id=case_id, event_title="Chargesheet Generated",
        description=f"Chargesheet draft created by {ctx.name}",
        event_type="Chargesheet",
        event_timestamp=datetime.utcnow(),
    )
    db.add(event)
    db.commit()

    return chargesheet


def _infer_sections(crime_type: str) -> list[dict]:
    BNS_MAP: dict[str, list[dict]] = {
        "Murder": [{"code": "BNS 101", "description": "Murder"}, {"code": "BNS 103", "description": "Culpable homicide"}],
        "Theft": [{"code": "BNS 303", "description": "Theft"}, {"code": "BNS 305", "description": "Theft in dwelling house"}],
        "Robbery": [{"code": "BNS 309", "description": "Robbery"}, {"code": "BNS 310", "description": "Dacoity"}],
        "Assault": [{"code": "BNS 115", "description": "Voluntarily causing hurt"}, {"code": "BNS 117", "description": "Grievous hurt"}],
        "Kidnapping": [{"code": "BNS 137", "description": "Kidnapping"}, {"code": "BNS 140", "description": "Abduction"}],
        "Cyber Fraud": [{"code": "IT Act 66C", "description": "Identity theft"}, {"code": "IT Act 66D", "description": "Cheating by personation"}],
        "Domestic Violence": [{"code": "BNS 85", "description": "Cruelty by husband/relatives"}, {"code": "DV Act 3", "description": "Domestic violence definition"}],
        "Drug Trafficking": [{"code": "NDPS 21", "description": "Possession of drugs"}, {"code": "NDPS 22", "description": "Sale of drugs"}],
        "Extortion": [{"code": "BNS 308", "description": "Extortion"}],
        "Rioting": [{"code": "BNS 189", "description": "Unlawful assembly"}, {"code": "BNS 191", "description": "Rioting"}],
        "Burglary": [{"code": "BNS 329", "description": "House-breaking"}],
        "Chain Snatching": [{"code": "BNS 304", "description": "Snatching"}, {"code": "BNS 309", "description": "Robbery"}],
        "Vehicle Theft": [{"code": "BNS 303", "description": "Theft"}, {"code": "MV Act 39", "description": "Theft of motor vehicle"}],
        "Human Trafficking": [{"code": "BNS 143", "description": "Trafficking of person"}],
        "UPI Scam": [{"code": "IT Act 66C", "description": "Identity theft"}, {"code": "BNS 318", "description": "Cheating"}],
        "Bank Fraud": [{"code": "BNS 318", "description": "Cheating"}, {"code": "BNS 316", "description": "Criminal breach of trust"}],
        "Fraud": [{"code": "BNS 318", "description": "Cheating"}],
    }
    return BNS_MAP.get(crime_type, [{"code": "BNS General", "description": "To be determined by IO"}])


def _row(c: m.Case):
    return {"id": c.id, "fir_number": c.fir_number, "title": c.title,
            "crime_type": c.crime_type, "crime_head": c.crime_head, "status": c.status,
            "severity": c.severity, "district": c.district,
            "is_financial": c.is_financial, "loss_amount": c.loss_amount,
            "occurrence_date": c.occurrence_date.isoformat() if c.occurrence_date else None}
