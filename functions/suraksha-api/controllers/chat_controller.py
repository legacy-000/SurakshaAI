from sqlalchemy.orm import Session
from services.chat_service import ChatService
from schemas.response import APIResponse

class ChatController:
    """
    Controller Layer: Translates network requests, coordinates with ChatService,
    and structures output according to the global APIResponse schema.
    """
    def __init__(self, db: Session):
        self.chat_service = ChatService(db)

    def handle_message(self, session_id: str, message: str) -> APIResponse:
        # Controller Layer calls Service Layer
        data = self.chat_service.process_query(session_id, message)
        
        return APIResponse(
            status="Project Initialized",
            message="Chat request handled successfully by Controller-Service-AI-Repository flow",
            data=data
        )
