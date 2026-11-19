from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base

STAGES = ["New", "Contacted", "Qualified", "Proposal", "Negotiation", "Closed Won", "Closed Lost"]


class Lead(Base):
    __tablename__ = "leads"

    lead_id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(200), nullable=False, index=True)
    industry = Column(String(120))
    contact_name = Column(String(120))
    contact_title = Column(String(120))
    email = Column(String(200))
    phone = Column(String(50))
    website = Column(String(200))
    company_size = Column(String(50))
    annual_revenue = Column(String(60))
    location = Column(String(120))
    funding_stage = Column(String(50))
    tech_stack = Column(JSON, default=list)
    notes = Column(Text)
    lead_status = Column(String(30), default="New", index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    insights = relationship("CompanyInsight", back_populates="lead",
                            cascade="all, delete-orphan", order_by="CompanyInsight.insight_id.desc()")
    scores = relationship("LeadScore", back_populates="lead",
                          cascade="all, delete-orphan", order_by="LeadScore.score_id.desc()")

    @property
    def latest_score(self):
        return self.scores[0].lead_score if self.scores else None

    @property
    def latest_priority(self):
        return self.scores[0].priority_level if self.scores else None


class CompanyInsight(Base):
    __tablename__ = "company_insights"

    insight_id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.lead_id"), nullable=False, index=True)
    business_needs = Column(JSON, default=list)
    opportunities = Column(JSON, default=list)
    industry_analysis = Column(Text)
    highlights = Column(JSON, default=list)
    source = Column(String(20), default="rules")
    generated_at = Column(DateTime, default=datetime.utcnow)

    lead = relationship("Lead", back_populates="insights")


class LeadScore(Base):
    __tablename__ = "lead_scores"

    score_id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.lead_id"), nullable=False, index=True)
    lead_score = Column(Integer, nullable=False)
    conversion_probability = Column(Float, nullable=False)
    priority_level = Column(String(10))
    factors = Column(JSON, default=list)
    generated_at = Column(DateTime, default=datetime.utcnow)

    lead = relationship("Lead", back_populates="scores")
