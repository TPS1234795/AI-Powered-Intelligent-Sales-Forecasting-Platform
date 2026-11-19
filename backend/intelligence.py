"""Lead intelligence engine: rule-based scoring + optional Gemini insights."""
import json
import math
import os
import re
import httpx

FUNDING_POINTS = {"bootstrapped": 6, "seed": 8, "series a": 12, "series b": 16,
                  "series c": 20, "series d+": 22, "public": 18}
DECISION_MAKERS = ("ceo", "cto", "cfo", "coo", "cio", "chief", "founder", "vp", "vice president",
                   "head", "director", "owner")
MODERN_TECH = {"aws", "azure", "gcp", "kubernetes", "docker", "python", "react", "node.js",
               "postgresql", "snowflake", "kafka", "terraform"}
STATUS_POINTS = {"contacted": 3, "qualified": 8, "proposal": 12, "negotiation": 15}

INDUSTRY_NEEDS = {
    "software": ("Scalable cloud infrastructure", "Faster data pipelines", "Developer productivity tooling"),
    "finance": ("Regulatory compliance automation", "Fraud detection", "Real-time reporting"),
    "health": ("Patient data interoperability", "Process automation", "Secure cloud migration"),
    "retail": ("Demand forecasting", "Omnichannel customer analytics", "Inventory optimisation"),
    "manufactur": ("ERP modernisation", "Predictive maintenance", "Supply chain visibility"),
}
INDUSTRY_OPPS = {
    "software": ("Cloud migration", "Process automation", "Digital transformation project"),
    "finance": ("Process automation", "Digital transformation project"),
    "health": ("Cloud migration", "Digital transformation project"),
    "retail": ("Process automation", "Cloud migration"),
    "manufactur": ("ERP modernisation", "Process automation"),
}


def _numbers(text):
    return [int(n.replace(",", "")) for n in re.findall(r"\d[\d,]*", text or "")]


def _match(table, industry, default):
    industry = (industry or "").lower()
    for key, vals in table.items():
        if key in industry:
            return list(vals)
    return list(default)


def score_lead(lead) -> dict:
    factors, total = [], 20

    def add(label, pts, detail):
        nonlocal total
        if pts:
            total += pts
            factors.append({"label": label, "points": pts, "detail": detail})

    stage = (lead.funding_stage or "").lower()
    for key, pts in FUNDING_POINTS.items():
        if key in stage:
            add("Company growth", pts, f"{lead.funding_stage} funding signals available budget")
            break

    size = max(_numbers(lead.company_size) or [0])
    if size:
        add("Company size", 18 if size >= 1000 else 15 if size >= 250 else 10 if size >= 50 else 5,
            f"{lead.company_size} employees")

    title = (lead.contact_title or "").lower()
    if any(k in title for k in DECISION_MAKERS):
        add("Decision maker", 22, f"{lead.contact_title} can approve spend")
    elif "manager" in title or "lead" in title:
        add("Influencer", 10, f"{lead.contact_title} can champion internally")
    elif title:
        add("Contact seniority", 4, f"{lead.contact_title}")

    stack = {t.strip().lower() for t in (lead.tech_stack or [])}
    overlap = len(stack & MODERN_TECH)
    add("Tech alignment", min(overlap * 3, 15), f"{overlap} modern technologies in stack")

    if lead.annual_revenue:
        add("Revenue profile", 5, f"Revenue {lead.annual_revenue}")
    add("Pipeline stage", STATUS_POINTS.get((lead.lead_status or "").lower(), 0),
        f"Currently in {lead.lead_status}")

    score = min(total, 99)
    probability = round(100 / (1 + math.exp(-(score - 60) / 20)), 1)
    priority = "Hot" if score >= 75 else "Warm" if score >= 50 else "Cold"
    return {"lead_score": score, "conversion_probability": probability,
            "priority_level": priority, "factors": factors}


def rule_insight(lead) -> dict:
    needs = _match(INDUSTRY_NEEDS, lead.industry, ("Operational efficiency", "Better customer analytics"))
    opps = _match(INDUSTRY_OPPS, lead.industry, ("Process automation",))
    highlights = []
    stage = (lead.funding_stage or "")
    if stage:
        highlights.append({"title": "Growth signal",
                           "detail": f"{stage} funding suggests an expansion phase with budget for new tools."})
    if lead.tech_stack:
        highlights.append({"title": "Tech alignment",
                           "detail": f"Stack includes {', '.join(lead.tech_stack[:4])}, which fits modern integrations."})
    if any(k in (lead.contact_title or "").lower() for k in DECISION_MAKERS):
        highlights.append({"title": "Decision maker",
                           "detail": f"{lead.contact_name or 'Contact'} ({lead.contact_title}) holds buying authority."})
    analysis = (f"{lead.company_name} operates in {lead.industry or 'an unspecified industry'}"
                f"{' with ' + lead.company_size + ' employees' if lead.company_size else ''}"
                f"{' based in ' + lead.location if lead.location else ''}. "
                f"Primary needs: {', '.join(needs[:2]).lower()}.")
    return {"business_needs": needs, "opportunities": opps, "industry_analysis": analysis,
            "highlights": highlights, "source": "rules"}


def gemini_insight(lead):
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return None
    model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    profile = {c: getattr(lead, c) for c in ("company_name", "industry", "contact_title", "company_size",
                                             "annual_revenue", "location", "funding_stage", "tech_stack", "notes")}
    prompt = ("You are a B2B sales analyst. Analyse this prospect and reply with JSON only, shaped as "
              '{"business_needs":[str],"opportunities":[str],"industry_analysis":str,'
              '"highlights":[{"title":str,"detail":str}]}. Max 4 items per list, 3 highlights.\n'
              f"Prospect: {json.dumps(profile)}")
    try:
        r = httpx.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            params={"key": key}, timeout=20,
            json={"contents": [{"parts": [{"text": prompt}]}],
                  "generationConfig": {"responseMimeType": "application/json", "temperature": 0.4}})
        r.raise_for_status()
        data = json.loads(r.json()["candidates"][0]["content"]["parts"][0]["text"])
        return {"business_needs": [str(x) for x in data.get("business_needs", [])][:4],
                "opportunities": [str(x) for x in data.get("opportunities", [])][:4],
                "industry_analysis": str(data.get("industry_analysis", "")),
                "highlights": [h for h in data.get("highlights", []) if isinstance(h, dict)][:3],
                "source": "gemini"}
    except Exception:
        return None


def generate_insight(lead) -> dict:
    return gemini_insight(lead) or rule_insight(lead)
