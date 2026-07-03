from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from .base import Base

class Investigation(Base):
    __tablename__ = "investigations"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, index=True, nullable=False) # References cases.id
    assigned_officer_id = Column(Integer, index=True, nullable=False) # References officers.id
    summary = Column(Text, nullable=True)
    leads_details = Column(Text, nullable=True)
    status = Column(String(50), default="Active") # Active, Suspended, Completed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
