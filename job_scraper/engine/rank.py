"""Configurable ranking: separate sponsorship score and skill-match score."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from .model import NormalizedJob
from .normalize import ROLE_KEYWORDS, TARGET_COUNTRIES

# Default preferred countries (Pakistan → target geos from the upgrade brief + profile).
DEFAULT_PREFERRED = {
    "DE", "NL", "GB", "IE", "AU", "CA", "NZ", "US", "SE", "FI", "DK", "AE", "SA", "QA", "PK", "CH"
}

_SPONSOR_SCORE = {
    "verified_in_listing": 1.0,
    "possible": 0.55,
    "sponsor_company_only": 0.35,
    "unknown": 0.15,
    "not_available": 0.0,
}

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
    "saas",
    "redux",
    "postgresql",
    "mongodb",
    "aws",
    "docker",
]


@dataclass
class RankScores:
    overall: float
    sponsorship_score: float
    skill_score: float
    country_score: float
    freshness_score: float
    reasons: list[str]


def _parse_day(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def skill_match_score(job: NormalizedJob) -> tuple[float, list[str]]:
    blob = f"{job.title} {job.description}".lower()
    title = (job.title or "").lower()
    reasons: list[str] = []
    hits = [s for s in _PROFILE_SKILLS if s in blob]
    role_hit = any(k in title for k in ROLE_KEYWORDS)
    if not role_hit and not hits:
        return 0.05, ["title outside target role keywords"]
    score = 0.35 if role_hit else 0.1
    score += min(0.55, 0.08 * len(set(hits)))
    if any(s in title for s in ("react", "next", "typescript", "full stack", "frontend")):
        score = min(1.0, score + 0.15)
        reasons.append("core stack in title")
    if hits:
        reasons.append("skills: " + ", ".join(sorted(set(hits))[:6]))
    return min(1.0, score), reasons


def country_score(job: NormalizedJob, preferred: set[str]) -> tuple[float, list[str]]:
    if job.country and job.country in preferred:
        return 1.0, [f"target country {job.country}"]
    if job.workplace == "remote":
        return 0.7, ["remote (country unset)"]
    if job.country is None:
        return 0.4, ["country unknown"]
    return 0.1, [f"outside preferred ({job.country})"]


def freshness_score(job: NormalizedJob) -> tuple[float, list[str]]:
    published = _parse_day(job.published_date)
    if not published:
        return 0.4, ["date unknown"]
    age = (date.today() - published).days
    if age < 0:
        age = 0
    if age <= 7:
        return 1.0, [f"posted {age}d ago"]
    if age <= 14:
        return 0.75, [f"posted {age}d ago"]
    if age <= 30:
        return 0.4, [f"posted {age}d ago"]
    return 0.15, [f"stale ({age}d)"]


def rank_job(
    job: NormalizedJob,
    *,
    preferred_countries: Optional[set[str]] = None,
    weights: Optional[dict[str, float]] = None,
) -> RankScores:
    preferred = preferred_countries or DEFAULT_PREFERRED
    w = {
        "sponsorship": 0.35,
        "skill": 0.35,
        "country": 0.2,
        "freshness": 0.1,
        **(weights or {}),
    }
    cls = (job.sponsorship.classification if job.sponsorship else "unknown")
    s_score = _SPONSOR_SCORE.get(cls, 0.15)
    # Hard rule: not_available never ranks as a confirmed sponsored job
    if cls == "not_available":
        s_score = 0.0

    sk, sk_reasons = skill_match_score(job)
    co, co_reasons = country_score(job, preferred)
    fr, fr_reasons = freshness_score(job)

    overall = (
        w["sponsorship"] * s_score
        + w["skill"] * sk
        + w["country"] * co
        + w["freshness"] * fr
    )
    # Cap overall when sponsorship unavailable so skill-only matches stay visible but not "sponsored"
    if cls == "not_available":
        overall = min(overall, 0.45)

    reasons = [f"sponsorship={cls} ({s_score:.2f})"] + sk_reasons + co_reasons + fr_reasons
    return RankScores(
        overall=round(overall, 4),
        sponsorship_score=round(s_score, 4),
        skill_score=round(sk, 4),
        country_score=round(co, 4),
        freshness_score=round(fr, 4),
        reasons=reasons,
    )


def rank_jobs(
    jobs: list[NormalizedJob],
    *,
    preferred_countries: Optional[set[str]] = None,
) -> list[tuple[NormalizedJob, RankScores]]:
    scored = [(j, rank_job(j, preferred_countries=preferred_countries)) for j in jobs]
    scored.sort(key=lambda pair: pair[1].overall, reverse=True)
    return scored
