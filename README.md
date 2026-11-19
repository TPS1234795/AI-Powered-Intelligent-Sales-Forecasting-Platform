# SalesGenie AI – Milestone 1: Lead Management & Intelligence Engine

Stack: React (Vite) · FastAPI · SQLAlchemy (SQLite by default, PostgreSQL optional) · optional Gemini.

## Run the backend
```bash
cd backend
python -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                   # optionally add GEMINI_API_KEY
uvicorn main:app --reload --port 8000
```
API docs: http://localhost:8000/docs (4 sample prospects are seeded on first run).

## Run the frontend
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173 (requests to `/api` are proxied to port 8000).

## Features
- Create, edit, delete, search and filter prospects; move them through sales stages
- CSV import (see `backend/sample_leads.csv`)
- "Analyse prospect": qualification score, conversion probability, scoring factors,
  business needs, opportunities and industry analysis (Gemini if a key is set, rules engine otherwise)
