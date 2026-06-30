from sqlalchemy import Column, Integer, String, Text, Float, DateTime
from sqlalchemy.sql import func
from .base import Base

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    target_area = Column(String(100), index=True, nullable=False) # Police Station or Beat Name
    crime_type = Column(String(50), nullable=False)
    probability = Column(Float, nullable=False) # 0.0 to 1.0
    forecast_window_start = Column(DateTime(timezone=True), nullable=False)
    forecast_window_end = Column(DateTime(timezone=True), nullable=False)
    contributing_factors = Column(Text, nullable=True) # JSON or text explanations
    created_at = Column(DateTime(timezone=True), server_default=func.now())
