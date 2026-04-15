from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database import Base


class Card(Base):
    __tablename__ = "cards"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    analysis = relationship("AnalysisResult", back_populates="card", uselist=False)


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=False, unique=True)

    # Individual defect scores (0–100, higher = better condition)
    corner_score = Column(Float, nullable=False)
    edge_score = Column(Float, nullable=False)
    surface_score = Column(Float, nullable=False)
    centering_score = Column(Float, nullable=False)

    # Aggregated
    overall_score = Column(Float, nullable=False)
    estimated_psa_grade = Column(Integer, nullable=False)  # 1–10
    recommend_submit = Column(Boolean, nullable=False)
    recommendation_reason = Column(Text, nullable=False)

    # Card identity & market price (populated by AI price lookup)
    card_name = Column(String, nullable=True)
    card_set = Column(String, nullable=True)
    card_number = Column(String, nullable=True)
    price_low = Column(Float, nullable=True)
    price_mid = Column(Float, nullable=True)
    price_high = Column(Float, nullable=True)
    price_currency = Column(String, nullable=True)

    analyzed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    card = relationship("Card", back_populates="analysis")
