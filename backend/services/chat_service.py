from typing import Any, Dict
from sqlalchemy.orm import Session
from backend.repositories.chat_repository import ChatRepository
from ai_engine.agents.chat_agent import ChatAgent

class ChatService:
    """
    Coordinates chat flows.
    Takes user input, calls AI Agent (AI Layer), and returns responses.
    """
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.chat_repo = ChatRepository(db_session)
        # Instantiate the AI Agent (AI Layer) passing the repository down
        self.ai_agent = ChatAgent(self.chat_repo)

    def process_query(self, session_id: str, message: str) -> Dict[str, Any]:
        # Service Layer calls AI Layer
        ai_response = self.ai_agent.process_chat_message(session_id, message)
        return ai_response
