from sqlalchemy.orm import Session
from models.chat_context import ChatContext
from .base import BaseRepository

class ChatRepository(BaseRepository[ChatContext]):
    """
    Repository for handling database actions related to ChatContext sessions.
    """
    def __init__(self, db: Session):
        super().__init__(ChatContext, db)

    def get_by_session_id(self, session_id: str) -> ChatContext | None:
        return self.db.query(self.model).filter(self.model.session_id == session_id).first()
