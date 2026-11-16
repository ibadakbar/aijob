"""Parse natural-language /leads prompts into SearchCriteria."""

from __future__ import annotations

import re
from typing import Optional

from .model import DiscoveryMode, LeadType, SearchCriteria, Workplace

_DEFAULT_TECH = [
    "react",
    "next.js",
    "typescript",
    "javascript",
    "node.js",
    "full-stack",
    "saas",
]

_TECH_ALIASES = {
    "react": "react",
    "react.js": "react",
    "reactjs": "react",
    "next": "next.js",
    "next.js": "next.js",
    "nextjs": "next.js",
    "typescript": "typescript",
    "ts": "typescript",
    "javascript": "javascript",
    "js": "javascript",
    "node": "node.js",
    "nodejs": "node.js",
    "node.js": "node.js",
    "tailwind": "tailwind",
    "mongodb": "mongodb",
    "postgres": "postgresql",
    "postgresql": "postgresql",
    "supabase": "supabase",
    "stripe": "stripe",
    "shopify": "shopify",
    "react native": "react native",
    "mern": "mern",
    "saas": "saas",
    "full stack": "full-stack",
    "fullstack": "full-stack",
    "full-stack": "full-stack",
}

_GEO_MARKERS = {
    "uk": "United Kingdom",
    "united kingdom": "United Kingdom",
    "britain": "United Kingdom",
    "england": "United Kingdom",
    "germany": "Germany",
    "deutschland": "Germany",
    "australia": "Australia",
    "uae": "UAE",
    "dubai": "UAE",
    "united arab emirates": "UAE",
    "netherlands": "Netherlands",
    "holland": "Netherlands",
    "ireland": "Ireland",
    "canada": "Canada",
    "united states": "United States",
    "usa": "United States",
    "us": "United States",
    "sweden": "Sweden",
    "finland": "Finland",
    "denmark": "Denmark",
    "switzerland": "Switzerland",
    "saudi": "Saudi Arabia",
    "qatar": "Qatar",
    "new zealand": "New Zealand",
    "pakistan": "Pakistan",
    "europe": "Europe",
    "eu": "Europe",
    "remote": "Remote",
}

_LEAD_TYPE_PATTERNS: list[tuple[re.Pattern[str], LeadType]] = [
    (re.compile(r"(?i)\b(client|clients|business(?:es)?|founder|agency|agencies|subcontract)\b"), "client"),
    (re.compile(r"(?i)\b(freelance|freelancer|gig|project brief)\b"), "freelance"),
    (re.compile(r"(?i)\b(contract|contractor|contracting)\b"), "contract"),
    (re.compile(r"(?i)\b(full[-\s]?time|permanent|fte|job|jobs|hiring|vacanc)\b"), "full_time"),
]

_EXCLUDE_COMPANY_RE = re.compile(
    r"(?i)(?:exclude|skip|ignore|except)\s+(?:compan(?:y|ies)\s+)?([A-Za-z0-9 .,&-]{2,60})"
)
_EXCLUDE_SOURCE_RE = re.compile(
    r"(?i)(?:exclude|skip|ignore)\s+(?:source|portal|board)s?\s+([a-z0-9_,\-\s]+)"
)
_LIMIT_RE = re.compile(r"(?i)\b(?:find|return|get|top|up to)?\s*(\d{1,3})\b")
_FRESH_RE = re.compile(r"(?i)\b(?:last|past|within)\s+(\d{1,3})\s+days?\b")
_BUDGET_RE = re.compile(
    r"(?i)(?:budget|rate|salary|\$|€|£)\s*[:=]?\s*([\$€£]?\s*[\d,]+(?:\s*[-–]\s*[\$€£]?[\d,]+)?(?:\s*(?:k|\/hr|\/hour|per hour|a year|\/yr))?)"
)


def _extract_technologies(text: str) -> list[str]:
    lower = text.lower()
    found: list[str] = []
    # Longer keys first so "react native" beats "react"
    for key in sorted(_TECH_ALIASES.keys(), key=len, reverse=True):
        if key in lower and _TECH_ALIASES[key] not in found:
            found.append(_TECH_ALIASES[key])
    return found or list(_DEFAULT_TECH)


def _extract_geographies(text: str) -> list[str]:
    lower = text.lower()
    found: list[str] = []
    for key in sorted(_GEO_MARKERS.keys(), key=len, reverse=True):
        # Word-boundary-ish for short keys like "us" / "uk" / "eu"
        if len(key) <= 3:
            if re.search(rf"(?<![a-z]){re.escape(key)}(?![a-z])", lower):
                geo = _GEO_MARKERS[key]
                if geo not in found:
                    found.append(geo)
        elif key in lower:
            geo = _GEO_MARKERS[key]
            if geo not in found:
                found.append(geo)
    return found


def _extract_lead_types(text: str) -> list[LeadType]:
    types: list[LeadType] = []
    for pat, lt in _LEAD_TYPE_PATTERNS:
        if pat.search(text) and lt not in types:
            types.append(lt)
    if not types or re.search(r"(?i)\b(all types|any lead|everything)\b", text):
        return ["all"]
    return types


def _extract_workplace(text: str) -> list[Workplace]:
    lower = text.lower()
    out: list[Workplace] = []
    if "remote" in lower:
        out.append("remote")
    if "hybrid" in lower:
        out.append("hybrid")
    if re.search(r"(?i)\b(on[-\s]?site|onsite|in[-\s]?office)\b", lower):
        out.append("onsite")
    return out or ["remote", "hybrid", "onsite"]


def _extract_industries(text: str) -> list[str]:
    markers = {
        "saas": "SaaS",
        "startup": "startup",
        "agency": "agency",
        "e-commerce": "e-commerce",
        "ecommerce": "e-commerce",
        "fintech": "fintech",
        "advertising": "advertising",
        "marketplace": "marketplace",
        "mvp": "MVP / product engineering",
    }
    lower = text.lower()
    return [label for key, label in markers.items() if key in lower]


def _extract_discovery_modes(text: str) -> list[DiscoveryMode]:
    lower = text.lower()
    modes: list[DiscoveryMode] = []
    if re.search(
        r"(?i)\b(opportunity radar|funded|funding|series [abc]|seed round|"
        r"product launch|newly launched|client win|expand(?:ing)? (?:the )?engineering|"
        r"demand signal|radar)\b",
        lower,
    ):
        modes.append("radar")
    if re.search(
        r"(?i)\b(agency|agencies|white-?label|subcontract|partnership|"
        r"overflow|design studio|consultancy partner)\b",
        lower,
    ):
        modes.append("agency")
    if re.search(
        r"(?i)\b(job|jobs|hiring|vacanc|full[-\s]?time|contract|freelance|"
        r"developer|engineer|role)\b",
        lower,
    ) or not modes:
        modes.append("jobs")
    # Deduplicate while preserving order
    out: list[DiscoveryMode] = []
    for mode in modes:
        if mode not in out:
            out.append(mode)
    return out


def parse_prompt(prompt: str, *, defaults: Optional[SearchCriteria] = None) -> SearchCriteria:
    """Convert a natural-language /leads request into structured criteria.

    Uses sensible defaults when optional details are omitted. Does not ask
    clarifying questions — callers decide when a missing essential detail warrants AskUserQuestion.
    """
    text = (prompt or "").strip()
    base = defaults or SearchCriteria()
    limit_match = _LIMIT_RE.search(text)
    # Prefer counts near "find N" / "top N" phrasing; fall back to first number 5–100
    limit = base.limit
    find_limit = re.search(r"(?i)\b(?:find|return|get|need|top)\s+(\d{1,3})\b", text)
    if find_limit:
        limit = max(1, min(300, int(find_limit.group(1))))
    elif limit_match:
        n = int(limit_match.group(1))
        if 5 <= n <= 300:
            limit = n

    freshness = base.freshness_days
    fresh_m = _FRESH_RE.search(text)
    if fresh_m:
        freshness = max(1, min(365, int(fresh_m.group(1))))
    elif re.search(r"(?i)\b(recent|current|active|now)\b", text):
        freshness = min(freshness, 21)

    budget = base.budget_or_salary
    budget_m = _BUDGET_RE.search(text)
    if budget_m:
        budget = budget_m.group(1).strip()

    excluded_companies: list[str] = list(base.excluded_companies)
    for m in _EXCLUDE_COMPANY_RE.finditer(text):
        name = m.group(1).strip(" .,")
        if name and name.lower() not in {c.lower() for c in excluded_companies}:
            excluded_companies.append(name)

    excluded_sources: list[str] = list(base.excluded_sources)
    src_m = _EXCLUDE_SOURCE_RE.search(text)
    if src_m:
        for part in re.split(r"[,/\s]+", src_m.group(1)):
            part = part.strip().lower()
            if part and part not in excluded_sources:
                excluded_sources.append(part)

    modes = _extract_discovery_modes(text) if text else list(base.discovery_modes)
    lead_types = _extract_lead_types(text)
    if "agency" in modes and lead_types == ["all"]:
        lead_types = ["client", "freelance", "contract"]
    if "radar" in modes and "client" not in lead_types and "all" not in lead_types:
        lead_types = list(dict.fromkeys([*lead_types, "client"]))

    return SearchCriteria(
        lead_types=lead_types,
        technologies=_extract_technologies(text),
        industries=_extract_industries(text),
        geographies=_extract_geographies(text),
        workplace=_extract_workplace(text),
        budget_or_salary=budget,
        limit=limit,
        freshness_days=freshness,
        require_sponsorship=bool(
            re.search(r"(?i)\b(visa|sponsorship|sponsor)\b", text)
        ),
        require_relocation=bool(re.search(r"(?i)\brelocati", text)),
        excluded_sources=excluded_sources,
        excluded_companies=excluded_companies,
        excluded_lead_ids=list(base.excluded_lead_ids),
        discovery_modes=modes,
        query_text=" ".join(_extract_technologies(text)[:6]),
        raw_prompt=text,
    )


def needs_clarification(criteria: SearchCriteria) -> Optional[str]:
    """Return a short clarification question only when an essential detail is missing."""
    if not criteria.raw_prompt or len(criteria.raw_prompt.strip()) < 8:
        return (
            "What kind of leads do you want (clients, freelance projects, contracts, "
            "full-time jobs), and which technologies or markets should I prioritize?"
        )
    return None
