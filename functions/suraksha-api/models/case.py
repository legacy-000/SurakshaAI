from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from .base import Base

class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    fir_number = Column(String(50), unique=True, index=True, nullable=False) # First Information Report Number
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(30), default="Open")  # Open, Investigating, Closed, ChargeSheeted
    crime_type = Column(String(50), index=True, nullable=False)
    location_name = Column(String(255), nullable=True)
    occurrence_date = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
