from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from .base import Base

class Victim(Base):
    __tablename__ = "victims"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    gender = Column(String(10), nullable=True)
    age = Column(Integer, nullable=True)
    contact_number = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    statement_summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
