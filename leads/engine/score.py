"""Explainable scoring: intent and fit stay separate dimensions."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from .model import ContactChannel, IntentClass, Lead, LeadScores, SearchCriteria

_INTENT_BASE = {
    "EXPLICIT_DEMAND": 1.0,
    "STRONG_SIGNAL": 0.55,
    "POTENTIAL_FIT": 0.2,
}

# Skills that match the candidate profile (from CLAUDE.md / 01-candidate-profile).
_PROFILE_SKILLS = [
    "react",
    "next.js",
    "nextjs",
    "typescript",
    "javascript",
    "node",
    "nodejs",
    "node.js",
    "full stack",
    "fullstack",
    "full-stack",
    "saas",
    "mongodb",
    "postgresql",
    "supabase",
    "stripe",
    "tailwind",
    "react native",
    "docker",
    "aws",
    "firebase",
    "shopify",
    "redux",
    "rest",
    "api",
]


def _parse_day(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def freshness_score(published: Optional[str], *, max_days: int = 30) -> tuple[float, str]:
    day = _parse_day(published)
    if day is None:
        return 0.35, "publication date unknown"
    age = (date.today() - day).days
    if age < 0:
        age = 0
    if age <= 7:
        return 1.0, f"published {age}d ago"
    if age <= max_days:
        return max(0.4, 1.0 - (age / (max_days * 1.5))), f"published {age}d ago"
    return 0.15, f"stale ({age}d old)"


def fit_score(
    *,
    title: str,
    description: str,
    requirements: list[str],
    criteria: SearchCriteria,
) -> tuple[float, list[str]]:
    blob = f"{title} {description} {' '.join(requirements)}".lower()
    reasons: list[str] = []
    hits = [s for s in _PROFILE_SKILLS if s in blob]
    tech_wanted = [t.lower() for t in criteria.technologies]
    wanted_hits = [t for t in tech_wanted if t.replace(".", "") in blob.replace(".", "") or t in blob]
    score = 0.1
    if hits:
        score += min(0.55, 0.09 * len(set(hits)))
        reasons.append("profile skills: " + ", ".join(sorted(set(hits))[:6]))
    if wanted_hits:
        score += min(0.25, 0.08 * len(set(wanted_hits)))
        reasons.append("requested tech: " + ", ".join(sorted(set(wanted_hits))[:5]))
    title_l = title.lower()
    if any(k in title_l for k in ("react", "next", "full stack", "frontend", "typescript", "node")):
        score = min(1.0, score + 0.15)
        reasons.append("core stack in title")
    if not reasons:
        reasons.append("weak skill overlap with profile")
        score = min(score, 0.2)
    return min(1.0, score), reasons


def contact_score(contacts: list[ContactChannel]) -> tuple[float, str]:
    if not contacts:
        return 0.1, "no contact channel"
    best = 0.15
    note = "weak contact"
    for c in contacts:
        if c.channel_type == "email" and c.verification_status in (
            "published_on_official_source",
            "domain_mx_present",
        ):
            best = max(best, 1.0 if c.verification_status == "domain_mx_present" else 0.92)
            note = f"published email ({c.verification_status})"
        elif (
            c.channel_type == "professional_profile"
            and c.verification_status == "published_on_official_source"
            and "linkedin.com/in/" in (c.value or "").lower()
        ):
            # Named founder LinkedIn beats anonymous apply forms for reply rate.
            best = max(best, 0.72)
            note = "published founder/professional LinkedIn"
        elif c.channel_type == "application_page" and c.value:
            best = max(best, 0.48)
            if note == "weak contact":
                note = "application/project page only (cold ATS)"
        elif c.channel_type == "contact_form":
            best = max(best, 0.58)
            note = "official contact form"
        elif c.channel_type == "professional_profile":
            best = max(best, 0.40)
            if "weak" in note or note == "application/project page only (cold ATS)":
                note = "public professional profile search link"
    return best, note


def score_lead(lead: Lead, criteria: SearchCriteria) -> LeadScores:
    from .quality import next_action_for_tier, quality_tier, tier_label

    intent_s = _INTENT_BASE.get(lead.intent, 0.2)
    # Explicit demand must outrank speculative fit even with perfect skills.
    fit_s, fit_reasons = fit_score(
        title=lead.title,
        description=" ".join(e.summary for e in lead.evidence) + " " + lead.recommended_service,
        requirements=lead.technical_requirements,
        criteria=criteria,
    )
    # Prefer technical requirements blob when present
    if lead.technical_requirements:
        fit_s2, fit_r2 = fit_score(
            title=lead.title,
            description=" ".join(lead.technical_requirements),
            requirements=lead.technical_requirements,
            criteria=criteria,
        )
        if fit_s2 > fit_s:
            fit_s, fit_reasons = fit_s2, fit_r2

    fresh_s, fresh_note = freshness_score(lead.published_date, max_days=criteria.freshness_days)
    if lead.expired:
        fresh_s = 0.0
        fresh_note = "listing marked expired"

    contact_s, contact_note = contact_score(lead.contacts)

    # Reply-first weighting: contact reaches decision-makers; intent still required.
    overall = (
        0.38 * intent_s
        + 0.27 * fit_s
        + 0.12 * fresh_s
        + 0.23 * contact_s
    )
    # Hard rule: POTENTIAL_FIT cannot outrank EXPLICIT_DEMAND with similar fit
    # via overall alone — intent weight already enforces this; add a floor gap.
    if lead.intent == "POTENTIAL_FIT":
        overall = min(overall, 0.42)

    tier = quality_tier(lead)
    if tier == "A":
        overall = min(1.0, overall + 0.08)
    elif tier == "B":
        overall = min(1.0, overall + 0.04)
    elif tier == "C":
        overall = max(0.0, overall - 0.06)  # demote cold apply-URL-only
    else:
        overall = min(overall, 0.35)

    # Persist actionable next step for exports / agent tables
    lead.next_action = next_action_for_tier(lead, tier)
    lead.raw = dict(lead.raw or {})
    lead.raw["quality_tier"] = tier

    reasons = [
        f"intent={lead.intent} ({intent_s:.2f})",
        f"fit={fit_s:.2f}: " + "; ".join(fit_reasons[:2]),
        f"freshness={fresh_s:.2f}: {fresh_note}",
        f"contact={contact_s:.2f}: {contact_note}",
        f"tier={tier_label(tier)}",
    ]
    ver = (lead.raw or {}).get("verification_status")
    if ver:
        reasons.append(f"verification={ver}")
    return LeadScores(
        intent_score=intent_s,
        fit_score=fit_s,
        contact_score=contact_s,
        freshness_score=fresh_s,
        overall=overall,
        reasons=reasons,
    )


def intent_rank_key(intent: IntentClass) -> int:
    return {"EXPLICIT_DEMAND": 0, "STRONG_SIGNAL": 1, "POTENTIAL_FIT": 2}.get(intent, 9)
