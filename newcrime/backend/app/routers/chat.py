"""Conversational AI endpoints: sessions, messages, NLQ."""
import json
import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import ChatRequest
from .. import models as m
from ..services.nlq import answer_question
from ..services.fileparse import extract_text, extract_entities, is_supported

router = APIRouter(prefix="/api/chat", tags=["chat"])

UPLOAD_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
os.makedirs(UPLOAD_ROOT, exist_ok=True)


@router.get("/conversations")
def list_conversations(db: Session = Depends(get_db)):
    convs = db.query(m.Conversation).order_by(m.Conversation.updated_at.desc()).all()
    return [{"id": c.id, "title": c.title or "New conversation",
             "language": c.language, "updated_at": c.updated_at.isoformat(),
             "message_count": len(c.messages)} for c in convs]


@router.get("/conversations/{conv_id}")
def get_conversation(conv_id: int, db: Session = Depends(get_db)):
    c = db.get(m.Conversation, conv_id)
    if not c:
        raise HTTPException(404, "conversation not found")
    return {"id": c.id, "title": c.title, "language": c.language,
            "messages": [_msg(x) for x in c.messages]}


@router.delete("/conversations/{conv_id}")
def delete_conversation(conv_id: int, db: Session = Depends(get_db)):
    c = db.get(m.Conversation, conv_id)
    if c:
        db.delete(c)
        db.commit()
    return {"ok": True}


@router.post("/message")
async def send_message(request: Request, db: Session = Depends(get_db)):
    content_type = request.headers.get("content-type", "")
    file_context = ""
    entities_found: dict | None = None
    uploaded_files: list[str] = []

    if "multipart/form-data" in content_type:
        form = await request.form()
        message = (form.get("message") or "").strip()
        language = form.get("language", "") or None
        conv_id_str = form.get("conversation_id", "")
        conv_id = int(conv_id_str) if conv_id_str and conv_id_str.isdigit() else None

        for key in form:
            upload = form[key]
            if not hasattr(upload, "filename") or not upload.filename:
                continue
            if key in ("message", "language", "conversation_id"):
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

                chat_dir = os.path.join(UPLOAD_ROOT, "global_chat")
                os.makedirs(chat_dir, exist_ok=True)
                stored = f"{uuid.uuid4().hex}_{fname}"
                with open(os.path.join(chat_dir, stored), "wb") as fh:
                    fh.write(file_bytes)
            else:
                file_context += f"\n[Unsupported file type: {fname}]\n"
    else:
        body = await request.json()
        message = body.get("message", "").strip()
        language = body.get("language") or None
        conv_id = body.get("conversation_id")

    combined = message
    if file_context:
        combined = f"{message}\n\nUploaded document content:{file_context}" if message else f"Analyse the uploaded document:{file_context}"
    if not combined.strip():
        raise HTTPException(400, "empty message")

    if conv_id:
        conv = db.get(m.Conversation, conv_id)
        if not conv:
            raise HTTPException(404, "conversation not found")
    else:
        title = message[:60] if message else f"File: {uploaded_files[0]}" if uploaded_files else "New conversation"
        conv = m.Conversation(title=title, language=language or "en")
        db.add(conv)
        db.flush()

    lang = None if language in (None, "auto") else language
    result = answer_question(db, combined, lang)

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
    from datetime import datetime
    conv.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(am)

    return {"conversation_id": conv.id, "intent": result["intent"],
            "answer": result["answer"], "sql": result["sql"],
            "evidence": result["evidence"], "data": result["data"],
            "language": result["language"], "provider": result["provider"],
            "grounding": result.get("grounding", {}),
            "reasoning": result.get("reasoning", []), "message_id": am.id,
            "uploaded_files": uploaded_files, "entities": entities_found}


def _msg(x: m.Message):
    return {"id": x.id, "role": x.role, "content": x.content, "language": x.language,
            "sql": x.sql_text, "intent": x.intent,
            "evidence": json.loads(x.evidence_json) if x.evidence_json else [],
            "grounding": json.loads(x.grounding_json) if x.grounding_json else {},
            "reasoning": json.loads(x.reasoning_json) if x.reasoning_json else [],
            "created_at": x.created_at.isoformat()}
