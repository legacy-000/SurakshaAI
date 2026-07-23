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
from fastapi.responses import FileResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_ctx
from .. import models as m
from ..services.nlq import answer_question

router = APIRouter(prefix="/api/investigation", tags=["investigation"])

# Roles allowed to approve stage advancement / access requests.
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
os.makedirs(UPLOAD_ROOT, exist_ok=True)


def _require_investigate(ctx):
    if not ctx.caps.get("can_investigate", False):
        raise HTTPException(403, "Your role cannot modify investigations.")


def _require_approver(ctx):
    """Approvals require at least SHO level (can_investigate + audit access)."""
    if ctx.role not in APPROVER_ROLES or not (
        ctx.caps.get("can_investigate", False) and ctx.caps.get("can_view_audit", False)
    ):
        raise HTTPException(403, "Only SHO/DSP/Commander can approve this request.")


def _log(db, case_id, title, etype, desc):
    db.add(m.TimelineEvent(case_id=case_id, event_title=title, event_type=etype,
                           description=desc, event_timestamp=datetime.utcnow()))


def _progress_for(stage: str) -> int:
    if stage not in STAGES:
        return 0
    return round((STAGES.index(stage) + 1) / len(STAGES) * 100)


# ── Overview bundle ───────────────────────────────────────────────────
@router.get("/{case_id}")
def bundle(case_id: int, request: Request, db: Session = Depends(get_db)):
    ctx = get_ctx(request)
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
        "status": c.status,
        "stages": STAGES,
        "current_stage": stage, "stage_index": idx,
        "progress": _progress_for(stage),
        "remaining_stages": len(STAGES) - idx - 1,
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
    n = m.CaseNote(case_id=case_id, author_name=ctx.name, author_role=ctx.role,
                   content=content.strip())
    db.add(n)
    _log(db, case_id, "Note added", "Note", f"{ctx.name} added an investigation note.")
    db.commit(); db.refresh(n)
    return {"id": n.id, "author": n.author_name, "role": n.author_role,
            "content": n.content, "pinned": n.pinned, "created_at": n.created_at.isoformat()}


@router.post("/notes/{note_id}/pin")
def toggle_pin(note_id: int, db: Session = Depends(get_db)):
    n = db.get(m.CaseNote, note_id)
    if not n:
        raise HTTPException(404, "note not found")
    n.pinned = not n.pinned
    db.commit()
    return {"id": n.id, "pinned": n.pinned}


@router.delete("/notes/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db)):
    n = db.get(m.CaseNote, note_id)
    if n:
        db.delete(n); db.commit()
    return {"ok": True}


# ── Witnesses ─────────────────────────────────────────────────────────
@router.get("/{case_id}/witnesses")
def list_witnesses(case_id: int, request: Request, db: Session = Depends(get_db)):
    pii = get_ctx(request).can_view_pii
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
    w = m.Witness(case_id=case_id, name=name.strip(), contact=contact.strip(),
                  statement=statement.strip(), reliability=reliability)

    if document is not None and document.filename:
        wit_dir = os.path.join(UPLOAD_ROOT, str(case_id), "witnesses")
        os.makedirs(wit_dir, exist_ok=True)
        stored = f"{uuid.uuid4().hex}_{document.filename}"
        path = os.path.join(wit_dir, stored)
        data = await document.read()
        with open(path, "wb") as fh:
            fh.write(data)
        w.document_path = stored
        w.document_name = document.filename

    db.add(w)
    _log(db, case_id, "Witness recorded", "Statement", f"{ctx.name} recorded witness {name}.")
    db.commit(); db.refresh(w)
    return {"id": w.id, "name": w.name, "reliability": w.reliability,
            "document_name": w.document_name,
            "document_url": (f"/api/investigation/witnesses/document/{w.id}"
                              if w.document_path else None)}


@router.get("/witnesses/document/{witness_id}")
def download_witness_document(witness_id: int, db: Session = Depends(get_db)):
    w = db.get(m.Witness, witness_id)
    if not w or not w.document_path:
        raise HTTPException(404, "document not found")
    path = os.path.join(UPLOAD_ROOT, str(w.case_id), "witnesses", w.document_path)
    if not os.path.exists(path):
        raise HTTPException(404, "file missing")
    return FileResponse(path, filename=w.document_name or w.document_path)


# ── Victims ──────────────────────────────────────────────────────────

@router.get("/{case_id}/victims")
def list_case_victims(case_id: int, request: Request, db: Session = Depends(get_db)):
    ctx = get_ctx(request)
    links = (db.query(m.CaseVictim).filter(m.CaseVictim.case_id == case_id)
             .all())
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
    c = db.get(m.Case, case_id)
    if not c:
        raise HTTPException(404, "case not found")
    v = m.Victim(
        full_name=full_name.strip(),
        gender=gender.strip() or None,
        age=age or None,
        contact_number=contact_number.strip() or None,
        address=address.strip() or None,
        district=district.strip() or c.district,
        occupation=occupation.strip() or None,
        statement_summary=statement_summary.strip() or None,
    )
    db.add(v)
    db.flush()
    link = m.CaseVictim(case_id=case_id, victim_id=v.id)
    db.add(link)
    _log(db, case_id, "Victim recorded", "Victim", f"{ctx.name} recorded victim {full_name.strip()}.")
    db.commit()
    db.refresh(v)
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
    v = db.get(m.Victim, victim_id)
    if not v:
        raise HTTPException(404, "victim not found")
    link = (db.query(m.CaseVictim)
            .filter(m.CaseVictim.case_id == case_id, m.CaseVictim.victim_id == victim_id)
            .first())
    if not link:
        raise HTTPException(404, "victim not linked to this case")
    if full_name.strip():
        v.full_name = full_name.strip()
    if gender.strip():
        v.gender = gender.strip()
    if age:
        v.age = age
    if contact_number.strip():
        v.contact_number = contact_number.strip()
    if address.strip():
        v.address = address.strip()
    if occupation.strip():
        v.occupation = occupation.strip()
    if statement_summary.strip():
        v.statement_summary = statement_summary.strip()
    _log(db, case_id, "Victim updated", "Victim", f"{ctx.name} updated victim {v.full_name}.")
    db.commit()
    return {"ok": True}


@router.post("/{case_id}/victims/link/{victim_id}")
def link_existing_victim(case_id: int, victim_id: int, request: Request,
                         db: Session = Depends(get_db)):
    ctx = get_ctx(request)
    _require_investigate(ctx)
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
def _mock_summary(name: str, category: str) -> str:
    return (f"Auto-analysis: '{name}' filed under {category}. "
            "Key entities and dates extracted; flagged for investigator review.")


@router.get("/{case_id}/evidence")
def list_evidence(case_id: int, db: Session = Depends(get_db), category: str | None = None):
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
    c = db.get(m.Case, case_id)
    if not c:
        raise HTTPException(404, "case not found")
    case_dir = os.path.join(UPLOAD_ROOT, str(case_id))
    os.makedirs(case_dir, exist_ok=True)
    stored = f"{uuid.uuid4().hex}_{file.filename}"
    path = os.path.join(case_dir, stored)
    data = await file.read()
    with open(path, "wb") as fh:
        fh.write(data)
    doc = m.EvidenceDocument(case_id=case_id, category=category, filename=stored,
                             original_name=file.filename, mime=file.content_type or "application/octet-stream",
                             size=len(data), uploaded_by=ctx.name,
                             ai_summary=_mock_summary(file.filename, category),
                             remarks=remarks.strip() or None)
    db.add(doc)
    _log(db, case_id, "Evidence uploaded", "Evidence",
         f"{ctx.name} uploaded '{file.filename}' ({category}).")
    db.commit(); db.refresh(doc)
    return {"id": doc.id, "original_name": doc.original_name, "category": doc.category,
            "size": doc.size, "ai_summary": doc.ai_summary, "remarks": doc.remarks}


@router.get("/evidence/{doc_id}/download")
def download_evidence(doc_id: int, db: Session = Depends(get_db)):
    doc = db.get(m.EvidenceDocument, doc_id)
    if not doc:
        raise HTTPException(404, "not found")
    path = os.path.join(UPLOAD_ROOT, str(doc.case_id), doc.filename)
    if not os.path.exists(path):
        raise HTTPException(404, "file missing")
    return FileResponse(path, media_type=doc.mime, filename=doc.original_name)


@router.delete("/evidence/{doc_id}")
def delete_evidence(doc_id: int, request: Request, db: Session = Depends(get_db)):
    _require_investigate(get_ctx(request))
    doc = db.get(m.EvidenceDocument, doc_id)
    if doc:
        path = os.path.join(UPLOAD_ROOT, str(doc.case_id), doc.filename)
        if os.path.exists(path):
            os.remove(path)
        db.delete(doc); db.commit()
    return {"ok": True}


# ── Stage approvals ────────────────────────────────────────────────────
def _approval_json(a: m.StageApproval):
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
def _access_json(r: m.AccessRequest):
    return {"id": r.id, "case_id": r.case_id, "requested_by": r.requested_by,
            "requested_role": r.requested_role, "reason": r.reason,
            "status": r.status, "reviewed_by": r.reviewed_by,
            "created_at": r.created_at.isoformat()}


@router.post("/{case_id}/request-access")
def request_access(case_id: int, request: Request, db: Session = Depends(get_db),
                   requested_role: str = Form(""), reason: str = Form("")):
    ctx = get_ctx(request)
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
def _chat_msg(x: m.Message):
    return {"id": x.id, "role": x.role, "content": x.content, "language": x.language,
            "sql": x.sql_text, "intent": x.intent,
            "evidence": json.loads(x.evidence_json) if x.evidence_json else [],
            "grounding": json.loads(x.grounding_json) if x.grounding_json else {},
            "reasoning": json.loads(x.reasoning_json) if x.reasoning_json else [],
            "created_at": x.created_at.isoformat()}


def _get_or_create_case_conversation(db: Session, case: m.Case) -> m.Conversation:
    conv = (db.query(m.Conversation).filter(m.Conversation.case_id == case.id)
            .order_by(m.Conversation.created_at.desc()).first())
    if not conv:
        conv = m.Conversation(title=f"Case {case.fir_number} investigation",
                              case_id=case.id, language="en")
        db.add(conv)
        db.flush()
    return conv


@router.get("/{case_id}/chat")
def get_case_chat(case_id: int, db: Session = Depends(get_db)):
    c = db.get(m.Case, case_id)
    if not c:
        raise HTTPException(404, "case not found")
    conv = _get_or_create_case_conversation(db, c)
    db.commit()
    return {"conversation_id": conv.id, "case_id": case_id,
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

                # Save file to uploads directory
                chat_dir = os.path.join(UPLOAD_ROOT, str(case_id), "chat_uploads")
                os.makedirs(chat_dir, exist_ok=True)
                stored = f"{uuid.uuid4().hex}_{fname}"
                with open(os.path.join(chat_dir, stored), "wb") as fh:
                    fh.write(file_bytes)
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
    c = db.get(m.Case, case_id)
    if not c:
        raise HTTPException(404, "case not found")
    conv = _get_or_create_case_conversation(db, c)

    lang = language or None
    result = answer_question(db, combined, lang)

    # Append entity extraction results to answer
    if entities_found and any(entities_found.values()):
        ent_lines = ["\n\n**Entities extracted from uploaded document:**"]
        if entities_found["phone_numbers"]:
            ent_lines.append(f"- Phone numbers: {', '.join(entities_found['phone_numbers'])}")
        if entities_found["fir_references"]:
            ent_lines.append(f"- FIR references: {', '.join(entities_found['fir_references'])}")
        if entities_found["locations"]:
            ent_lines.append(f"- Locations: {', '.join(entities_found['locations'])}")
        if entities_found["crime_types"]:
            ent_lines.append(f"- Crime types: {', '.join(entities_found['crime_types'])}")
        if entities_found["aadhaar_numbers"]:
            ent_lines.append(f"- ID numbers detected: {len(entities_found['aadhaar_numbers'])}")
        result["answer"] += "\n".join(ent_lines)

    display_msg = message or f"[Uploaded: {', '.join(uploaded_files)}]"
    um = m.Message(conversation_id=conv.id, role="user", content=display_msg,
                   language=result["language"])
    am = m.Message(conversation_id=conv.id, role="assistant", content=result["answer"],
                   language=result["language"], sql_text=result["sql"],
                   evidence_json=json.dumps(result["evidence"]), intent=result["intent"],
                   grounding_json=json.dumps(result.get("grounding", {})),
                   reasoning_json=json.dumps(result.get("reasoning", [])))
    db.add_all([um, am])
    conv.updated_at = datetime.utcnow()
    _log(db, case_id, "AI chat message", "Chat", f"{ctx.name} asked the case assistant a question.")
    db.commit()

    return {"conversation_id": conv.id, "case_id": case_id,
            "answer": result["answer"], "sql": result["sql"],
            "evidence": result["evidence"], "intent": result["intent"],
            "language": result["language"], "provider": result["provider"],
            "grounding": result.get("grounding", {}),
            "reasoning": result.get("reasoning", []),
            "uploaded_files": uploaded_files,
            "entities": entities_found}
