from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from .base import Base

class Accused(Base):
    __tablename__ = "accused"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    aliases = Column(String(255), nullable=True)
    gender = Column(String(10), nullable=True)
    age = Column(Integer, nullable=True)
    address = Column(Text, nullable=True)
    phone_number = Column(String(20), nullable=True)
    previous_convictions = Column(Text, nullable=True)
    status = Column(String(50), default="Suspect")  # Suspect, Apprehended, Absconding, Released
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
