"""Phase 1 — 'Work a Case' investigation workflow.

Stages, notebook (notes), evidence/document upload, witnesses, and a
system-generated timeline. Extends the existing case/investigation records
rather than duplicating them.
"""
import json
import os
import uuid
from datetime import datetime
from typing import Optional

from fastapi import (APIRouter, Depends, HTTPException, Request, UploadFile,
                     File, Form)
from fastapi.responses import FileResponse, Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..services import file_store
from ..llm import get_llm
from ..deps import get_ctx
from .. import models as m
from ..services.nlq import answer_question

router = APIRouter(prefix="/api/investigation", tags=["investigation"])

APPROVER_ROLES = {"sho", "pi", "ci", "acp", "dsp", "sp", "dig", "ig", "addl_dgp", "dgp"}

STAGES = [
    "Case Assigned", "Initial Review", "Evidence Collection", "Victim Analysis",
    "Suspect Identification", "Witness Statements", "Intelligence Gathering",
    "Criminal Analysis", "AI Investigation Completed", "Report Preparation",
    "Charges Filed", "Case Closed",
]
EVIDENCE_CATEGORIES = [
    "Evidence", "FIR Documents", "Charge Sheets", "Victim Records", "Suspect Records",
    "Witness Statements", "Forensic Reports", "Medical Reports", "Phone Records",
    "CCTV Footage", "Images", "Videos", "Audio Recordings", "Financial Documents",
    "Intelligence Reports", "Court Documents", "Miscellaneous",
]

UPLOAD_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")


def _stream(data: bytes | None, mime: str | None, filename: str | None):
    """Serve bytes pulled from the File Store as a download."""
    if data is None:
        raise HTTPException(404, "file missing")
    return Response(content=data,
                    media_type=mime or "application/octet-stream",
                    headers={"Content-Disposition":
                             f'attachment; filename="{filename or "download"}"'})


def _require_investigate(ctx):
    if not ctx.caps.get("can_investigate", False):
        raise HTTPException(403, "Your role cannot modify investigations.")


def _require_approver(ctx):
    if ctx.role not in APPROVER_ROLES or not (
        ctx.caps.get("can_investigate", False) and ctx.caps.get("can_view_audit", False)
    ):
        raise HTTPException(403, "Only SHO/DSP/Commander can approve this request.")


def _log(db, case_id, title, etype, desc):
    if settings.use_catalyst:
        from ..catalyst_store import get_store
        get_store().insert("timeline_events", {
            "case_id": case_id, "event_title": title, "event_type": etype,
            "description": desc, "event_timestamp": datetime.utcnow().isoformat(),
        })
        return
    db.add(m.TimelineEvent(case_id=case_id, event_title=title, event_type=etype,
                           description=desc, event_timestamp=datetime.utcnow()))


def _progress_for(stage: str) -> int:
    if stage not in STAGES:
        return 0
    return round((STAGES.index(stage) + 1) / len(STAGES) * 100)


def _get_store():
    from ..catalyst_store import get_store
    return get_store()


# ── Overview bundle ───────────────────────────────────────────────────
@router.get("/{case_id}")
def bundle(case_id: int, request: Request, db: Session = Depends(get_db)):
    ctx = get_ctx(request)

    if settings.use_catalyst:
        store = _get_store()
        c = store.get("cases", case_id)
        if not c:
            raise HTTPException(404, "case not found")
        invs = store.query(f"SELECT * FROM investigations WHERE case_id = {case_id}")
        inv = invs[0] if invs else None
        stage = (inv.get("current_stage") if inv else None) or STAGES[0]
        idx = STAGES.index(stage) if stage in STAGES else 0
        counts = {
            "evidence": store.count("evidence_documents", f"case_id = {case_id}"),
            "witnesses": store.count("witnesses", f"case_id = {case_id}"),
            "notes": store.count("case_notes", f"case_id = {case_id}"),
            "suspects": len(store.query(f"SELECT * FROM case_accused WHERE case_id = {case_id}")),
            "victims": len(store.query(f"SELECT * FROM case_victim WHERE case_id = {case_id}")),
        }
        officer_name = None
        if inv and inv.get("officer_id"):
            off = store.get("officers", inv.get("officer_id"))
            officer_name = off.get("name") if off else None
        return {
            "case_id": case_id, "fir_number": c.get("fir_number"), "title": c.get("title"),
            "status": c.get("status"), "stages": STAGES,
            "current_stage": stage, "stage_index": idx,
            "progress": _progress_for(stage), "remaining_stages": len(STAGES) - idx - 1,
            "can_investigate": ctx.caps.get("can_investigate", False),
            "counts": counts, "officer": officer_name,
            "evidence_categories": EVIDENCE_CATEGORIES,
        }

    c = db.get(m.Case, case_id)
    if not c:
        raise HTTPException(404, "case not found")
    inv = c.investigation
    stage = (inv.current_stage if inv and inv.current_stage else STAGES[0])
    idx = STAGES.index(stage) if stage in STAGES else 0
    counts = {
        "evidence": db.query(func.count(m.EvidenceDocument.id)).filter(m.EvidenceDocument.case_id == case_id).scalar() or 0,
        "witnesses": db.query(func.count(m.Witness.id)).filter(m.Witness.case_id == case_id).scalar() or 0,
        "notes": db.query(func.count(m.CaseNote.id)).filter(m.CaseNote.case_id == case_id).scalar() or 0,
        "suspects": len(c.accused_links), "victims": len(c.victim_links),
    }
    return {
        "case_id": case_id, "fir_number": c.fir_number, "title": c.title,
        "status": c.status, "stages": STAGES,
        "current_stage": stage, "stage_index": idx,
        "progress": _progress_for(stage), "remaining_stages": len(STAGES) - idx - 1,
        "can_investigate": ctx.caps.get("can_investigate", False),
        "counts": counts,
        "officer": inv.officer.name if inv and inv.officer else None,
        "evidence_categories": EVIDENCE_CATEGORIES,
    }


@router.post("/{case_id}/stage")
def set_stage(case_id: int, request: Request, db: Session = Depends(get_db),
              stage: str = Form(...), mode: str = Form("set")):
    ctx = get_ctx(request)
    _require_investigate(ctx)
    if stage not in STAGES:
        raise HTTPException(400, "invalid stage")

    if settings.use_catalyst:
        store = _get_store()
        c = store.get("cases", case_id)
        if not c:
            raise HTTPException(404, "case not found")
        invs = store.query(f"SELECT * FROM investigations WHERE case_id = {case_id}")
        if invs:
            inv = invs[0]
            inv_id = inv.get("ROWID")
            prev = inv.get("current_stage") or STAGES[0]
        else:
            result = store.insert("investigations", {"case_id": case_id, "status": "Active"})
            inv_id = result.get("ROWID") if isinstance(result, dict) else None
            prev = STAGES[0]
        progress = _progress_for(stage)
        updates = {"current_stage": stage, "progress": progress}
        if stage == "Case Closed":
            updates["status"] = "Solved"
        if inv_id:
            store.update("investigations", inv_id, updates)
        _log(db, case_id, f"Stage → {stage}", "Stage",
             f"{ctx.name} advanced investigation from '{prev}' to '{stage}'.")
        return {"current_stage": stage, "progress": progress,
                "remaining_stages": len(STAGES) - STAGES.index(stage) - 1}

    c = db.get(m.Case, case_id)
    if not c:
        raise HTTPException(404, "case not found")
    inv = c.investigation
    if not inv:
        inv = m.Investigation(case_id=case_id, status="Active")
        db.add(inv); db.flush()
    prev = inv.current_stage or STAGES[0]
    inv.current_stage = stage
    inv.progress = _progress_for(stage)
    if stage == "Case Closed":
        inv.status = "Solved"
    _log(db, case_id, f"Stage → {stage}", "Stage",
         f"{ctx.name} advanced investigation from '{prev}' to '{stage}'.")
    db.commit()
    return {"current_stage": stage, "progress": inv.progress,
            "remaining_stages": len(STAGES) - STAGES.index(stage) - 1}


# ── Notes ─────────────────────────────────────────────────────────────
@router.get("/{case_id}/notes")
def list_notes(case_id: int, db: Session = Depends(get_db)):
    if settings.use_catalyst:
        store = _get_store()
        rows = store.query(f"SELECT * FROM case_notes WHERE case_id = {case_id}")
        rows.sort(key=lambda n: (not n.get("pinned"), n.get("CREATEDTIME") or ""), reverse=True)
        return [{"id": n.get("ROWID"), "author": n.get("author_name"),
                 "role": n.get("author_role"), "content": n.get("content"),
                 "pinned": n.get("pinned"), "created_at": n.get("CREATEDTIME")} for n in rows]

    rows = (db.query(m.CaseNote).filter(m.CaseNote.case_id == case_id)
            .order_by(m.CaseNote.pinned.desc(), m.CaseNote.created_at.desc()).all())
    return [{"id": n.id, "author": n.author_name, "role": n.author_role,
             "content": n.content, "pinned": n.pinned,
             "created_at": n.created_at.isoformat()} for n in rows]


@router.post("/{case_id}/notes")
def add_note(case_id: int, request: Request, db: Session = Depends(get_db),
             content: str = Form(...)):
    ctx = get_ctx(request)
    if not content.strip():
        raise HTTPException(400, "empty note")

    if settings.use_catalyst:
        store = _get_store()
        result = store.insert("case_notes", {
            "case_id": case_id, "author_name": ctx.name,
            "author_role": ctx.role, "content": content.strip(), "pinned": False,
        })
        _log(db, case_id, "Note added", "Note", f"{ctx.name} added an investigation note.")
        rid = result.get("ROWID") if isinstance(result, dict) else None
        return {"id": rid, "author": ctx.name, "role": ctx.role,
                "content": content.strip(), "pinned": False,
                "created_at": datetime.utcnow().isoformat()}

    n = m.CaseNote(case_id=case_id, author_name=ctx.name, author_role=ctx.role,
                   content=content.strip())
    db.add(n)
    _log(db, case_id, "Note added", "Note", f"{ctx.name} added an investigation note.")
    db.commit(); db.refresh(n)
    return {"id": n.id, "author": n.author_name, "role": n.author_role,
            "content": n.content, "pinned": n.pinned, "created_at": n.created_at.isoformat()}


@router.post("/notes/{note_id}/pin")
def toggle_pin(note_id: int, db: Session = Depends(get_db)):
    if settings.use_catalyst:
        store = _get_store()
        n = store.get("case_notes", note_id)
        if not n:
            raise HTTPException(404, "note not found")
        new_val = not n.get("pinned")
        store.update("case_notes", note_id, {"pinned": new_val})
        return {"id": note_id, "pinned": new_val}

    n = db.get(m.CaseNote, note_id)
    if not n:
        raise HTTPException(404, "note not found")
    n.pinned = not n.pinned
    db.commit()
    return {"id": n.id, "pinned": n.pinned}


@router.delete("/notes/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db)):
    if settings.use_catalyst:
        _get_store().delete("case_notes", note_id)
        return {"ok": True}

    n = db.get(m.CaseNote, note_id)
    if n:
        db.delete(n); db.commit()
    return {"ok": True}


# ── Witnesses ─────────────────────────────────────────────────────────
@router.get("/{case_id}/witnesses")
def list_witnesses(case_id: int, request: Request, db: Session = Depends(get_db)):
    pii = get_ctx(request).can_view_pii

    if settings.use_catalyst:
        store = _get_store()
        rows = store.query(f"SELECT * FROM witnesses WHERE case_id = {case_id}")
        return [{"id": w.get("ROWID"),
                 "name": (w.get("name") if pii else (w.get("name", "")[0] + "•••••" if w.get("name") else "•••••")),
                 "contact": (w.get("contact") if pii else "•••••••"),
                 "statement": w.get("statement"), "reliability": w.get("reliability"),
                 "document_name": w.get("document_name"),
                 "document_url": (f"/api/investigation/witnesses/document/{w.get('ROWID')}"
                                   if w.get("document_path") else None),
                 "created_at": w.get("CREATEDTIME")} for w in rows]

    rows = db.query(m.Witness).filter(m.Witness.case_id == case_id).order_by(m.Witness.created_at.desc()).all()
    return [{"id": w.id, "name": (w.name if pii else w.name[0] + "•••••"),
             "contact": (w.contact if pii else "•••••••"),
             "statement": w.statement, "reliability": w.reliability,
             "document_name": w.document_name,
             "document_url": (f"/api/investigation/witnesses/document/{w.id}"
                               if w.document_path else None),
             "created_at": w.created_at.isoformat()} for w in rows]


@router.post("/{case_id}/witnesses")
async def add_witness(case_id: int, request: Request, db: Session = Depends(get_db),
                      name: str = Form(...), contact: str = Form(""),
                      statement: str = Form(""), reliability: str = Form("Medium"),
                      document: Optional[UploadFile] = File(None)):
    ctx = get_ctx(request)
    _require_investigate(ctx)

    doc_path = None
    doc_name = None
    if document is not None and document.filename:
        data = await document.read()
        stored = file_store.upload_file(
            "witness", document.filename, data,
            os.path.join(str(case_id), "witnesses"))["file_id"]
        doc_path = stored
        doc_name = document.filename

    if settings.use_catalyst:
        store = _get_store()
        result = store.insert("witnesses", {
            "case_id": case_id, "name": name.strip(), "contact": contact.strip(),
            "statement": statement.strip(), "reliability": reliability,
            "document_path": doc_path, "document_name": doc_name,
        })
        _log(db, case_id, "Witness recorded", "Statement", f"{ctx.name} recorded witness {name}.")
        rid = result.get("ROWID") if isinstance(result, dict) else None
        return {"id": rid, "name": name.strip(), "reliability": reliability,
                "document_name": doc_name,
                "document_url": (f"/api/investigation/witnesses/document/{rid}" if doc_path else None)}

    w = m.Witness(case_id=case_id, name=name.strip(), contact=contact.strip(),
                  statement=statement.strip(), reliability=reliability,
                  document_path=doc_path, document_name=doc_name)
    db.add(w)
    _log(db, case_id, "Witness recorded", "Statement", f"{ctx.name} recorded witness {name}.")
    db.commit(); db.refresh(w)
    return {"id": w.id, "name": w.name, "reliability": w.reliability,
            "document_name": w.document_name,
            "document_url": (f"/api/investigation/witnesses/document/{w.id}"
                              if w.document_path else None)}


@router.put("/{case_id}/witnesses/{witness_id}")
async def update_witness(case_id: int, witness_id: int, request: Request,
                         db: Session = Depends(get_db),
                         name: str = Form(""), contact: str = Form(""),
                         statement: str = Form(""), reliability: str = Form(""),
                         document: Optional[UploadFile] = File(None)):
    ctx = get_ctx(request)
    _require_investigate(ctx)

    if settings.use_catalyst:
        store = _get_store()
        w = store.get("witnesses", witness_id)
        if not w or w.get("case_id") != case_id:
            raise HTTPException(404, "witness not found for this case")
        updates = {}
        if name.strip(): updates["name"] = name.strip()
        if contact.strip(): updates["contact"] = contact.strip()
        if statement.strip(): updates["statement"] = statement.strip()
        if reliability.strip(): updates["reliability"] = reliability.strip()
        if document is not None and document.filename:
            data = await document.read()
            stored = file_store.upload_file(
                "witness", document.filename, data,
                os.path.join(str(case_id), "witnesses"))["file_id"]
            updates["document_path"] = stored
            updates["document_name"] = document.filename
        if updates:
            store.update("witnesses", witness_id, updates)
        _log(db, case_id, "Witness updated", "Statement",
             f"{ctx.name} updated witness {w.get('name')}.")
        return {"ok": True, "id": witness_id, "name": updates.get("name", w.get("name"))}

    w = db.get(m.Witness, witness_id)
    if not w or w.case_id != case_id:
        raise HTTPException(404, "witness not found for this case")
    if name.strip(): w.name = name.strip()
    if contact.strip(): w.contact = contact.strip()
    if statement.strip(): w.statement = statement.strip()
    if reliability.strip(): w.reliability = reliability.strip()
    if document is not None and document.filename:
        data = await document.read()
        stored = file_store.upload_file(
            "witness", document.filename, data,
            os.path.join(str(case_id), "witnesses"))["file_id"]
        w.document_path = stored
        w.document_name = document.filename
    _log(db, case_id, "Witness updated", "Statement", f"{ctx.name} updated witness {w.name}.")
    db.commit()
    return {"ok": True, "id": w.id, "name": w.name}


@router.delete("/witnesses/{witness_id}")
def delete_witness(witness_id: int, request: Request, db: Session = Depends(get_db)):
    ctx = get_ctx(request)
    _require_investigate(ctx)

    if settings.use_catalyst:
        store = _get_store()
        w = store.get("witnesses", witness_id)
        if not w:
            raise HTTPException(404, "witness not found")
        _log(db, w.get("case_id"), "Witness removed", "Statement",
             f"{ctx.name} removed witness {w.get('name')}.")
        store.delete("witnesses", witness_id)
        return {"ok": True}

    w = db.get(m.Witness, witness_id)
    if not w:
        raise HTTPException(404, "witness not found")
    case_id = w.case_id
    _log(db, case_id, "Witness removed", "Statement", f"{ctx.name} removed witness {w.name}.")
    db.delete(w)
    db.commit()
    return {"ok": True}


@router.get("/witnesses/document/{witness_id}")
def download_witness_document(witness_id: int, db: Session = Depends(get_db)):
    if settings.use_catalyst:
        store = _get_store()
        w = store.get("witnesses", witness_id)
        if not w or not w.get("document_path"):
            raise HTTPException(404, "document not found")
        sub = os.path.join(str(w.get("case_id")), "witnesses")
        return _stream(file_store.download_file("witness", w.get("document_path"), sub),
                       None, w.get("document_name") or w.get("document_path"))

    w = db.get(m.Witness, witness_id)
    if not w or not w.document_path:
        raise HTTPException(404, "document not found")
    sub = os.path.join(str(w.case_id), "witnesses")
    return _stream(file_store.download_file("witness", w.document_path, sub),
                   None, w.document_name or w.document_path)


# ── Victims ──────────────────────────────────────────────────────────

@router.get("/{case_id}/victims")
def list_case_victims(case_id: int, request: Request, db: Session = Depends(get_db)):
    ctx = get_ctx(request)

    if settings.use_catalyst:
        store = _get_store()
        links = store.query(f"SELECT * FROM case_victim WHERE case_id = {case_id}")
        all_victims = {v.get("ROWID"): v for v in store.query("SELECT * FROM victims")}
        all_links = store.query("SELECT * FROM case_victim")
        from collections import Counter
        link_counts = Counter(l.get("victim_id") for l in all_links)
        result = []
        for lk in links:
            vid = lk.get("victim_id")
            v = all_victims.get(vid, {})
            result.append({
                "id": vid, "link_id": lk.get("ROWID"),
                "name": v.get("full_name"), "gender": v.get("gender"), "age": v.get("age"),
                "contact": v.get("contact_number") if ctx.can_view_pii else "***",
                "address": v.get("address") if ctx.can_view_pii else "***",
                "district": v.get("district"), "occupation": v.get("occupation"),
                "statement_summary": v.get("statement_summary"),
                "case_count": link_counts.get(vid, 0),
                "created_at": v.get("CREATEDTIME"),
            })
        return result

    links = db.query(m.CaseVictim).filter(m.CaseVictim.case_id == case_id).all()
    result = []
    for lk in links:
        v = lk.victim
        case_count = (db.query(func.count(m.CaseVictim.id))
                      .filter(m.CaseVictim.victim_id == v.id).scalar() or 0)
        result.append({
            "id": v.id, "link_id": lk.id,
            "name": v.full_name, "gender": v.gender, "age": v.age,
            "contact": v.contact_number if ctx.can_view_pii else "***",
            "address": v.address if ctx.can_view_pii else "***",
            "district": v.district, "occupation": v.occupation,
            "statement_summary": v.statement_summary,
            "case_count": case_count,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        })
    return result


@router.post("/{case_id}/victims")
def add_victim(case_id: int, request: Request, db: Session = Depends(get_db),
               full_name: str = Form(...), gender: str = Form(""),
               age: int = Form(0), contact_number: str = Form(""),
               address: str = Form(""), district: str = Form(""),
               occupation: str = Form(""), statement_summary: str = Form("")):
    ctx = get_ctx(request)
    _require_investigate(ctx)

    if settings.use_catalyst:
        store = _get_store()
        c = store.get("cases", case_id)
        if not c:
            raise HTTPException(404, "case not found")
        v_result = store.insert("victims", {
            "full_name": full_name.strip(), "gender": gender.strip() or None,
            "age": age or None, "contact_number": contact_number.strip() or None,
            "address": address.strip() or None,
            "district": district.strip() or c.get("district"),
            "occupation": occupation.strip() or None,
            "statement_summary": statement_summary.strip() or None,
        })
        vid = v_result.get("ROWID") if isinstance(v_result, dict) else None
        if vid:
            store.insert("case_victim", {"case_id": case_id, "victim_id": vid})
        _log(db, case_id, "Victim recorded", "Victim",
             f"{ctx.name} recorded victim {full_name.strip()}.")
        return {"id": vid, "name": full_name.strip(), "gender": gender.strip(),
                "age": age, "district": district.strip() or c.get("district")}

    c = db.get(m.Case, case_id)
    if not c:
        raise HTTPException(404, "case not found")
    v = m.Victim(
        full_name=full_name.strip(), gender=gender.strip() or None,
        age=age or None, contact_number=contact_number.strip() or None,
        address=address.strip() or None, district=district.strip() or c.district,
        occupation=occupation.strip() or None,
        statement_summary=statement_summary.strip() or None,
    )
    db.add(v); db.flush()
    link = m.CaseVictim(case_id=case_id, victim_id=v.id)
    db.add(link)
    _log(db, case_id, "Victim recorded", "Victim", f"{ctx.name} recorded victim {full_name.strip()}.")
    db.commit(); db.refresh(v)
    return {"id": v.id, "name": v.full_name, "gender": v.gender,
            "age": v.age, "district": v.district}


@router.put("/{case_id}/victims/{victim_id}")
def update_victim(case_id: int, victim_id: int, request: Request,
                  db: Session = Depends(get_db),
                  full_name: str = Form(""), gender: str = Form(""),
                  age: int = Form(0), contact_number: str = Form(""),
                  address: str = Form(""), occupation: str = Form(""),
                  statement_summary: str = Form("")):
    ctx = get_ctx(request)
    _require_investigate(ctx)

    if settings.use_catalyst:
        store = _get_store()
        v = store.get("victims", victim_id)
        if not v:
            raise HTTPException(404, "victim not found")
        links = store.query(
            f"SELECT * FROM case_victim WHERE case_id = {case_id} AND victim_id = {victim_id}")
        if not links:
            raise HTTPException(404, "victim not linked to this case")
        updates = {}
        if full_name.strip(): updates["full_name"] = full_name.strip()
        if gender.strip(): updates["gender"] = gender.strip()
        if age: updates["age"] = age
        if contact_number.strip(): updates["contact_number"] = contact_number.strip()
        if address.strip(): updates["address"] = address.strip()
        if occupation.strip(): updates["occupation"] = occupation.strip()
        if statement_summary.strip(): updates["statement_summary"] = statement_summary.strip()
        if updates:
            store.update("victims", victim_id, updates)
        _log(db, case_id, "Victim updated", "Victim",
             f"{ctx.name} updated victim {v.get('full_name')}.")
        return {"ok": True}

    v = db.get(m.Victim, victim_id)
    if not v:
        raise HTTPException(404, "victim not found")
    link = (db.query(m.CaseVictim)
            .filter(m.CaseVictim.case_id == case_id, m.CaseVictim.victim_id == victim_id)
            .first())
    if not link:
        raise HTTPException(404, "victim not linked to this case")
    if full_name.strip(): v.full_name = full_name.strip()
    if gender.strip(): v.gender = gender.strip()
    if age: v.age = age
    if contact_number.strip(): v.contact_number = contact_number.strip()
    if address.strip(): v.address = address.strip()
    if occupation.strip(): v.occupation = occupation.strip()
    if statement_summary.strip(): v.statement_summary = statement_summary.strip()
    _log(db, case_id, "Victim updated", "Victim", f"{ctx.name} updated victim {v.full_name}.")
    db.commit()
    return {"ok": True}


@router.post("/{case_id}/victims/link/{victim_id}")
def link_existing_victim(case_id: int, victim_id: int, request: Request,
                         db: Session = Depends(get_db)):
    ctx = get_ctx(request)
    _require_investigate(ctx)

    if settings.use_catalyst:
        store = _get_store()
        v = store.get("victims", victim_id)
        if not v:
            raise HTTPException(404, "victim not found")
        existing = store.query(
            f"SELECT * FROM case_victim WHERE case_id = {case_id} AND victim_id = {victim_id}")
        if existing:
            raise HTTPException(409, "victim already linked to this case")
        store.insert("case_victim", {"case_id": case_id, "victim_id": victim_id})
        _log(db, case_id, "Victim linked", "Victim",
             f"{ctx.name} linked existing victim {v.get('full_name')}.")
        return {"ok": True, "id": victim_id, "name": v.get("full_name")}

    v = db.get(m.Victim, victim_id)
    if not v:
        raise HTTPException(404, "victim not found")
    existing = (db.query(m.CaseVictim)
                .filter(m.CaseVictim.case_id == case_id, m.CaseVictim.victim_id == victim_id)
                .first())
    if existing:
        raise HTTPException(409, "victim already linked to this case")
    link = m.CaseVictim(case_id=case_id, victim_id=victim_id)
    db.add(link)
    _log(db, case_id, "Victim linked", "Victim", f"{ctx.name} linked existing victim {v.full_name}.")
    db.commit()
    return {"ok": True, "id": v.id, "name": v.full_name}


@router.delete("/{case_id}/victims/{victim_id}")
def unlink_victim(case_id: int, victim_id: int, request: Request,
                  db: Session = Depends(get_db)):
    ctx = get_ctx(request)
    _require_investigate(ctx)

    if settings.use_catalyst:
        store = _get_store()
        links = store.query(
            f"SELECT * FROM case_victim WHERE case_id = {case_id} AND victim_id = {victim_id}")
        if not links:
            raise HTTPException(404, "victim not linked to this case")
        store.delete("case_victim", links[0].get("ROWID"))
        _log(db, case_id, "Victim unlinked", "Victim",
             f"{ctx.name} unlinked victim from case.")
        return {"ok": True}

    link = (db.query(m.CaseVictim)
            .filter(m.CaseVictim.case_id == case_id, m.CaseVictim.victim_id == victim_id)
            .first())
    if not link:
        raise HTTPException(404, "victim not linked to this case")
    db.delete(link)
    _log(db, case_id, "Victim unlinked", "Victim", f"{ctx.name} unlinked victim from case.")
    db.commit()
    return {"ok": True}


# ── Evidence / documents ──────────────────────────────────────────────
def _evidence_summary(name: str, category: str, data: bytes, mime: str) -> str:
    """Summarise an uploaded document with GLM.

    Says plainly when it could not summarise. The previous placeholder claimed
    "key entities and dates extracted" for every upload, which was never true —
    a fabricated analysis note attached to a police evidence record.
    """
    from ..services import fileparse

    text = fileparse.extract_text_from_bytes(data, mime or "")
    if text.strip():
        llm = get_llm()
        if getattr(llm, "available", False) and llm.provider != "mock":
            summary = llm.complete(
                "You are a police evidence analyst. Summarise this document for "
                "an investigation in 2-3 sentences: what it is, who and what it "
                "mentions, and why it may matter. State only what the text "
                "supports. Do not speculate.",
                f"Document '{name}' (category: {category}):\n\n{text[:4000]}")
            if summary and summary.strip():
                return summary.strip()
        return (f"'{name}' filed under {category}. Text extracted "
                f"({len(text)} chars); no AI summary available.")
    return (f"'{name}' filed under {category}. "
            "Not machine-readable — manual review required.")


@router.get("/{case_id}/evidence")
def list_evidence(case_id: int, db: Session = Depends(get_db), category: str | None = None):
    if settings.use_catalyst:
        store = _get_store()
        rows = store.query(f"SELECT * FROM evidence_documents WHERE case_id = {case_id}")
        if category:
            rows = [e for e in rows if e.get("category") == category]
        return [{"id": e.get("ROWID"), "category": e.get("category"),
                 "original_name": e.get("original_name"), "mime": e.get("mime"),
                 "size": e.get("size"), "uploaded_by": e.get("uploaded_by"),
                 "ai_summary": e.get("ai_summary"), "remarks": e.get("remarks"),
                 "created_at": e.get("CREATEDTIME")} for e in rows]

    q = db.query(m.EvidenceDocument).filter(m.EvidenceDocument.case_id == case_id)
    if category:
        q = q.filter(m.EvidenceDocument.category == category)
    rows = q.order_by(m.EvidenceDocument.created_at.desc()).all()
    return [{"id": e.id, "category": e.category, "original_name": e.original_name,
             "mime": e.mime, "size": e.size, "uploaded_by": e.uploaded_by,
             "ai_summary": e.ai_summary, "remarks": e.remarks,
             "created_at": e.created_at.isoformat()} for e in rows]


@router.post("/{case_id}/evidence")
async def upload_evidence(case_id: int, request: Request, db: Session = Depends(get_db),
                          category: str = Form("Evidence"), file: UploadFile = File(...),
                          remarks: str = Form("")):
    ctx = get_ctx(request)
    _require_investigate(ctx)

    data = await file.read()
    # Function instances have ephemeral disks — evidence must go to the File
    # Store or it disappears when the instance recycles.
    saved = file_store.upload_file("evidence", file.filename, data, str(case_id))
    stored = saved["file_id"]
    summary = _evidence_summary(file.filename, category, data, file.content_type or "")

    if settings.use_catalyst:
        store = _get_store()
        c = store.get("cases", case_id)
        if not c:
            raise HTTPException(404, "case not found")
        result = store.insert("evidence_documents", {
            "case_id": case_id, "category": category, "filename": stored,
            "original_name": file.filename,
            "mime": file.content_type or "application/octet-stream",
            "size": len(data), "uploaded_by": ctx.name,
            "ai_summary": summary,
            "remarks": remarks.strip() or None,
        })
        _log(db, case_id, "Evidence uploaded", "Evidence",
             f"{ctx.name} uploaded '{file.filename}' ({category}).")
        rid = result.get("ROWID") if isinstance(result, dict) else None
        return {"id": rid, "original_name": file.filename, "category": category,
                "size": len(data), "ai_summary": summary,
                "remarks": remarks.strip() or None}

    c = db.get(m.Case, case_id)
    if not c:
        raise HTTPException(404, "case not found")
    doc = m.EvidenceDocument(case_id=case_id, category=category, filename=stored,
                             original_name=file.filename,
                             mime=file.content_type or "application/octet-stream",
                             size=len(data), uploaded_by=ctx.name,
                             ai_summary=summary,
                             remarks=remarks.strip() or None)
    db.add(doc)
    _log(db, case_id, "Evidence uploaded", "Evidence",
         f"{ctx.name} uploaded '{file.filename}' ({category}).")
    db.commit(); db.refresh(doc)
    return {"id": doc.id, "original_name": doc.original_name, "category": doc.category,
            "size": doc.size, "ai_summary": doc.ai_summary, "remarks": doc.remarks}


@router.get("/evidence/{doc_id}/download")
def download_evidence(doc_id: int, db: Session = Depends(get_db)):
    if settings.use_catalyst:
        store = _get_store()
        doc = store.get("evidence_documents", doc_id)
        if not doc:
            raise HTTPException(404, "not found")
        return _stream(file_store.download_file("evidence", doc.get("filename"),
                                                str(doc.get("case_id"))),
                       doc.get("mime"), doc.get("original_name"))

    doc = db.get(m.EvidenceDocument, doc_id)
    if not doc:
        raise HTTPException(404, "not found")
    return _stream(file_store.download_file("evidence", doc.filename, str(doc.case_id)),
                   doc.mime, doc.original_name)


@router.delete("/evidence/{doc_id}")
def delete_evidence(doc_id: int, request: Request, db: Session = Depends(get_db)):
    _require_investigate(get_ctx(request))

    if settings.use_catalyst:
        store = _get_store()
        doc = store.get("evidence_documents", doc_id)
        if doc:
            file_store.delete_file("evidence", doc.get("filename"),
                                   str(doc.get("case_id")))
            store.delete("evidence_documents", doc_id)
        return {"ok": True}

    doc = db.get(m.EvidenceDocument, doc_id)
    if doc:
        file_store.delete_file("evidence", doc.filename, str(doc.case_id))
        db.delete(doc); db.commit()
    return {"ok": True}


# ── Stage approvals ────────────────────────────────────────────────────
def _approval_json(a):
    if isinstance(a, dict):
        return {"id": a.get("ROWID"), "case_id": a.get("case_id"), "stage": a.get("stage"),
                "action": a.get("action"), "requested_by": a.get("requested_by"),
                "requested_role": a.get("requested_role"), "approved_by": a.get("approved_by"),
                "approved_role": a.get("approved_role"), "comments": a.get("comments"),
                "created_at": a.get("CREATEDTIME")}
    return {"id": a.id, "case_id": a.case_id, "stage": a.stage, "action": a.action,
            "requested_by": a.requested_by, "requested_role": a.requested_role,
            "approved_by": a.approved_by, "approved_role": a.approved_role,
            "comments": a.comments, "created_at": a.created_at.isoformat()}


@router.post("/{case_id}/stage/request")
def request_stage(case_id: int, request: Request, db: Session = Depends(get_db),
                  stage: str = Form(...), comments: str = Form("")):
    ctx = get_ctx(request)
    _require_investigate(ctx)
    if stage not in STAGES:
        raise HTTPException(400, "invalid stage")

    if settings.use_catalyst:
        store = _get_store()
        c = store.get("cases", case_id)
        if not c:
            raise HTTPException(404, "case not found")
        result = store.insert("stage_approvals", {
            "case_id": case_id, "stage": stage, "action": "requested",
            "requested_by": ctx.name, "requested_role": ctx.role,
            "comments": comments.strip() or None,
        })
        _log(db, case_id, "Stage advancement requested", "Approval",
             f"{ctx.name} requested advancement to '{stage}'.")
        return _approval_json(result if isinstance(result, dict) else {})

    c = db.get(m.Case, case_id)
    if not c:
        raise HTTPException(404, "case not found")
    a = m.StageApproval(case_id=case_id, stage=stage, action="requested",
                        requested_by=ctx.name, requested_role=ctx.role,
                        comments=comments.strip() or None)
    db.add(a)
    _log(db, case_id, "Stage advancement requested", "Approval",
         f"{ctx.name} requested advancement to '{stage}'.")
    db.commit(); db.refresh(a)
    return _approval_json(a)


@router.get("/{case_id}/approvals")
def list_approvals(case_id: int, db: Session = Depends(get_db)):
    if settings.use_catalyst:
        rows = _get_store().query(f"SELECT * FROM stage_approvals WHERE case_id = {case_id}")
        return [_approval_json(a) for a in rows]

    rows = (db.query(m.StageApproval).filter(m.StageApproval.case_id == case_id)
            .order_by(m.StageApproval.created_at.desc()).all())
    return [_approval_json(a) for a in rows]


@router.post("/approval/{approval_id}/review")
def review_approval(approval_id: int, request: Request, db: Session = Depends(get_db),
                    action: str = Form(...), comments: str = Form("")):
    ctx = get_ctx(request)
    _require_approver(ctx)
    if action not in ("approved", "rejected"):
        raise HTTPException(400, "action must be 'approved' or 'rejected'")

    if settings.use_catalyst:
        store = _get_store()
        a = store.get("stage_approvals", approval_id)
        if not a:
            raise HTTPException(404, "approval request not found")
        updates = {"action": action, "approved_by": ctx.name, "approved_role": ctx.role}
        if comments.strip():
            updates["comments"] = comments.strip()
        store.update("stage_approvals", approval_id, updates)

        if action == "approved" and a.get("stage") in STAGES:
            case_id = a.get("case_id")
            invs = store.query(f"SELECT * FROM investigations WHERE case_id = {case_id}")
            if invs:
                inv_id = invs[0].get("ROWID")
                prev = invs[0].get("current_stage") or STAGES[0]
            else:
                res = store.insert("investigations", {"case_id": case_id, "status": "Active"})
                inv_id = res.get("ROWID") if isinstance(res, dict) else None
                prev = STAGES[0]
            upd = {"current_stage": a.get("stage"), "progress": _progress_for(a.get("stage"))}
            if a.get("stage") == "Case Closed":
                upd["status"] = "Solved"
            if inv_id:
                store.update("investigations", inv_id, upd)
            _log(db, case_id, f"Stage → {a.get('stage')}", "Stage",
                 f"{ctx.name} approved advancement from '{prev}' to '{a.get('stage')}' "
                 f"(requested by {a.get('requested_by')}).")
        else:
            _log(db, a.get("case_id"), "Stage request rejected", "Approval",
                 f"{ctx.name} rejected advancement to '{a.get('stage')}' requested by {a.get('requested_by')}.")
        a.update(updates)
        return _approval_json(a)

    a = db.get(m.StageApproval, approval_id)
    if not a:
        raise HTTPException(404, "approval request not found")
    a.action = action
    a.approved_by = ctx.name
    a.approved_role = ctx.role
    if comments.strip():
        a.comments = comments.strip()

    if action == "approved" and a.stage in STAGES:
        c = db.get(m.Case, a.case_id)
        if c:
            inv = c.investigation
            if not inv:
                inv = m.Investigation(case_id=a.case_id, status="Active")
                db.add(inv); db.flush()
            prev = inv.current_stage or STAGES[0]
            inv.current_stage = a.stage
            inv.progress = _progress_for(a.stage)
            if a.stage == "Case Closed":
                inv.status = "Solved"
            _log(db, a.case_id, f"Stage → {a.stage}", "Stage",
                 f"{ctx.name} approved advancement from '{prev}' to '{a.stage}' "
                 f"(requested by {a.requested_by}).")
    else:
        _log(db, a.case_id, "Stage request rejected", "Approval",
             f"{ctx.name} rejected advancement to '{a.stage}' requested by {a.requested_by}.")

    db.commit(); db.refresh(a)
    return _approval_json(a)


# ── Access requests ────────────────────────────────────────────────────
def _access_json(r):
    if isinstance(r, dict):
        return {"id": r.get("ROWID"), "case_id": r.get("case_id"),
                "requested_by": r.get("requested_by"),
                "requested_role": r.get("requested_role"), "reason": r.get("reason"),
                "status": r.get("status"), "reviewed_by": r.get("reviewed_by"),
                "created_at": r.get("CREATEDTIME")}
    return {"id": r.id, "case_id": r.case_id, "requested_by": r.requested_by,
            "requested_role": r.requested_role, "reason": r.reason,
            "status": r.status, "reviewed_by": r.reviewed_by,
            "created_at": r.created_at.isoformat()}


@router.post("/{case_id}/request-access")
def request_access(case_id: int, request: Request, db: Session = Depends(get_db),
                   requested_role: str = Form(""), reason: str = Form("")):
    ctx = get_ctx(request)

    if settings.use_catalyst:
        store = _get_store()
        c = store.get("cases", case_id)
        if not c:
            raise HTTPException(404, "case not found")
        role = requested_role.strip() or ctx.role
        result = store.insert("access_requests", {
            "case_id": case_id, "requested_by": ctx.name,
            "requested_role": role, "reason": reason.strip() or None, "status": "pending",
        })
        _log(db, case_id, "Access requested", "Access",
             f"{ctx.name} requested '{requested_role}' access.")
        return _access_json(result if isinstance(result, dict) else {})

    c = db.get(m.Case, case_id)
    if not c:
        raise HTTPException(404, "case not found")
    role = requested_role.strip() or ctx.role
    r = m.AccessRequest(case_id=case_id, requested_by=ctx.name,
                        requested_role=role, reason=reason.strip() or None,
                        status="pending")
    db.add(r)
    _log(db, case_id, "Access requested", "Access",
         f"{ctx.name} requested '{requested_role}' access.")
    db.commit(); db.refresh(r)
    return _access_json(r)


@router.get("/{case_id}/access-requests")
def list_access_requests(case_id: int, db: Session = Depends(get_db)):
    if settings.use_catalyst:
        rows = _get_store().query(f"SELECT * FROM access_requests WHERE case_id = {case_id}")
        return [_access_json(r) for r in rows]

    rows = (db.query(m.AccessRequest).filter(m.AccessRequest.case_id == case_id)
            .order_by(m.AccessRequest.created_at.desc()).all())
    return [_access_json(r) for r in rows]


@router.post("/access-request/{request_id}/review")
def review_access_request(request_id: int, request: Request, db: Session = Depends(get_db),
                          action: str = Form(...)):
    ctx = get_ctx(request)
    _require_approver(ctx)
    if action not in ("approved", "rejected"):
        raise HTTPException(400, "action must be 'approved' or 'rejected'")

    if settings.use_catalyst:
        store = _get_store()
        r = store.get("access_requests", request_id)
        if not r:
            raise HTTPException(404, "access request not found")
        store.update("access_requests", request_id, {
            "status": action, "reviewed_by": ctx.name})
        _log(db, r.get("case_id"), "Access request reviewed", "Access",
             f"{ctx.name} {action} access request from {r.get('requested_by')} "
             f"(role: {r.get('requested_role')}).")
        r["status"] = action
        r["reviewed_by"] = ctx.name
        return _access_json(r)

    r = db.get(m.AccessRequest, request_id)
    if not r:
        raise HTTPException(404, "access request not found")
    r.status = action
    r.reviewed_by = ctx.name
    _log(db, r.case_id, "Access request reviewed", "Access",
         f"{ctx.name} {action} access request from {r.requested_by} "
         f"(role: {r.requested_role}).")
    db.commit(); db.refresh(r)
    return _access_json(r)


EMERGENCY_ROLES = {"dsp", "sp", "dig", "ig", "addl_dgp", "dgp"}

@router.post("/{case_id}/emergency-access")
def emergency_access(case_id: int, request: Request, db: Session = Depends(get_db),
                     reason: str = Form("")):
    ctx = get_ctx(request)
    if ctx.role not in EMERGENCY_ROLES:
        raise HTTPException(403, "Emergency access is restricted to DSP and Commander roles.")
    if not reason.strip():
        raise HTTPException(400, "Justification is required for emergency access.")

    if settings.use_catalyst:
        store = _get_store()
        c = store.get("cases", case_id)
        if not c:
            raise HTTPException(404, "case not found")
        store.insert("access_requests", {
            "case_id": case_id, "requested_by": ctx.name,
            "requested_role": ctx.role, "reason": f"[EMERGENCY] {reason.strip()}",
            "status": "approved", "reviewed_by": "SYSTEM (emergency override)",
        })
        _log(db, case_id, "Emergency access granted", "Access",
             f"{ctx.name} ({ctx.role}) invoked emergency access override. Reason: {reason.strip()}")
        return {"status": "granted", "message": "Emergency access granted. This action has been logged for audit."}

    c = db.get(m.Case, case_id)
    if not c:
        raise HTTPException(404, "case not found")
    r = m.AccessRequest(case_id=case_id, requested_by=ctx.name,
                        requested_role=ctx.role, reason=f"[EMERGENCY] {reason.strip()}",
                        status="approved", reviewed_by="SYSTEM (emergency override)")
    db.add(r)
    _log(db, case_id, "Emergency access granted", "Access",
         f"{ctx.name} ({ctx.role}) invoked emergency access override. Reason: {reason.strip()}")
    db.commit(); db.refresh(r)
    return {"status": "granted", "message": "Emergency access granted. This action has been logged for audit."}


# ── Approval console (cross-case) ────────────────────────────────────
@router.get("/approvals/pending")
def all_pending_approvals(request: Request, db: Session = Depends(get_db)):
    ctx = get_ctx(request)
    _require_approver(ctx)

    if settings.use_catalyst:
        store = _get_store()
        rows = store.query("SELECT * FROM stage_approvals WHERE action = 'requested'")
        result = []
        for a in rows:
            c = store.get("cases", a.get("case_id"))
            d = _approval_json(a)
            d["fir_number"] = c.get("fir_number") if c else "?"
            d["case_title"] = c.get("title") if c else "?"
            result.append(d)
        return result

    rows = (db.query(m.StageApproval).filter(m.StageApproval.action == "requested")
            .order_by(m.StageApproval.created_at.desc()).all())
    result = []
    for a in rows:
        c = db.get(m.Case, a.case_id)
        d = _approval_json(a)
        d["fir_number"] = c.fir_number if c else "?"
        d["case_title"] = c.title if c else "?"
        result.append(d)
    return result


@router.get("/access-requests/pending")
def all_pending_access(request: Request, db: Session = Depends(get_db)):
    ctx = get_ctx(request)
    _require_approver(ctx)

    if settings.use_catalyst:
        store = _get_store()
        rows = store.query("SELECT * FROM access_requests WHERE status = 'pending'")
        result = []
        for r in rows:
            c = store.get("cases", r.get("case_id"))
            d = _access_json(r)
            d["fir_number"] = c.get("fir_number") if c else "?"
            d["case_title"] = c.get("title") if c else "?"
            result.append(d)
        return result

    rows = (db.query(m.AccessRequest).filter(m.AccessRequest.status == "pending")
            .order_by(m.AccessRequest.created_at.desc()).all())
    result = []
    for r in rows:
        c = db.get(m.Case, r.case_id)
        d = _access_json(r)
        d["fir_number"] = c.fir_number if c else "?"
        d["case_title"] = c.title if c else "?"
        result.append(d)
    return result


# ── Case-scoped AI chat ─────────────────────────────────────────────────
def _chat_msg(x):
    if isinstance(x, dict):
        return {"id": x.get("ROWID"), "role": x.get("role"), "content": x.get("content"),
                "language": x.get("language"), "sql": x.get("sql_text"),
                "intent": x.get("intent"),
                "evidence": json.loads(x.get("evidence_json") or "[]"),
                "grounding": json.loads(x.get("grounding_json") or "{}"),
                "reasoning": json.loads(x.get("reasoning_json") or "[]"),
                "created_at": x.get("CREATEDTIME")}
    return {"id": x.id, "role": x.role, "content": x.content, "language": x.language,
            "sql": x.sql_text, "intent": x.intent,
            "evidence": json.loads(x.evidence_json) if x.evidence_json else [],
            "grounding": json.loads(x.grounding_json) if x.grounding_json else {},
            "reasoning": json.loads(x.reasoning_json) if x.reasoning_json else [],
            "created_at": x.created_at.isoformat()}


def _get_or_create_case_conversation(db, case_id, case_fir, user_id=None):
    if settings.use_catalyst:
        store = _get_store()
        convs = store.query(f"SELECT * FROM conversations WHERE case_id = {case_id}")
        if convs:
            return convs[0].get("ROWID"), False
        result = store.insert("conversations", {
            "title": f"Case {case_fir} investigation",
            "case_id": case_id, "language": "en", "user_id": user_id,
        })
        return (result.get("ROWID") if isinstance(result, dict) else None), True

    conv = (db.query(m.Conversation).filter(m.Conversation.case_id == case_id)
            .order_by(m.Conversation.created_at.desc()).first())
    if conv:
        return conv.id, False
    conv = m.Conversation(title=f"Case {case_fir} investigation",
                          case_id=case_id, language="en", user_id=user_id)
    db.add(conv); db.flush()
    return conv.id, True


@router.get("/{case_id}/chat")
def get_case_chat(case_id: int, db: Session = Depends(get_db)):
    if settings.use_catalyst:
        store = _get_store()
        c = store.get("cases", case_id)
        if not c:
            raise HTTPException(404, "case not found")
        conv_id, _ = _get_or_create_case_conversation(db, case_id, c.get("fir_number"))
        msgs = store.query(f"SELECT * FROM messages WHERE conversation_id = {conv_id}") if conv_id else []
        return {"conversation_id": conv_id, "case_id": case_id,
                "messages": [_chat_msg(x) for x in msgs]}

    c = db.get(m.Case, case_id)
    if not c:
        raise HTTPException(404, "case not found")
    conv_id, created = _get_or_create_case_conversation(db, case_id, c.fir_number)
    if created:
        db.commit()
    conv = db.get(m.Conversation, conv_id)
    return {"conversation_id": conv_id, "case_id": case_id,
            "messages": [_chat_msg(x) for x in conv.messages]}


@router.post("/{case_id}/chat")
async def send_case_chat(case_id: int, request: Request, db: Session = Depends(get_db)):
    from ..services.fileparse import extract_text, extract_entities, is_supported

    content_type = request.headers.get("content-type", "")
    file_context = ""
    entities_found: dict | None = None
    uploaded_files: list[str] = []

    if "multipart/form-data" in content_type:
        form = await request.form()
        message = (form.get("message") or "").strip()
        language = form.get("language", "")

        for key in form:
            upload = form[key]
            if not hasattr(upload, "filename") or not upload.filename:
                continue
            if key in ("message", "language"):
                continue
            file_bytes = await upload.read()
            fname = upload.filename
            uploaded_files.append(fname)

            if is_supported(fname):
                text = extract_text(file_bytes, fname)
                if text:
                    file_context += f"\n--- Content of {fname} ---\n{text}\n"
                    ents = extract_entities(text)
                    if any(ents.values()):
                        entities_found = ents

                file_store.upload_file(
                    "chat", fname, file_bytes,
                    os.path.join(str(case_id), "chat_uploads"))
            else:
                file_context += f"\n[Unsupported file type: {fname}]\n"
    else:
        body = await request.json()
        message = body.get("message", "").strip()
        language = body.get("language", "")

    combined = message
    if file_context:
        combined = f"{message}\n\nUploaded document content:{file_context}" if message else f"Analyse the uploaded document:{file_context}"
    if not combined.strip():
        raise HTTPException(400, "empty message")

    ctx = get_ctx(request)

    if settings.use_catalyst:
        store = _get_store()
        c = store.get("cases", case_id)
        if not c:
            raise HTTPException(404, "case not found")
        conv_id, _ = _get_or_create_case_conversation(db, case_id, c.get("fir_number"),
                                                       user_id=ctx.user_id)
        lang = language or None
        result = answer_question(db, combined, lang)

        if entities_found and any(entities_found.values()):
            from .chat import _append_entities
            _append_entities(result, entities_found)

        display_msg = message or f"[Uploaded: {', '.join(uploaded_files)}]"
        store.insert("messages", {
            "conversation_id": conv_id, "role": "user", "content": display_msg,
            "language": result["language"],
            "intent": result["intent"] or "unknown",
        })
        store.insert("messages", {
            "conversation_id": conv_id, "role": "assistant", "content": result["answer"],
            "language": result["language"], "sql_text": result["sql"],
            "evidence_json": json.dumps(result["evidence"]),
            "intent": result["intent"] or "unknown",
            "grounding_json": json.dumps(result.get("grounding", {})),
            "reasoning_json": json.dumps(result.get("reasoning", [])),
        })
        _log(db, case_id, "AI chat message", "Chat",
             f"{ctx.name} asked the case assistant a question.")
        return {"conversation_id": conv_id, "case_id": case_id,
                "answer": result["answer"], "sql": result["sql"],
                "evidence": result["evidence"], "intent": result["intent"],
                "language": result["language"], "provider": result["provider"],
                "grounding": result.get("grounding", {}),
                "reasoning": result.get("reasoning", []),
                "uploaded_files": uploaded_files, "entities": entities_found}

    c = db.get(m.Case, case_id)
    if not c:
        raise HTTPException(404, "case not found")
    conv_id, _ = _get_or_create_case_conversation(db, case_id, c.fir_number,
                                                   user_id=ctx.user_id)
    conv = db.get(m.Conversation, conv_id)

    lang = language or None
    result = answer_question(db, combined, lang)

    if entities_found and any(entities_found.values()):
        from .chat import _append_entities
        _append_entities(result, entities_found)

    display_msg = message or f"[Uploaded: {', '.join(uploaded_files)}]"
    um = m.Message(conversation_id=conv_id, role="user", content=display_msg,
                   language=result["language"])
    am = m.Message(conversation_id=conv_id, role="assistant", content=result["answer"],
                   language=result["language"], sql_text=result["sql"],
                   evidence_json=json.dumps(result["evidence"]), intent=result["intent"],
                   grounding_json=json.dumps(result.get("grounding", {})),
                   reasoning_json=json.dumps(result.get("reasoning", [])))
    db.add_all([um, am])
    conv.updated_at = datetime.utcnow()
    _log(db, case_id, "AI chat message", "Chat", f"{ctx.name} asked the case assistant a question.")
    db.commit()

    return {"conversation_id": conv_id, "case_id": case_id,
            "answer": result["answer"], "sql": result["sql"],
            "evidence": result["evidence"], "intent": result["intent"],
            "language": result["language"], "provider": result["provider"],
            "grounding": result.get("grounding", {}),
            "reasoning": result.get("reasoning", []),
            "uploaded_files": uploaded_files, "entities": entities_found}
