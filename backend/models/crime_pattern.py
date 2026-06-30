from sqlalchemy import Column, Integer, String, Text, Float, DateTime
from sqlalchemy.sql import func
from .base import Base

class CrimePattern(Base):
    __tablename__ = "crime_patterns"

    id = Column(Integer, primary_key=True, index=True)
    pattern_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    crime_type = Column(String(50), index=True, nullable=False)
    hotspot_radius_meters = Column(Float, default=500.0)
    temporal_signature = Column(String(100), nullable=True) # e.g. "Weekends 22:00 - 02:00"
    modus_operandi_tags = Column(String(255), nullable=True) # Comma-separated MO traits
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
