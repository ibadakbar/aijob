"""Prompt → structured research mission / search plan (discovery only)."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Optional

from .criteria import parse_prompt
from .model import SearchCriteria
from .sources import LIVE_SOURCES, STUB_SOURCES

OpportunityKind = Literal[
    "full_time",
    "freelance",
    "contract",
    "direct_client",
    "agency_partner",
    "hidden_signal",
]

ALL_LIVE = list(LIVE_SOURCES.keys())
DEFAULT_JOB_SOURCES = ["remotive", "arbeitnow", "greenhouse", "ashby", "lever"]
# Full public arsenal for "find leads" / worldwide missions (no stubs).
WORLD_LEAD_SOURCES = [
    "remotive",
    "arbeitnow",
    "greenhouse",
    "ashby",
    "lever",
    "ycombinator",
]


@dataclass
class SearchPlan:
    """Executable plan derived from one natural-language research prompt."""

    prompt: str
    criteria: SearchCriteria
    opportunity_kinds: list[OpportunityKind] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    sources_not_in_scope: list[str] = field(default_factory=list)
    min_verification: str = "partially_verified"
    require_published_email: bool = False
    require_salary: bool = False
    max_results: int = 20
    freshness_days: int = 30
    notes: list[str] = field(default_factory=list)
    claim: str = (
        "Partial worldwide research over configured public adapters - "
        "not a claim that the entire internet was searched."
    )

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["criteria"] = self.criteria.to_dict()
        return d


def _kinds_from_prompt(text: str, criteria: SearchCriteria) -> list[OpportunityKind]:
    lower = text.lower()
    kinds: list[OpportunityKind] = []
    if re.search(r"(?i)\b(full[-\s]?time|permanent|fte|staff engineer|software engineer job)\b", lower):
        kinds.append("full_time")
    if re.search(r"(?i)\b(freelance|gig|project brief|mvp)\b", lower):
        kinds.append("freelance")
    if re.search(r"(?i)\b(contract|contractor|staff[-\s]?aug)\b", lower):
        kinds.append("contract")
    if re.search(
        r"(?i)\b(direct client|companies that need|business(?:es)? seeking|"
        r"need(?:s|ing)? developers?|buying intent)\b",
        lower,
    ):
        kinds.append("direct_client")
    if re.search(
        r"(?i)\b(agency|agencies|subcontract|white-?label|overflow|partner)\b",
        lower,
    ):
        kinds.append("agency_partner")
    if re.search(
        r"(?i)\b(hidden|procurement|rfp|announcement|career[-\s]?page|beyond job board)\b",
        lower,
    ):
        kinds.append("hidden_signal")
    if not kinds:
        # Infer from lead_types
        for lt in criteria.lead_types:
            if lt == "full_time":
                kinds.append("full_time")
            elif lt == "freelance":
                kinds.append("freelance")
            elif lt == "contract":
                kinds.append("contract")
            elif lt == "client":
                kinds.append("direct_client")
            elif lt == "all":
                kinds.extend(["full_time", "freelance", "contract"])
        if "agency" in (criteria.discovery_modes or []):
            kinds.append("agency_partner")
        if "radar" in (criteria.discovery_modes or []):
            kinds.append("hidden_signal")
    # unique
    out: list[OpportunityKind] = []
    for k in kinds:
        if k not in out:
            out.append(k)
    return out or ["full_time"]


def _is_world_mission(text: str) -> bool:
    """Vague 'find leads' / worldwide prompts → full public arsenal."""
    lower = (text or "").lower().strip()
    if not lower:
        return True
    if re.search(
        r"(?i)\b("
        r"find(?:\s+me)?\s+leads?|today'?s?\s+leads?|leads?\s+today|"
        r"world(?:wide)?|entire\s+world|global|top\s*notch|best\s+leads?|"
        r"warm\s+leads?|with\s+email|reply(?:able)?|super\s*power|"
        r"all\s+sources|full\s+arsenal"
        r")\b",
        lower,
    ):
        return True
    # Short prompts like "leads" / "find clients" still mean the full arsenal
    return len(lower.split()) <= 4 and bool(
        re.search(r"(?i)\b(leads?|clients?|contracts?|freelance|hiring)\b", lower)
    )


def _sources_for(kinds: list[OpportunityKind], text: str) -> list[str]:
    lower = text.lower()
    sources: list[str] = []
    if _is_world_mission(text):
        sources.extend(WORLD_LEAD_SOURCES)
    if any(k in ("full_time", "contract", "freelance") for k in kinds):
        for s in DEFAULT_JOB_SOURCES:
            if s not in sources:
                sources.append(s)
    if "agency_partner" in kinds or "direct_client" in kinds or "hidden_signal" in kinds:
        # Public boards still help; agent WebSearch covers the rest.
        for s in ("remotive", "arbeitnow", "ycombinator"):
            if s not in sources:
                sources.append(s)
    # Y Combinator directory: startups + published founder LinkedIn (no private emails)
    if re.search(
        r"(?i)\b(y\s*combinator|\byc\b|co-?founders?|yc[- ]?backed|yc startups?|"
        r"funded startups?|startup founders?)\b",
        lower,
    ):
        if "ycombinator" not in sources:
            sources.append("ycombinator")
    if re.search(r"(?i)\b(ycombinator|yc)\s+only\b", lower):
        sources = ["ycombinator"]
    if re.search(r"(?i)\bfixture\b", lower):
        sources = ["fixture"]
    if re.search(r"(?i)\bremotive only\b", lower):
        sources = ["remotive"]
    # Drop unknown / alias duplicate (yc shares adapter with ycombinator)
    deduped: list[str] = []
    for s in sources:
        if s not in LIVE_SOURCES:
            continue
        # Prefer canonical name over alias
        canon = "ycombinator" if s == "yc" else s
        if canon not in deduped:
            deduped.append(canon)
    return deduped or list(WORLD_LEAD_SOURCES)


def plan_mission(prompt: str, *, criteria: Optional[SearchCriteria] = None) -> SearchPlan:
    """Convert one prompt into a structured research plan with sensible defaults."""
    text = (prompt or "").strip()
    crit = criteria or parse_prompt(text)
    world = _is_world_mission(text)
    # Allow up to 300 results for worldwide missions
    find_limit = re.search(r"(?i)\b(?:find|return|get|need|top)\s+(\d{1,3})\b", text)
    if find_limit:
        crit.limit = max(1, min(300, int(find_limit.group(1))))
    elif world:
        crit.limit = max(crit.limit, 40)
    elif crit.limit < 20 and len(text) > 40:
        crit.limit = 50

    if world and crit.freshness_days > 21:
        crit.freshness_days = 21
    if world and (not crit.geographies or crit.geographies == ["Remote"]):
        # Prefer remote-capable worldwide search; agent filters to profile markets.
        if "Remote" not in crit.geographies:
            crit.geographies = list(crit.geographies) + ["Remote"]

    # World missions hunt contracts + freelance + full-time, not jobs-only.
    if world and set(crit.lead_types) <= {"full_time", "all"}:
        crit.lead_types = ["freelance", "contract", "full_time", "client"]
    if world and "radar" not in (crit.discovery_modes or []):
        modes = list(crit.discovery_modes or ["jobs"])
        if "radar" not in modes:
            modes.append("radar")
        crit.discovery_modes = modes  # type: ignore[assignment]

    kinds = _kinds_from_prompt(text, crit)
    if world:
        for k in ("freelance", "contract", "full_time", "direct_client", "hidden_signal"):
            if k not in kinds:
                kinds.append(k)  # type: ignore[arg-type]
    sources = _sources_for(kinds, text)
    require_email = bool(
        re.search(
            r"(?i)\b(published email|with email|contact email|business email|phone|"
            r"warm|reply|cold email|directly contact)\b",
            text,
        )
    ) or world  # world default: prefer published contacts in ranking/presentation
    require_salary = bool(
        re.search(r"(?i)\b(salary|compensation|budget|pay range|rate)\b", text)
    )
    notes: list[str] = []
    if world:
        notes.append(
            "WORLD LEADS mode: Remotive+Arbeitnow+ATS+YC in parallel; "
            "rank Tier A (published email) > B (founder LinkedIn) > C (apply URL); "
            "demote cold marketplace / no-demand rows. Agent must also run LinkedIn "
            "freelance/contract + visa/relocation scrape and WebSearch contact enrichment."
        )
    if require_email:
        notes.append(
            "Email/phone preferred when published; leads without contacts are still kept "
            "and marked missing_information — never invent addresses. "
            "Present Tier A/B first; park Tier C/D as secondary."
        )
    if "direct_client" in kinds or "hidden_signal" in kinds:
        notes.append(
            "Direct-client / hidden signals need corroborating public evidence; "
            "funding or a website alone is not confirmed demand."
        )
    if any(k in kinds for k in ("full_time", "contract")):
        notes.append(
            "ATS adapters (Greenhouse/Ashby/Lever) use curated public board tokens only."
        )

    not_in_scope = sorted(
        set(STUB_SOURCES.keys())
        | {s for s in ALL_LIVE if s not in sources}
    )

    return SearchPlan(
        prompt=text,
        criteria=crit,
        opportunity_kinds=kinds,
        sources=sources,
        sources_not_in_scope=not_in_scope,
        min_verification="partially_verified",
        require_published_email=require_email,
        require_salary=require_salary,
        max_results=crit.limit,
        freshness_days=crit.freshness_days,
        notes=notes,
        claim=(
            "Worldwide public-adapter sweep (Remotive, Arbeitnow, curated ATS, YC) "
            "plus agent LinkedIn/WebSearch enrichment — not a claim that every site "
            "on the internet was searched."
            if world
            else (
                "Partial worldwide research over configured public adapters - "
                "not a claim that the entire internet was searched."
            )
        ),
    )
