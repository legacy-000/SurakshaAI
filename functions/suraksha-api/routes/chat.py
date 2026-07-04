from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from configuration.database import get_db
from controllers.chat_controller import ChatController
from schemas.response import APIResponse
from schemas.requests import ChatQueryRequest

router = APIRouter(prefix="/chat", tags=["AI Chat"])

@router.post("/query", response_model=APIResponse)
def query_chat(body: ChatQueryRequest, db: Session = Depends(get_db)) -> APIResponse:
    controller = ChatController(db)
    return controller.handle_message(body.session_id, body.message)
