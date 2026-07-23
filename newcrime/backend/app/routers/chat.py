"""Conversational AI endpoints: sessions, messages, NLQ."""
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import ChatRequest
from .. import models as m
from ..services.nlq import answer_question

router = APIRouter(prefix="/api/chat", tags=["chat"])


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
def send_message(req: ChatRequest, db: Session = Depends(get_db)):
    if not req.message.strip():
        raise HTTPException(400, "empty message")

    # conversation
    if req.conversation_id:
        conv = db.get(m.Conversation, req.conversation_id)
        if not conv:
            raise HTTPException(404, "conversation not found")
    else:
        conv = m.Conversation(title=req.message[:60], language=req.language or "en")
        db.add(conv)
        db.flush()

    lang = None if (req.language in (None, "auto")) else req.language
    result = answer_question(db, req.message, lang)

    # persist user + assistant messages
    um = m.Message(conversation_id=conv.id, role="user", content=req.message,
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
            "reasoning": result.get("reasoning", []), "message_id": am.id}


def _msg(x: m.Message):
    return {"id": x.id, "role": x.role, "content": x.content, "language": x.language,
            "sql": x.sql_text, "intent": x.intent,
            "evidence": json.loads(x.evidence_json) if x.evidence_json else [],
            "grounding": json.loads(x.grounding_json) if x.grounding_json else {},
            "reasoning": json.loads(x.reasoning_json) if x.reasoning_json else [],
            "created_at": x.created_at.isoformat()}
