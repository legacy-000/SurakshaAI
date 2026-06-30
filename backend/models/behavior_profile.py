from sqlalchemy import Column, Integer, Text, Float, DateTime
from sqlalchemy.sql import func
from .base import Base

class BehaviorProfile(Base):
    __tablename__ = "behavior_profiles"

    id = Column(Integer, primary_key=True, index=True)
    accused_id = Column(Integer, index=True, unique=True, nullable=False) # References accused.id
    risk_score = Column(Float, default=0.0) # 0.0 to 100.0 risk coefficient
    behavioral_traits = Column(Text, nullable=True) # JSON or tags representing MO behavior
    propensity_tags = Column(Text, nullable=True) # AI profiling labels (e.g. "repeat-offender")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
