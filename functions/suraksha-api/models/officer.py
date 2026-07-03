from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from .base import Base

class Officer(Base):
    __tablename__ = "officers"

    id = Column(Integer, primary_key=True, index=True)
    badge_number = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    rank = Column(String(50), nullable=False)  # DSP, ACP, Inspector, Sub-Inspector, Constable
    posting_station = Column(String(100), nullable=False) # Police Station Name
    contact_number = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
