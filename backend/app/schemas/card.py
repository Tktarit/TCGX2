from pydantic import BaseModel
from datetime import datetime


class AnalysisResultSchema(BaseModel):
    id: int
    card_id: int
    card_filename: str | None = None
    corner_score: float
    edge_score: float
    surface_score: float
    centering_score: float
    overall_score: float
    estimated_psa_grade: int
    recommend_submit: bool
    recommendation_reason: str
    card_name: str | None = None
    card_set: str | None = None
    card_number: str | None = None
    price_low: float | None = None
    price_mid: float | None = None
    price_high: float | None = None
    price_currency: str | None = None
    analyzed_at: datetime

    model_config = {"from_attributes": True}


