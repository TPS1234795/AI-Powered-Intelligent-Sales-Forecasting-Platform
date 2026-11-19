from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class LeadBase(BaseModel):
    company_name: str = Field(min_length=1, max_length=200)
    industry: Optional[str] = None
    contact_name: Optional[str] = None
    contact_title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    company_size: Optional[str] = None
    annual_revenue: Optional[str] = None
    location: Optional[str] = None
    funding_stage: Optional[str] = None
    tech_stack: List[str] = []
    notes: Optional[str] = None
    lead_status: str = "New"


class LeadCreate(LeadBase):
    pass


class LeadOut(LeadBase):
    model_config = ConfigDict(from_attributes=True)
    lead_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    latest_score: Optional[int] = None
    latest_priority: Optional[str] = None


class InsightOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    insight_id: int
    lead_id: int
    business_needs: List[str] = []
    opportunities: List[str] = []
    industry_analysis: Optional[str] = None
    highlights: List[dict] = []
    source: str = "rules"
    generated_at: datetime


class ScoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    score_id: int
    lead_id: int
    lead_score: int
    conversion_probability: float
    priority_level: Optional[str] = None
    factors: List[dict] = []
    generated_at: datetime


class IntelligenceOut(BaseModel):
    insight: Optional[InsightOut] = None
    score: Optional[ScoreOut] = None
