import logging
import os
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.card import Card, AnalysisResult
from app.schemas.card import AnalysisResultSchema

logger = logging.getLogger(__name__)
router = APIRouter()


class SaveRequest(BaseModel):
    unique_filename: str
    original_filename: str
    file_path: str
    cropped_path: str | None = None
    corner_score: float = 0.0
    edge_score: float = 0.0
    surface_score: float = 0.0
    centering_score: float = 0.0
    overall_score: float = 0.0
    estimated_psa_grade: int = 1
    recommend_submit: bool = False
    recommendation_reason: str = ""
    card_name: str | None = None
    card_set: str | None = None
    card_number: str | None = None
    price_low: float | None = None
    price_mid: float | None = None
    price_high: float | None = None
    price_currency: str | None = None


@router.post("/save", response_model=AnalysisResultSchema, status_code=201)
def save_analysis(req: SaveRequest, db: Session = Depends(get_db)):
    card = Card(
        filename=req.unique_filename,
        original_filename=req.original_filename,
        file_path=req.file_path,
    )
    db.add(card)
    db.flush()

    db_result = AnalysisResult(
        card_id=card.id,
        corner_score=req.corner_score,
        edge_score=req.edge_score,
        surface_score=req.surface_score,
        centering_score=req.centering_score,
        overall_score=req.overall_score,
        estimated_psa_grade=req.estimated_psa_grade,
        recommend_submit=req.recommend_submit,
        recommendation_reason=req.recommendation_reason,
        card_name=req.card_name,
        card_set=req.card_set,
        card_number=req.card_number,
        price_low=req.price_low,
        price_mid=req.price_mid,
        price_high=req.price_high,
        price_currency=req.price_currency,
    )
    db.add(db_result)
    db.commit()
    db.refresh(db_result)

    if req.cropped_path and os.path.isfile(req.cropped_path):
        os.remove(req.cropped_path)

    return db_result


# IMPORTANT: literal routes must come before parameterized routes
@router.get("/history", response_model=list[AnalysisResultSchema])
def get_history(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    rows = (
        db.query(AnalysisResult, Card.filename)
        .join(Card, Card.id == AnalysisResult.card_id)
        .order_by(AnalysisResult.analyzed_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    results = []
    for analysis, filename in rows:
        analysis.card_filename = filename
        results.append(analysis)
    return results


@router.delete("/{card_id}", status_code=204)
def delete_analysis(card_id: int, db: Session = Depends(get_db)):
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    db.delete(card)
    db.commit()


