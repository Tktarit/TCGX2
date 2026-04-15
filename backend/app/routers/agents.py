"""
Individual agent endpoints — designed to be called by n8n HTTP Request nodes.

All endpoints accept { "file_path": "uploads/xxx.jpg" } in the request body.
n8n receives saved_path from the initial /analyze webhook call and passes it
to each of these endpoints sequentially (or in parallel branches).
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import uuid
import os
import base64
import cv2

from app.services.image_processor import crop_card, normalize_image, _imread
from app.services.centering_agent import CenteringAgent
from app.services.corner_agent import CornerAgent
from app.services.edge_agent import EdgeAgent
from app.config import settings

router = APIRouter()


class FilePathRequest(BaseModel):
    file_path: str


def _load(file_path: str):
    img = _imread(file_path)
    if img is None:
        raise HTTPException(status_code=422, detail=f"Cannot read image: {file_path}")
    return img


# ── Crop ─────────────────────────────────────────────────────────────────────

@router.post("/crop")
def agent_crop(req: FilePathRequest):
    """
    Detect and crop the card area.
    Saves the cropped image to uploads/ and returns cropped_path
    so downstream agents can use it as their file_path.
    """
    img = _load(req.file_path)
    try:
        cropped = crop_card(req.file_path)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Save full-res cropped image for downstream agents
    cropped_name = f"cropped_{uuid.uuid4().hex}.png"
    cropped_path = os.path.join(settings.UPLOAD_DIR, cropped_name)
    cv2.imwrite(cropped_path, cropped)

    # Resize to max 256px on longest side before base64 — reduces AI token cost
    MAX_PX = 256
    ch_full, cw_full = cropped.shape[:2]
    scale = min(MAX_PX / cw_full, MAX_PX / ch_full, 1.0)
    if scale < 1.0:
        small = cv2.resize(cropped, (int(cw_full * scale), int(ch_full * scale)),
                           interpolation=cv2.INTER_AREA)
    else:
        small = cropped

    _, buf = cv2.imencode(".jpg", small, [cv2.IMWRITE_JPEG_QUALITY, 70])
    cropped_image = "data:image/jpeg;base64," + base64.b64encode(buf).decode()

    oh, ow = img.shape[:2]
    ch, cw = cropped.shape[:2]
    return {
        "cropped_path":  cropped_path,   # ← pass this as file_path to next agents
        "cropped_image": cropped_image,  # ← base64 for frontend display
        "original_w":    ow,
        "original_h":    oh,
        "cropped_w":     cw,
        "cropped_h":     ch,
    }


# ── Centering ────────────────────────────────────────────────────────────────

@router.post("/centering")
def agent_centering(req: FilePathRequest):
    """Measure border symmetry. Returns centering score 0–10."""
    img = _load(req.file_path)
    img = normalize_image(img)
    score = CenteringAgent().analyze(img)
    return {"centering_score": score}


# ── Corner ───────────────────────────────────────────────────────────────────

@router.post("/corner")
def agent_corner(req: FilePathRequest):
    """Measure corner sharpness. Returns per-corner scores and average 0–10."""
    img = _load(req.file_path)
    img = normalize_image(img)
    result = CornerAgent().analyze(img)
    return {
        "corner_scores": result["corner_scores"],   # [tl, tr, bl, br]
        "corner_score":  result["score"],
    }


# ── Edge ─────────────────────────────────────────────────────────────────────

@router.post("/edge")
def agent_edge(req: FilePathRequest):
    """Measure edge straightness. Returns per-edge scores and average 0–10."""
    img = _load(req.file_path)
    img = normalize_image(img)
    result = EdgeAgent().analyze(img)
    return {
        "edge_scores": result["edge_scores"],   # [top, bottom, left, right]
        "edge_score":  result["score"],
    }


