# TCGX2 — Trading Card PSA Grading Analyzer

Web application that analyzes trading card images and recommends whether a card is worth submitting for PSA grading.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + Vite |
| Backend | FastAPI (Python) |
| Image Processing | OpenCV + Pillow |
| Database | SQLite (via SQLAlchemy) |

---

## Project Structure

```
TCGX2/
├── README.md
├── docker-compose.yml
│
├── frontend/                        # React app (Vite)
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx                 # Entry point
│       ├── App.jsx                  # Root component + routing
│       ├── components/
│       │   ├── CardUploader.jsx     # Drag-and-drop image uploader
│       │   ├── AnalysisResult.jsx   # Display defect scores per category
│       │   ├── GradeRecommendation.jsx  # PSA grade prediction badge
│       │   └── CardHistory.jsx      # List of previously analyzed cards
│       ├── pages/
│       │   ├── Home.jsx             # Upload + analyze page
│       │   └── History.jsx          # Analysis history page
│       ├── services/
│       │   └── api.js               # Axios wrapper for backend API
│       └── styles/
│           └── index.css
│
└── backend/                         # FastAPI app
    ├── main.py                      # App entrypoint, CORS, router registration
    ├── requirements.txt
    ├── .env.example
    ├── uploads/                     # Uploaded card images (gitignored)
    └── app/
        ├── config.py                # Settings via pydantic-settings
        ├── database.py              # SQLAlchemy engine + session
        ├── models/
        │   └── card.py              # ORM models: Card, AnalysisResult
        ├── schemas/
        │   └── card.py              # Pydantic request/response schemas
        ├── routers/
        │   ├── cards.py             # POST /cards/upload, GET /cards/{id}
        │   └── analysis.py          # POST /analysis/{card_id}, GET /analysis/history
        └── services/
            ├── image_processor.py   # OpenCV pipeline: corners, edges, surface
            └── grading_analyzer.py  # Scoring logic → PSA grade recommendation
```

---

## Analysis Pipeline

```
Upload Image
     │
     ▼
image_processor.py  (OpenCV)
  ├── Corner wear detection
  ├── Edge/border analysis
  ├── Surface scratch detection
  └── Centering measurement
     │
     ▼
grading_analyzer.py
  ├── Weighted defect scoring
  ├── PSA grade estimate (1–10)
  └── Submit recommendation + reason
     │
     ▼
SQLite (store card + result)
     │
     ▼
API Response → React UI
```

### PSA Grade Thresholds

| Grade | Condition | Recommend Submit |
|-------|-----------|-----------------|
| 10 (Gem Mint) | Score ≥ 90 | Yes — high ROI |
| 9 (Mint) | Score 80–89 | Yes |
| 8 (NM-MT) | Score 70–79 | Maybe |
| 7 and below | Score < 70 | No |

---

## Quick Start

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### With Docker Compose
```bash
docker-compose up --build
```

API docs available at: `http://localhost:8000/docs`

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/cards/upload` | Upload card image |
| GET | `/cards/{id}` | Get card details |
| POST | `/analysis/{card_id}` | Run analysis on uploaded card |
| GET | `/analysis/history` | Get all past analyses |
| GET | `/health` | Health check |
