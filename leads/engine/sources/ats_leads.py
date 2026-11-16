"""Greenhouse / Ashby / Lever → Lead adapters (curated public board tokens only)."""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

from job_scraper.engine.sources.ashby import AshbySource
from job_scraper.engine.sources.greenhouse import GreenhouseSource
from job_scraper.engine.sources.lever import LeverSource

from ..contacts import build_contacts_from_listing
from ..dedupe import make_lead_id
from ..intent import classify_intent
from ..model import Evidence, Lead, LeadType, SearchCriteria
from ..sanitize import safe_excerpt, sanitize_text
from .base import FetchResult, LeadSourceAdapter, SourceMeta

ROOT = Path(__file__).resolve().parents[3]
BOARDS_PATH = ROOT / "job_scraper" / "boards.json"

_STACK_RE = re.compile(
    r"(?i)\b(react(?:\.?js)?|next\.?js|typescript|javascript|node\.?js|full[-\s]?stack|"
    r"tailwind|mongodb|postgres(?:ql)?|supabase|stripe|saas|mern|redux|"
    r"frontend|front[\s-]?end)\b"
)


def load_boards() -> dict[str, list[dict[str, str]]]:
    if not BOARDS_PATH.is_file():
        return {"greenhouse": [], "ashby": [], "lever": []}
    data = json.loads(BOARDS_PATH.read_text(encoding="utf-8"))
    return {
        "greenhouse": list(data.get("greenhouse") or []),
        "ashby": list(data.get("ashby") or []),
        "lever": list(data.get("lever") or []),
    }


def _map_employment(raw: Optional[str]) -> LeadType:
    t = (raw or "").lower().replace("-", " ")
    if "freelance" in t:
        return "freelance"
    if "contract" in t or "temporary" in t or "fixed term" in t:
        return "contract"
    if "part" in t:
        return "contract"
    return "full_time"


def _wanted_types(criteria: SearchCriteria) -> set[str]:
    types = set(criteria.lead_types)
    if "all" in types or not types:
        return {"client", "freelance", "contract", "full_time"}
    if "client" in types:
        types |= {"freelance", "contract", "full_time"}
    return types


def _tech_ok(title: str, desc: str, techs: list[str], extracted: list[str]) -> bool:
    if not techs:
        return bool(_STACK_RE.search(f"{title} {desc}")) or True
    blob = f"{title} {desc} {' '.join(extracted)}".lower().replace(".", "")
    return any(t.lower().replace(".", "") in blob for t in techs) or bool(
        _STACK_RE.search(f"{title} {desc}")
    )


def _job_to_lead(
    *,
    source: str,
    company: str,
    title: str,
    url: str,
    location: str,
    country: Optional[str],
    workplace: str,
    published: Optional[str],
    description: str,
    salary: Optional[str],
    employment_type: Optional[str],
    sponsorship: Any,
    source_job_id: str,
    board: str,
    criteria: SearchCriteria,
    today: str,
) -> Lead:
    desc = sanitize_text(description or "", max_len=5000)
    job_type = _map_employment(employment_type)
    techs = sorted({m.group(0).lower() for m in _STACK_RE.finditer(f"{title} {desc}")})
    intent, intent_expl = classify_intent(
        title=title,
        description=desc,
        lead_type_hint=job_type,
        source_kind="job_listing",
    )
    contacts = build_contacts_from_listing(
        description=desc,
        listing_url=url,
        company=company,
        check_mx=False,
    )
    expired = False
    if published:
        try:
            age = (date.today() - datetime.strptime(published[:10], "%Y-%m-%d").date()).days
            expired = age > max(criteria.freshness_days * 3, 90)
        except ValueError:
            expired = False

    risks: list[str] = []
    if expired:
        risks.append("Listing may be stale relative to freshness window")
    if not salary:
        risks.append("Compensation not stated on listing")
    spons_status = (
        getattr(sponsorship, "classification", None) if sponsorship is not None else None
    )
    if spons_status and spons_status != "unknown":
        risks.append(f"Sponsorship signal: {spons_status}")

    wp = workplace if workplace in ("remote", "hybrid", "onsite", "unknown") else "unknown"

    return Lead(
        id=make_lead_id(source=source, company=company, title=title, url=url),
        name=f"{company} — {title}",
        lead_type=job_type,
        company=company,
        title=title,
        url=url,
        source=source,
        intent=intent,
        intent_explanation=intent_expl,
        evidence=[
            Evidence(
                summary=f"{source.title()} ATS listing: {title} at {company}",
                excerpt=safe_excerpt(desc, max_len=280),
                source_url=url,
                published_date=published,
                checked_date=today,
            )
        ],
        technical_requirements=techs,
        profile_match_reasons=[],
        recommended_service=f"Full-stack / frontend product engineering ({', '.join(techs[:4]) or 'React/TS'}).",
        contacts=contacts,
        budget_or_salary=(salary or None),
        location=location or "",
        workplace=wp,  # type: ignore[arg-type]
        country=country,
        published_date=published,
        checked_date=today,
        expired=expired,
        risks=risks,
        next_action=f"Review official {source} posting URL (do not auto-apply).",
        raw={
            "ats": source,
            "board": board,
            "source_job_id": source_job_id,
            "sponsorship": spons_status,
            "employment_type": employment_type,
        },
    )


def _normalize_jobs(
    jobs: list[Any],
    *,
    source: str,
    criteria: SearchCriteria,
) -> tuple[list[Lead], list[str]]:
    leads: list[Lead] = []
    errors: list[str] = []
    wanted = _wanted_types(criteria)
    excluded = {c.lower() for c in criteria.excluded_companies}
    today = date.today().isoformat()
    for job in jobs:
        try:
            company = (job.company or "").strip()
            title = (job.title or "").strip()
            url = (job.url or "").strip()
            if not company or not title or not url:
                continue
            if company.lower() in excluded:
                continue
            lead_type = _map_employment(getattr(job, "employment_type", None))
            if lead_type not in wanted and "all" not in criteria.lead_types:
                continue
            desc = job.description or ""
            techs = sorted({m.group(0).lower() for m in _STACK_RE.finditer(f"{title} {desc}")})
            if not _tech_ok(title, desc, criteria.technologies, techs):
                continue
            if criteria.require_sponsorship:
                spons = getattr(job, "sponsorship", None)
                classification = (
                    getattr(spons, "classification", "") if spons is not None else ""
                )
                if classification not in (
                    "verified_in_listing",
                    "possible",
                    "sponsor_company_only",
                ):
                    if not re.search(r"(?i)\b(visa|sponsor|relocati)", desc):
                        continue
            lead = _job_to_lead(
                source=source,
                company=company,
                title=title,
                url=url,
                location=getattr(job, "location", "") or "",
                country=getattr(job, "country", None),
                workplace=getattr(job, "workplace", "unknown") or "unknown",
                published=getattr(job, "published_date", None),
                description=desc,
                salary=getattr(job, "salary", None),
                employment_type=getattr(job, "employment_type", None),
                sponsorship=getattr(job, "sponsorship", None),
                source_job_id=getattr(job, "source_job_id", "") or "",
                board=str((getattr(job, "raw", None) or {}).get("board") or ""),
                criteria=criteria,
                today=today,
            )
            leads.append(lead)
            if len(leads) >= max(criteria.limit * 2, 40):
                break
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{source} parse: {exc}")
    return leads, errors


class GreenhouseLeadsSource(LeadSourceAdapter):
    meta = SourceMeta(
        name="greenhouse",
        official_api=True,
        notes="Public Greenhouse Job Board API; curated tokens in job_scraper/boards.json only.",
    )

    def fetch(self, criteria: SearchCriteria, **kwargs: Any) -> FetchResult:
        if "greenhouse" in {s.lower() for s in criteria.excluded_sources}:
            return FetchResult(meta={"skipped": "excluded_sources"})
        boards = load_boards().get("greenhouse") or []
        if not boards:
            return FetchResult(errors=["greenhouse: no boards configured"], meta={"boards": 0})
        max_jobs = min(80, max(criteria.limit * 2, 30))
        result = GreenhouseSource().fetch(
            boards=boards,
            role_filter=True,
            fetch_content=True,
            max_jobs=max_jobs,
            max_per_board=15,
        )
        leads, parse_errors = _normalize_jobs(result.jobs, source="greenhouse", criteria=criteria)
        return FetchResult(
            leads=leads,
            errors=list(result.errors) + parse_errors,
            meta={
                "boards": len(boards),
                "raw_jobs": len(result.jobs),
                "attribution": "Greenhouse public boards-api; original absolute_url per job.",
                **(result.meta or {}),
            },
        )


class AshbyLeadsSource(LeadSourceAdapter):
    meta = SourceMeta(
        name="ashby",
        official_api=True,
        notes="Public Ashby posting API; curated slugs in job_scraper/boards.json only.",
    )

    def fetch(self, criteria: SearchCriteria, **kwargs: Any) -> FetchResult:
        if "ashby" in {s.lower() for s in criteria.excluded_sources}:
            return FetchResult(meta={"skipped": "excluded_sources"})
        boards = load_boards().get("ashby") or []
        if not boards:
            return FetchResult(errors=["ashby: no boards configured"], meta={"boards": 0})
        max_jobs = min(80, max(criteria.limit * 2, 30))
        result = AshbySource().fetch(
            boards=boards,
            role_filter=True,
            max_jobs=max_jobs,
            max_per_board=15,
        )
        leads, parse_errors = _normalize_jobs(result.jobs, source="ashby", criteria=criteria)
        return FetchResult(
            leads=leads,
            errors=list(result.errors) + parse_errors,
            meta={
                "boards": len(boards),
                "raw_jobs": len(result.jobs),
                "attribution": "Ashby public posting-api; original jobUrl per posting.",
                **(result.meta or {}),
            },
        )


class LeverLeadsSource(LeadSourceAdapter):
    meta = SourceMeta(
        name="lever",
        official_api=True,
        notes="Public Lever postings API; curated sites in job_scraper/boards.json only.",
    )

    def fetch(self, criteria: SearchCriteria, **kwargs: Any) -> FetchResult:
        if "lever" in {s.lower() for s in criteria.excluded_sources}:
            return FetchResult(meta={"skipped": "excluded_sources"})
        boards = load_boards().get("lever") or []
        if not boards:
            return FetchResult(errors=["lever: no boards configured"], meta={"boards": 0})
        max_jobs = min(80, max(criteria.limit * 2, 30))
        result = LeverSource().fetch(
            boards=boards,
            role_filter=True,
            max_jobs=max_jobs,
            max_per_board=15,
        )
        leads, parse_errors = _normalize_jobs(result.jobs, source="lever", criteria=criteria)
        return FetchResult(
            leads=leads,
            errors=list(result.errors) + parse_errors,
            meta={
                "boards": len(boards),
                "raw_jobs": len(result.jobs),
                "attribution": "Lever public postings API; original hostedUrl per posting.",
                **(result.meta or {}),
            },
        )
