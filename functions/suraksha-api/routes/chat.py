from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from configuration.database import get_db
from controllers.chat_controller import ChatController
from schemas.response import APIResponse

router = APIRouter(prefix="/chat", tags=["AI Chat"])

@router.post("/query", response_model=APIResponse)
def query_chat(session_id: str, message: str, db: Session = Depends(get_db)) -> APIResponse:
    # Controller Layer is invoked
    controller = ChatController(db)
    return controller.handle_message(session_id, message)
