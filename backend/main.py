from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
import uuid
import json
import httpx

from app.database import init_db
from app.config import settings
from app.routers import cards, analysis, agents
from app.services.image_processor import crop_card

N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/grade-card")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    yield


app = FastAPI(
    title="TCGX2 — Card Grading Analyzer",
    description="Analyze trading card images and get PSA grading recommendations",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

app.include_router(cards.router, prefix="/cards", tags=["cards"])
app.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
app.include_router(agents.router, prefix="/agents", tags=["agents"])


@app.get("/health", tags=["system"])
def health_check():
    return {"status": "ok"}


@app.post("/analyze", tags=["system"])
async def analyze(
    file: UploadFile = File(...),
    card_name_hint: str = Form(""),
    card_set_hint: str = Form(""),
):
    ext = (file.filename or "img").rsplit(".", 1)[-1].lower()
    if ext not in settings.allowed_extensions_set:
        raise HTTPException(
            status_code=400,
            detail=f"ไม่รองรับไฟล์ .{ext} — กรุณาใช้ไฟล์ {settings.ALLOWED_EXTENSIONS}",
        )

    unique_name = f"{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_name)

    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    # Pre-check: verify the image contains a trading card before calling n8n
    try:
        crop_card(file_path)
    except ValueError as e:
        os.unlink(file_path)
        return {"is_card": False, "reason": str(e)}

    # Forward image + metadata to n8n webhook (n8n handles DB save)
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                N8N_WEBHOOK_URL,
                files={"file": (file.filename, contents, file.content_type)},
                data={
                    "saved_path": file_path,
                    "unique_filename": unique_name,
                    "original_filename": file.filename or "",
                    "card_name_hint": card_name_hint,
                    "card_set_hint": card_set_hint,
                },
            )
            response.raise_for_status()
            body = response.text
            if not body.strip():
                os.unlink(file_path)
                raise HTTPException(
                    status_code=502,
                    detail="n8n returned empty response — check n8n execution logs for workflow errors",
                )
            try:
                n8n_data = json.loads(body)
            except json.JSONDecodeError:
                os.unlink(file_path)
                raise HTTPException(
                    status_code=502,
                    detail=f"n8n returned invalid JSON: {body[:200]}",
                )
    except httpx.TimeoutException:
        os.unlink(file_path)
        raise HTTPException(status_code=504, detail="n8n webhook timed out (>30s) — workflow may still be running")
    except httpx.HTTPStatusError as e:
        os.unlink(file_path)
        raise HTTPException(status_code=502, detail=f"n8n returned {e.response.status_code}: {e.response.text}")
    except httpx.RequestError as e:
        os.unlink(file_path)
        raise HTTPException(status_code=502, detail=f"Cannot reach n8n: {e}")

    return n8n_data
