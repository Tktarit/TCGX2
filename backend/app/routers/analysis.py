import logging
import os
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.card import Card, AnalysisResult
from app.schemas.card import AnalysisResultSchema
from app.services.image_processor import analyze_card
from app.services.grading_analyzer import compute_grade

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


@router.post("/{card_id}", response_model=AnalysisResultSchema, status_code=201)
def run_analysis(card_id: int, db: Session = Depends(get_db)):
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    if card.analysis:
        raise HTTPException(
            status_code=409,
            detail="Analysis already exists for this card.",
        )

    try:
        image_data = analyze_card(card.file_path)
    except Exception as e:
        logger.exception("Image processing failed for card %s", card_id)
        raise HTTPException(
            status_code=422,
            detail=f"Image processing failed: {type(e).__name__}: {e}",
        )

    try:
        result = compute_grade(image_data)
    except Exception as e:
        logger.exception("Grading computation failed for card %s", card_id)
        raise HTTPException(
            status_code=500,
            detail=f"Grading computation failed: {type(e).__name__}: {e}",
        )

    db_result = AnalysisResult(
        card_id=card.id,
        corner_score=image_data.corner_score,
        edge_score=image_data.edge_score,
        surface_score=image_data.surface_score,
        centering_score=image_data.centering_score,
        overall_score=result.overall_score,
        estimated_psa_grade=result.estimated_psa_grade,
        recommend_submit=result.recommend_submit,
        recommendation_reason=result.recommendation_reason,
    )
    db.add(db_result)
    db.commit()
    db.refresh(db_result)

    return db_result
