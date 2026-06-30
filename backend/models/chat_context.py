from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from .base import Base

class ChatContext(Base):
    __tablename__ = "chat_contexts"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    user_id = Column(Integer, index=True, nullable=False) # References users.id
    history_json = Column(Text, nullable=True) # Serialized chat messages list
    metadata_json = Column(Text, nullable=True) # Serialized state/tokens/filters
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
