# TCGX2 — Trading Card PSA Grading Analyzer

Web application that analyzes trading card images using computer vision and AI, then recommends whether a card is worth submitting for PSA grading.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18 + Vite + nginx |
| Backend | FastAPI (Python 3.12) |
| Image Processing | OpenCV + Pillow |
| Workflow / AI | n8n + Claude (Anthropic) |
| Database | SQLite (via SQLAlchemy) |
| Deployment | Docker Compose |

---

## Architecture

```
Browser (localhost:5173)
       │
       ▼
   nginx (frontend)
       │  proxy /analyze, /agents, /analysis, /cards, /uploads
       ▼
FastAPI backend (:8000)
       │
       ├── POST /analyze → validates image → calls n8n webhook
       │
       └── GET/POST /agents/*  ← called by n8n HTTP nodes
           ├── /agents/crop        (detect & crop card area)
           ├── /agents/centering   (border symmetry score)
           ├── /agents/corner      (corner sharpness score)
           └── /agents/edge        (edge straightness score)

n8n workflow (:5678)
       ├── Receives webhook from /analyze
       ├── Calls each agent endpoint in sequence
       ├── Calls Claude AI (surface analysis + price lookup)
       ├── Calculates PSA grade
       └── Saves result → POST /analysis/save → SQLite
```

---

## Quick Start (Docker)

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### 1. Clone and start

```bash
git clone https://github.com/Tktarit/TCGX2.git
cd TCGX2

mkdir -p backend/uploads

docker compose up --build -d
```

### 2. Import n8n workflow

1. Open n8n at **http://localhost:5678**
2. Complete the initial n8n setup (create account)
3. Go to **Workflows** → **Import from file**
4. Select `n8n-workflows/n8n-workflows.json`
5. Set up Anthropic credential:
   - Go to **Credentials** → **Add credential** → **Anthropic**
   - Enter your [Anthropic API key](https://console.anthropic.com/)
   - Assign this credential to both `Anthropic Chat Model` nodes in the workflow
6. **Activate** the workflow (toggle at top right)

### 3. Open the app

**http://localhost:5173**

---

## Local Development (without Docker)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### n8n (local)

```bash
npx n8n
# Open http://localhost:5678, import workflow, set credentials
```

> **Note:** When running locally, n8n workflow uses `http://127.0.0.1:8000` for agent URLs.
> In Docker, it uses `http://backend:8000`. The workflow in this repo is configured for Docker.
> Change URLs in the workflow nodes if running locally.

API docs: **http://localhost:8000/docs**

---

## Project Structure

```
TCGX2/
├── docker-compose.yml
├── n8n-workflows/
│   └── n8n-workflows.json        # Import this into n8n
│
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf                # Reverse proxy config
│   └── src/
│       ├── components/
│       │   ├── CardUploader.jsx  # Drag-and-drop image upload
│       │   ├── AnalysisResult.jsx
│       │   ├── GradeRecommendation.jsx
│       │   ├── PriceInfo.jsx
│       │   └── CardHistory.jsx
│       ├── pages/
│       │   ├── Home.jsx          # Upload + analyze page
│       │   └── History.jsx       # Analysis history
│       └── services/api.js
│
└── backend/
    ├── Dockerfile
    ├── main.py                   # FastAPI app entry point
    ├── requirements.txt
    └── app/
        ├── config.py             # Settings (pydantic-settings)
        ├── database.py           # SQLAlchemy setup
        ├── models/card.py        # ORM: Card, AnalysisResult
        ├── schemas/card.py       # Pydantic schemas
        ├── routers/
        │   ├── agents.py         # /agents/* endpoints (called by n8n)
        │   ├── analysis.py       # /analysis/* endpoints
        │   └── cards.py          # /cards/* endpoints
        └── services/
            ├── image_processor.py  # crop_card(), normalize_image()
            ├── centering_agent.py  # Border symmetry → score 0–10
            ├── corner_agent.py     # Corner sharpness → score 0–10
            └── edge_agent.py       # Edge straightness → score 0–10
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/analyze` | Upload image → validate → trigger n8n workflow |
| POST | `/agents/crop` | Detect and crop card area from image |
| POST | `/agents/centering` | Measure border centering (score 0–10) |
| POST | `/agents/corner` | Measure corner sharpness (score 0–10) |
| POST | `/agents/edge` | Measure edge straightness (score 0–10) |
| POST | `/analysis/save` | Save analysis result to database |
| GET | `/analysis/history` | Get paginated analysis history |
| DELETE | `/analysis/{id}` | Delete a card and its analysis |
| GET | `/cards/{id}` | Get card details |
| GET | `/health` | Health check |

---

## Grading Logic (n8n workflow)

The grade is calculated from four CV scores (0–10 each):

| Category | Weight |
|----------|--------|
| Centering | 20% |
| Corners | 35% |
| Edges | 25% |
| Surface (Claude AI) | 20% |

| PSA Grade | Overall Score | Submit? |
|-----------|--------------|---------|
| 10 (Gem Mint) | ≥ 9.5 | Yes |
| 9 (Mint) | ≥ 8.5 | Yes |
| 8 (NM-MT) | ≥ 7.5 | Maybe |
| 7 and below | < 7.5 | No |

---

## Running Tests

```bash
cd backend
pip install pytest
pytest tests/ -v
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./tcgx2.db` | SQLAlchemy connection string |
| `UPLOAD_DIR` | `uploads` | Directory for uploaded images |
| `N8N_WEBHOOK_URL` | `http://n8n:5678/webhook/grade-card` | n8n webhook URL |
| `ALLOWED_EXTENSIONS` | `jpg,jpeg,png,webp,avif,heic,heif` | Accepted image formats |
