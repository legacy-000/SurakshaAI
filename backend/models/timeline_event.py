from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from .base import Base

class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, index=True, nullable=False) # References cases.id
    event_title = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    event_timestamp = Column(DateTime(timezone=True), nullable=False)
    event_type = Column(String(50), nullable=True) # Arrest, FIR, EvidenceGathered, Interview
    created_at = Column(DateTime(timezone=True), server_default=func.now())
