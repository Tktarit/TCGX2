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
    analyzed_at: datetime

    model_config = {"from_attributes": True}


class CardSchema(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_path: str
    uploaded_at: datetime
    analysis: AnalysisResultSchema | None = None

    model_config = {"from_attributes": True}


class CardUploadResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    uploaded_at: datetime

    model_config = {"from_attributes": True}
