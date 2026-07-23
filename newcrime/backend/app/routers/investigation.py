"""Phase 1 — 'Work a Case' investigation workflow.

Stages, notebook (notes), evidence/document upload, witnesses, and a
system-generated timeline. Extends the existing case/investigation records
rather than duplicating them.
"""
import os
import uuid
from datetime import datetime

from fastapi import (APIRouter, Depends, HTTPException, Request, UploadFile,
                     File, Form)
from fastapi.responses import FileResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_ctx
from .. import models as m

router = APIRouter(prefix="/api/investigation", tags=["investigation"])

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
             "created_at": w.created_at.isoformat()} for w in rows]


@router.post("/{case_id}/witnesses")
def add_witness(case_id: int, request: Request, db: Session = Depends(get_db),
                name: str = Form(...), contact: str = Form(""),
                statement: str = Form(""), reliability: str = Form("Medium")):
    ctx = get_ctx(request)
    _require_investigate(ctx)
    w = m.Witness(case_id=case_id, name=name.strip(), contact=contact.strip(),
                  statement=statement.strip(), reliability=reliability)
    db.add(w)
    _log(db, case_id, "Witness recorded", "Statement", f"{ctx.name} recorded witness {name}.")
    db.commit(); db.refresh(w)
    return {"id": w.id, "name": w.name, "reliability": w.reliability}


# ── Evidence / documents ──────────────────────────────────────────────
def _mock_summary(name: str, category: str) -> str:
    return (f"AI summary (auto-generated): '{name}' filed under {category}. "
            "Key entities and dates extracted; flagged for investigator review. "
            "[Wire a real OCR/LLM pipeline to replace this placeholder.]")


@router.get("/{case_id}/evidence")
def list_evidence(case_id: int, db: Session = Depends(get_db), category: str | None = None):
    q = db.query(m.EvidenceDocument).filter(m.EvidenceDocument.case_id == case_id)
    if category:
        q = q.filter(m.EvidenceDocument.category == category)
    rows = q.order_by(m.EvidenceDocument.created_at.desc()).all()
    return [{"id": e.id, "category": e.category, "original_name": e.original_name,
             "mime": e.mime, "size": e.size, "uploaded_by": e.uploaded_by,
             "ai_summary": e.ai_summary, "created_at": e.created_at.isoformat()} for e in rows]


@router.post("/{case_id}/evidence")
async def upload_evidence(case_id: int, request: Request, db: Session = Depends(get_db),
                          category: str = Form("Evidence"), file: UploadFile = File(...)):
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
                             ai_summary=_mock_summary(file.filename, category))
    db.add(doc)
    _log(db, case_id, "Evidence uploaded", "Evidence",
         f"{ctx.name} uploaded '{file.filename}' ({category}).")
    db.commit(); db.refresh(doc)
    return {"id": doc.id, "original_name": doc.original_name, "category": doc.category,
            "size": doc.size, "ai_summary": doc.ai_summary}


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
