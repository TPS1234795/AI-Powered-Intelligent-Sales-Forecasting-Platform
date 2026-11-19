import csv
import io
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

import models
import schemas
from database import Base, SessionLocal, engine, get_db
from intelligence import generate_insight, score_lead

SEED = [
    dict(company_name="TechCorp Solutions", industry="Enterprise Software", contact_name="Sarah Johnson",
         contact_title="CTO", email="sarah.johnson@techcorp.com", company_size="250-500",
         annual_revenue="$45M - $60M", location="San Francisco, CA", funding_stage="Series C",
         tech_stack=["AWS", "Python", "React", "Node.js", "Kubernetes", "PostgreSQL"], lead_status="Qualified"),
    dict(company_name="InnovateAI Labs", industry="Software", contact_name="Mark Chen",
         contact_title="VP Sales", email="mark@innovateai.io", company_size="50-100",
         annual_revenue="$8M - $12M", location="Austin, TX", funding_stage="Series A",
         tech_stack=["GCP", "Python", "Docker"], lead_status="Contacted"),
    dict(company_name="DataFlow Systems", industry="Software", contact_name="Emily Davis",
         contact_title="CEO", email="emily@dataflow.dev", company_size="10-50",
         annual_revenue="$2M - $5M", location="Seattle, WA", funding_stage="Seed",
         tech_stack=["Azure", "Kafka", "Snowflake"], lead_status="New"),
    dict(company_name="CloudScale Inc.", industry="Finance", contact_name="Robert Lee",
         contact_title="Head of IT", email="robert@cloudscale.com", company_size="1000+",
         annual_revenue="$200M+", location="New York, NY", funding_stage="Public",
         tech_stack=["AWS", "Terraform", "Docker"], lead_status="New"),
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(models.Lead).count() == 0:
            for row in SEED:
                db.add(models.Lead(**row))
            db.commit()
    finally:
        db.close()
    yield


app = FastAPI(title="SalesGenie AI", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
                   allow_methods=["*"], allow_headers=["*"])


def get_lead_or_404(db: Session, lead_id: int) -> models.Lead:
    lead = db.get(models.Lead, lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")
    return lead


def check_status(status: str):
    if status not in models.STAGES:
        raise HTTPException(422, f"lead_status must be one of {models.STAGES}")


@app.get("/api/stages")
def stages():
    return models.STAGES


@app.get("/api/stats")
def stats(db: Session = Depends(get_db)):
    by_status = dict(db.query(models.Lead.lead_status, func.count()).group_by(models.Lead.lead_status).all())
    leads = db.query(models.Lead).all()
    scores = [l.latest_score for l in leads if l.latest_score is not None]
    return {"total": len(leads), "by_status": by_status, "analyzed": len(scores),
            "avg_score": round(sum(scores) / len(scores), 1) if scores else None,
            "hot": sum(1 for l in leads if l.latest_priority == "Hot")}


@app.get("/api/leads", response_model=List[schemas.LeadOut])
def list_leads(q: Optional[str] = None, status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.Lead)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(models.Lead.company_name.ilike(like), models.Lead.contact_name.ilike(like),
                                 models.Lead.industry.ilike(like), models.Lead.email.ilike(like)))
    if status:
        query = query.filter(models.Lead.lead_status == status)
    return query.order_by(models.Lead.updated_at.desc()).all()


@app.post("/api/leads", response_model=schemas.LeadOut, status_code=201)
def create_lead(payload: schemas.LeadCreate, db: Session = Depends(get_db)):
    check_status(payload.lead_status)
    lead = models.Lead(**payload.model_dump())
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


@app.get("/api/leads/{lead_id}", response_model=schemas.LeadOut)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    return get_lead_or_404(db, lead_id)


@app.put("/api/leads/{lead_id}", response_model=schemas.LeadOut)
def update_lead(lead_id: int, payload: schemas.LeadCreate, db: Session = Depends(get_db)):
    check_status(payload.lead_status)
    lead = get_lead_or_404(db, lead_id)
    for k, v in payload.model_dump().items():
        setattr(lead, k, v)
    db.commit()
    db.refresh(lead)
    return lead


@app.delete("/api/leads/{lead_id}", status_code=204)
def delete_lead(lead_id: int, db: Session = Depends(get_db)):
    db.delete(get_lead_or_404(db, lead_id))
    db.commit()


@app.get("/api/leads/{lead_id}/intelligence", response_model=schemas.IntelligenceOut)
def get_intelligence(lead_id: int, db: Session = Depends(get_db)):
    lead = get_lead_or_404(db, lead_id)
    return {"insight": lead.insights[0] if lead.insights else None,
            "score": lead.scores[0] if lead.scores else None}


@app.post("/api/leads/{lead_id}/analyze", response_model=schemas.IntelligenceOut)
def analyze_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = get_lead_or_404(db, lead_id)
    insight = models.CompanyInsight(lead_id=lead.lead_id, **generate_insight(lead))
    score = models.LeadScore(lead_id=lead.lead_id, **score_lead(lead))
    db.add_all([insight, score])
    db.commit()
    db.refresh(insight)
    db.refresh(score)
    return {"insight": insight, "score": score}


@app.post("/api/leads/import")
async def import_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    raw = (await file.read()).decode("utf-8-sig", errors="replace")
    imported, skipped = 0, []
    for i, row in enumerate(csv.DictReader(io.StringIO(raw)), start=2):
        row = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
        if not row.get("company_name"):
            skipped.append({"row": i, "reason": "missing company_name"})
            continue
        status = row.get("lead_status") or "New"
        if status not in models.STAGES:
            status = "New"
        stack = [t.strip() for t in row.get("tech_stack", "").replace(";", ",").split(",") if t.strip()]
        fields = {c: row.get(c) or None for c in (
            "company_name", "industry", "contact_name", "contact_title", "email", "phone", "website",
            "company_size", "annual_revenue", "location", "funding_stage", "notes")}
        db.add(models.Lead(**fields, tech_stack=stack, lead_status=status))
        imported += 1
    db.commit()
    return {"imported": imported, "skipped": skipped}
