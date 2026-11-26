"""Independent job/client scoring with hireability Grade A gate."""

from __future__ import annotations

from datetime import date, datetime

from agent.models.opportunity import OpportunityRecord, grade_from_score

STACK = {
    "react",
    "next",
    "nextjs",
    "typescript",
    "javascript",
    "nodejs",
    "node",
    "express",
    "supabase",
    "postgres",
    "postgresql",
    "mongodb",
    "mysql",
    "tailwind",
    "redux",
    "reactnative",
    "expo",
    "saas",
    "fullstack",
    "aws",
    "firebase",
}

_DEMAND_MARKERS = (
    "hiring",
    "we're hiring",
    "we are hiring",
    "looking for",
    "open role",
    "job opening",
    "apply now",
    "join our team",
    "now hiring",
)


def _text_blob(rec: OpportunityRecord) -> str:
    return " ".join(
        [
            rec.role_or_title,
            rec.description,
            rec.required_skills,
            rec.company,
            rec.evidence,
        ]
    ).casefold()


def _skill_points(blob: str, max_pts: int = 30) -> float:
    compact = blob.replace(".", "").replace(" ", "")
    hits = sum(1 for s in STACK if s in compact)
    if "next.js" in blob or "nextjs" in blob:
        hits += 1
    if "full stack" in blob or "fullstack" in blob:
        hits += 1
    return min(max_pts, hits * 4)


def _freshness_points(posted: str, max_pts: int = 10) -> float:
    if not posted:
        return max_pts * 0.4
    try:
        d = datetime.strptime(str(posted)[:10], "%Y-%m-%d").date()
    except ValueError:
        return max_pts * 0.4
    age = (date.today() - d).days
    if age <= 2:
        return max_pts
    if age <= 7:
        return max_pts * 0.8
    if age <= 14:
        return max_pts * 0.5
    if age <= 30:
        return max_pts * 0.2
    return 0


def has_demand_signal(rec: OpportunityRecord) -> bool:
    intent = (rec.intent_classification or "").upper()
    if intent == "EXPLICIT_DEMAND":
        return True
    if intent == "STRONG_SIGNAL":
        return True
    if (rec.sponsorship_class or "") == "verified_in_listing":
        return True
    if (rec.path or "").upper() in ("A", "B") and rec.source_url:
        return True
    blob = _text_blob(rec)
    return any(m in blob for m in _DEMAND_MARKERS)


def has_reachable_contact(rec: OpportunityRecord) -> bool:
    if rec.contact_email and (rec.email_status or "") != "INFERRED":
        return True
    if getattr(rec, "contact_phone", ""):
        return True
    if getattr(rec, "contact_whatsapp", ""):
        return True
    if rec.linkedin_url and "linkedin.com/in/" in rec.linkedin_url.lower():
        return True
    return False


def contact_points(rec: OpportunityRecord, email_pts: int = 10, li_pts: int = 5) -> float:
    if rec.contact_email and (rec.email_status or "") == "VERIFIED":
        return float(email_pts)
    if rec.contact_email and (rec.email_status or "") != "INFERRED":
        return float(email_pts) * 0.85
    if getattr(rec, "contact_phone", "") or getattr(rec, "contact_whatsapp", ""):
        return float(email_pts) * 0.8
    if rec.linkedin_url and "linkedin.com/in/" in (rec.linkedin_url or "").lower():
        return float(li_pts)
    if rec.source_url:
        return 2.0  # Tier C apply URL
    return 0.0


def _apply_grade_a_gate(rec: OpportunityRecord) -> None:
    """Grade A only with real demand + reachable contact (email or founder LinkedIn)."""
    if rec.grade != "A":
        return
    if has_demand_signal(rec) and has_reachable_contact(rec):
        return
    # Demote — scrapey high scores without hireability must not be A
    if has_demand_signal(rec) and rec.source_url:
        rec.grade = "B"
        rec.opportunity_score = min(rec.opportunity_score, 84.0)
    else:
        rec.grade = "C" if rec.opportunity_score >= 50 else "Low"
        rec.opportunity_score = min(rec.opportunity_score, 69.0)


def score_job(rec: OpportunityRecord) -> OpportunityRecord:
    blob = _text_blob(rec)
    skill = _skill_points(blob, 30)
    hiring = 20 if has_demand_signal(rec) else (8 if rec.source_url else 2)
    if (rec.sponsorship_class or "") == "verified_in_listing":
        hiring = max(hiring, 20)
    intl = 0.0
    if (rec.visa_sponsorship or "").lower() in ("yes", "true", "1"):
        intl += 8
    if (rec.relocation_support or "").lower() in ("yes", "true", "1"):
        intl += 4
    if (rec.path or "").upper() == "A" or "worldwide" in (
        rec.international_eligibility or ""
    ).casefold():
        intl += 5
    elif (rec.remote_type or "").lower() == "remote":
        intl += 2
    intl = min(15, intl)
    senior = 15 if any(w in blob for w in ("senior", "staff", "lead", "principal")) else 10
    if "junior" in blob or "intern" in blob:
        senior = 4
    fresh = _freshness_points(rec.posted_date, 10)
    comp = 5 if rec.salary_or_budget else 2
    contact = contact_points(rec, email_pts=8, li_pts=5)
    total = skill + hiring + intl + senior + fresh + comp + contact
    rec.opportunity_score = round(min(100, total), 1)
    rec.grade = grade_from_score(rec.opportunity_score)
    rec.skill_score = round(skill / 30 * 100, 1) if skill else 0
    _apply_grade_a_gate(rec)
    return rec


def score_client(rec: OpportunityRecord) -> OpportunityRecord:
    blob = _text_blob(rec)
    intent = {
        "EXPLICIT_DEMAND": 30,
        "STRONG_SIGNAL": 18,
        "POTENTIAL_FIT": 8,
    }.get((rec.intent_classification or "").upper(), 5)
    skill = _skill_points(blob, 20)
    clarity = 15 if len(rec.description or "") > 80 else 7
    budget = 15 if rec.salary_or_budget else 4
    contact = contact_points(rec, email_pts=12, li_pts=7)
    fresh = _freshness_points(rec.posted_date or rec.discovered_date, 10)
    total = intent + skill + clarity + budget + contact + fresh
    rec.opportunity_score = round(min(100, total), 1)
    rec.grade = grade_from_score(rec.opportunity_score)
    _apply_grade_a_gate(rec)
    return rec


def score_opportunity(rec: OpportunityRecord) -> OpportunityRecord:
    otype = (rec.opportunity_type or "").lower()
    if otype in ("job", "contract"):
        return score_job(rec)
    return score_client(rec)
