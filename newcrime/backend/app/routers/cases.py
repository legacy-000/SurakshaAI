"""Case (FIR) browsing, creation, chargesheet + investigator decision support."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Form
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..deps import get_ctx, mask_pii
from .. import models as m

router = APIRouter(prefix="/api/cases", tags=["cases"])


@router.get("")
def list_cases(request: Request, db: Session = Depends(get_db),
               q: str | None = None, crime_type: str | None = None,
               district: str | None = None, status: str | None = None,
               limit: int = 50, offset: int = 0):
    ctx = get_ctx(request)
    if settings.use_catalyst:
        from ..catalyst_store import get_store
        store = get_store()
        rows = store.query("SELECT * FROM cases ORDER BY CREATEDTIME DESC")
        rows = ctx.scope_rows(rows)
        if q:
            ql = q.lower()
            rows = [c for c in rows if ql in (c.get("title") or "").lower()
                    or ql in (c.get("fir_number") or "").lower()
                    or ql in (c.get("location_name") or "").lower()]
        if crime_type:
            rows = [c for c in rows if c.get("crime_type") == crime_type]
        if district:
            rows = [c for c in rows if c.get("district") == district]
        if status:
            rows = [c for c in rows if c.get("status") == status]
        total = len(rows)
        page = rows[offset:offset + limit]
        return {"total": total, "items": [_row_dict(c) for c in page]}

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
def filters(request: Request, db: Session = Depends(get_db)):
    ctx = get_ctx(request)
    if settings.use_catalyst:
        from ..catalyst_store import get_store
        cases = ctx.scope_rows(get_store().query("SELECT * FROM cases"))
        return {
            "crime_types": sorted({c.get("crime_type") for c in cases if c.get("crime_type")}),
            "districts": sorted({c.get("district") for c in cases if c.get("district")}),
            "statuses": sorted({c.get("status") for c in cases if c.get("status")}),
        }

    return {
        "crime_types": [r[0] for r in db.query(m.Case.crime_type).distinct().all()],
        "districts": [r[0] for r in db.query(m.Case.district).distinct().all()],
        "statuses": [r[0] for r in db.query(m.Case.status).distinct().all()],
    }


@router.get("/{case_id}")
def case_detail(case_id: int, request: Request, db: Session = Depends(get_db)):
    ctx = get_ctx(request)
    pii = ctx.can_view_pii

    if settings.use_catalyst:
        from ..catalyst_store import get_store
        store = get_store()
        c = store.get("cases", case_id)
        if not c:
            raise HTTPException(404, "case not found")
        # 404, not 403 — out-of-territory cases must not be confirmed to exist
        if not ctx.can_access_district(c.get("district")):
            raise HTTPException(404, "case not found")
        accused_links = store.query(f"SELECT * FROM case_accused WHERE case_id = {case_id}")
        all_accused = {a.get("ROWID"): a for a in store.query("SELECT * FROM accused")}
        victim_links = store.query(f"SELECT * FROM case_victim WHERE case_id = {case_id}")
        all_victims = {v.get("ROWID"): v for v in store.query("SELECT * FROM victims")}
        invs = store.query(f"SELECT * FROM investigations WHERE case_id = {case_id}")
        inv = invs[0] if invs else None
        events = store.query(f"SELECT * FROM timeline_events WHERE case_id = {case_id}")
        events.sort(key=lambda e: e.get("event_timestamp") or e.get("CREATEDTIME") or "")
        officer_name = None
        if inv and inv.get("officer_id"):
            off = store.get("officers", inv.get("officer_id"))
            officer_name = off.get("name") if off else None
        return {
            **_row_dict(c),
            "description": c.get("description"), "modus_operandi": c.get("modus_operandi"),
            "station": c.get("station"), "location_name": c.get("location_name"),
            "latitude": c.get("latitude"), "longitude": c.get("longitude"),
            "pii_masked": not pii,
            "accused": [{"id": al.get("accused_id"),
                         "name": mask_pii(all_accused.get(al.get("accused_id"), {}).get("full_name", ""), pii),
                         "role": al.get("role_in_crime"),
                         "status": all_accused.get(al.get("accused_id"), {}).get("status")}
                        for al in accused_links],
            "victims": [{"id": vl.get("victim_id"),
                         "name": mask_pii(all_victims.get(vl.get("victim_id"), {}).get("full_name", ""), pii),
                         "age": all_victims.get(vl.get("victim_id"), {}).get("age"),
                         "gender": all_victims.get(vl.get("victim_id"), {}).get("gender")}
                        for vl in victim_links],
            "investigation": {"officer": officer_name,
                              "status": inv.get("status"),
                              "progress": inv.get("progress", 0),
                              "summary": inv.get("summary"),
                              "leads": inv.get("leads_details")} if inv else None,
            "timeline": [{"title": e.get("event_title"), "type": e.get("event_type"),
                          "description": e.get("description"),
                          "timestamp": e.get("event_timestamp") or e.get("CREATEDTIME")}
                         for e in events],
        }

    c = db.get(m.Case, case_id)
    if not c:
        raise HTTPException(404, "case not found")
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
def similar_cases(case_id: int, request: Request, db: Session = Depends(get_db)):
    ctx = get_ctx(request)
    if settings.use_catalyst:
        from ..catalyst_store import get_store
        store = get_store()
        c = store.get("cases", case_id)
        if not c or not ctx.can_access_district(c.get("district")):
            raise HTTPException(404, "case not found")
        ct = c.get("crime_type")
        all_cases = store.query(f"SELECT * FROM cases WHERE crime_type = '{ct}'")
        others = ctx.scope_rows([o for o in all_cases if o.get("ROWID") != case_id])

        def score(o):
            s = 40
            if o.get("district") == c.get("district"):
                s += 30
            if o.get("modus_operandi") == c.get("modus_operandi"):
                s += 30
            return s
        others.sort(key=lambda o: (-score(o), o.get("occurrence_date") or ""), reverse=False)
        others.sort(key=lambda o: -score(o))
        return {"reference": _row_dict(c),
                "similar": [{**_row_dict(o), "match_score": score(o),
                             "outcome": o.get("status")} for o in others[:6]]}

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

    if settings.use_catalyst:
        from ..catalyst_store import get_store
        store = get_store()
        if fir_number:
            existing = store.query(f"SELECT * FROM cases WHERE fir_number = '{fir_number}'")
            if existing:
                raise HTTPException(409, f"FIR {fir_number} already exists")
        else:
            count = store.count("cases")
            district_code = (form.get("district") or "UNK")[:3].upper()
            fir_number = f"FIR/{datetime.utcnow().year}/{district_code}/{1000 + count + 1}"

        occ_date = None
        if form.get("occurrence_date"):
            try:
                occ_date = str(form.get("occurrence_date"))
            except ValueError:
                pass

        loss = 0.0
        if form.get("loss_amount"):
            try:
                loss = float(str(form.get("loss_amount")))
            except ValueError:
                pass

        row = {
            "fir_number": fir_number, "title": title,
            "description": str(form.get("description") or ""),
            "crime_type": str(form.get("crime_type") or ""),
            "crime_head": str(form.get("crime_head") or ""),
            "modus_operandi": str(form.get("modus_operandi") or ""),
            "status": "Open", "severity": str(form.get("severity") or "Medium"),
            "district": str(form.get("district") or ""),
            "station": str(form.get("station") or ""),
            "location_name": str(form.get("location_name") or ""),
            "is_financial": str(form.get("is_financial")).lower() in ("true", "1", "yes"),
            "loss_amount": loss, "occurrence_date": occ_date,
            "reported_date": datetime.utcnow().isoformat(),
        }
        result = store.insert("cases", row)
        case_id = result.get("ROWID") if isinstance(result, dict) else None
        if case_id:
            store.insert("timeline_events", {
                "case_id": case_id, "event_title": "FIR Registered",
                "description": f"FIR {fir_number} registered", "event_type": "FIR",
                "event_timestamp": datetime.utcnow().isoformat(),
            })
        row["id"] = case_id
        return {"ok": True, "case": _row_dict(row)}

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
        fir_number=fir_number, title=title,
        description=str(form.get("description") or ""),
        crime_type=str(form.get("crime_type") or ""),
        crime_head=str(form.get("crime_head") or ""),
        modus_operandi=str(form.get("modus_operandi") or ""),
        status="Open", severity=str(form.get("severity") or "Medium"),
        district=str(form.get("district") or ""),
        station=str(form.get("station") or ""),
        location_name=str(form.get("location_name") or ""),
        is_financial=str(form.get("is_financial")).lower() in ("true", "1", "yes"),
        loss_amount=loss, occurrence_date=occ_date, reported_date=datetime.utcnow(),
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
    form = await request.form()

    if settings.use_catalyst:
        from ..catalyst_store import get_store
        store = get_store()
        c = store.get("cases", case_id)
        if not c:
            raise HTTPException(404, "case not found")
        updates = {}
        for field in ("title", "description", "crime_type", "crime_head", "modus_operandi",
                      "severity", "district", "station", "location_name", "status",
                      "occurrence_date"):
            val = form.get(field)
            if val is not None and str(val).strip():
                updates[field] = str(val).strip()
        for float_field in ("latitude", "longitude"):
            val = form.get(float_field)
            if val is not None and str(val).strip():
                try:
                    updates[float_field] = float(str(val))
                except ValueError:
                    pass
        if form.get("is_financial") is not None:
            updates["is_financial"] = str(form.get("is_financial")).lower() in ("true", "1", "yes")
        if form.get("loss_amount"):
            try:
                updates["loss_amount"] = float(str(form.get("loss_amount")))
            except ValueError:
                pass
        if updates:
            store.update("cases", case_id, updates)
        c.update(updates)
        return {"ok": True, "case": _row_dict(c)}

    c = db.get(m.Case, case_id)
    if not c:
        raise HTTPException(404, "case not found")

    for field in ("title", "description", "crime_type", "crime_head", "modus_operandi",
                  "severity", "district", "station", "location_name", "status",
                  "occurrence_date"):
        val = form.get(field)
        if val is not None and str(val).strip():
            setattr(c, field, str(val).strip())

    for float_field in ("latitude", "longitude"):
        val = form.get(float_field)
        if val is not None and str(val).strip():
            try:
                setattr(c, float_field, float(str(val)))
            except ValueError:
                pass

    if form.get("is_financial") is not None:
        c.is_financial = str(form.get("is_financial")).lower() in ("true", "1", "yes")

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
    ctx = get_ctx(request)

    if settings.use_catalyst:
        from ..catalyst_store import get_store
        store = get_store()
        c = store.get("cases", case_id)
        if not c:
            raise HTTPException(404, "case not found")
        al = store.query(f"SELECT * FROM case_accused WHERE case_id = {case_id}")
        all_acc = {a.get("ROWID"): a for a in store.query("SELECT * FROM accused")}
        accused = [{"id": l.get("accused_id"),
                     "name": all_acc.get(l.get("accused_id"), {}).get("full_name"),
                     "role": l.get("role_in_crime"),
                     "status": all_acc.get(l.get("accused_id"), {}).get("status")}
                    for l in al]
        vl = store.query(f"SELECT * FROM case_victim WHERE case_id = {case_id}")
        all_vic = {v.get("ROWID"): v for v in store.query("SELECT * FROM victims")}
        victims = [{"id": l.get("victim_id"),
                     "name": all_vic.get(l.get("victim_id"), {}).get("full_name"),
                     "age": all_vic.get(l.get("victim_id"), {}).get("age"),
                     "gender": all_vic.get(l.get("victim_id"), {}).get("gender")}
                    for l in vl]
        witnesses = [{"id": w.get("ROWID"), "name": w.get("name"), "reliability": w.get("reliability")}
                     for w in store.query(f"SELECT * FROM witnesses WHERE case_id = {case_id}")]
        evidence = [{"id": e.get("ROWID"), "filename": e.get("original_name"), "category": e.get("category")}
                    for e in store.query(f"SELECT * FROM evidence_documents WHERE case_id = {case_id}")]
        invs = store.query(f"SELECT * FROM investigations WHERE case_id = {case_id}")
        inv = invs[0] if invs else {}
        officer_name = None
        if inv.get("officer_id"):
            off = store.get("officers", inv.get("officer_id"))
            officer_name = off.get("name") if off else None
        sections = _infer_sections(c.get("crime_type", ""))
        chargesheet = {
            "case_id": case_id, "fir_number": c.get("fir_number"),
            "title": c.get("title"), "crime_type": c.get("crime_type"),
            "district": c.get("district"), "station": c.get("station"),
            "occurrence_date": c.get("occurrence_date"),
            "reported_date": c.get("reported_date"),
            "investigating_officer": officer_name,
            "investigation_summary": inv.get("summary"),
            "accused": accused, "victims": victims,
            "witnesses": witnesses, "evidence": evidence,
            "applicable_sections": sections, "status": "Draft",
            "generated_at": datetime.utcnow().isoformat(), "generated_by": ctx.name,
        }
        store.insert("timeline_events", {
            "case_id": case_id, "event_title": "Chargesheet Generated",
            "description": f"Chargesheet draft created by {ctx.name}",
            "event_type": "Chargesheet",
            "event_timestamp": datetime.utcnow().isoformat(),
        })
        return chargesheet

    c = db.get(m.Case, case_id)
    if not c:
        raise HTTPException(404, "case not found")

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
        "case_id": case_id, "fir_number": c.fir_number, "title": c.title,
        "crime_type": c.crime_type, "district": c.district, "station": c.station,
        "occurrence_date": c.occurrence_date.isoformat() if c.occurrence_date else None,
        "reported_date": c.reported_date.isoformat() if c.reported_date else None,
        "investigating_officer": inv.officer.name if inv and inv.officer else None,
        "investigation_summary": inv.summary if inv else None,
        "accused": accused, "victims": victims, "witnesses": witnesses, "evidence": evidence,
        "applicable_sections": sections, "status": "Draft",
        "generated_at": datetime.utcnow().isoformat(), "generated_by": ctx.name,
    }

    event = m.TimelineEvent(
        case_id=case_id, event_title="Chargesheet Generated",
        description=f"Chargesheet draft created by {ctx.name}",
        event_type="Chargesheet", event_timestamp=datetime.utcnow(),
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


def _row_dict(c: dict):
    return {"id": c.get("ROWID") or c.get("id"), "fir_number": c.get("fir_number"),
            "title": c.get("title"), "crime_type": c.get("crime_type"),
            "crime_head": c.get("crime_head"), "status": c.get("status"),
            "severity": c.get("severity"), "district": c.get("district"),
            "is_financial": c.get("is_financial"), "loss_amount": c.get("loss_amount"),
            "occurrence_date": c.get("occurrence_date")}
