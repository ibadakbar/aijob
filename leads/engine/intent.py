"""Classify buying/hiring intent from evidence — never invent demand."""

from __future__ import annotations

import re
from typing import Optional

from .model import IntentClass
from .sanitize import sanitize_text

_EXPLICIT_PATTERNS = [
    re.compile(r"(?i)\b(we(?:'re| are)?\s+(?:hiring|looking for|seeking)|now hiring)\b"),
    re.compile(r"(?i)\b(apply (?:now|today|here)|job opening|open (?:role|position))\b"),
    re.compile(r"(?i)\b(contract(?:or)?|freelance(?:r)?)\s+(?:developer|engineer|role|position|needed|wanted)\b"),
    re.compile(r"(?i)\b(?:need(?:ed)?|looking for|seeking)\s+(?:a\s+)?(?:react|next\.?js|full[-\s]?stack|node|frontend|front-end)\b"),
    re.compile(r"(?i)\b(rfp|project brief|statement of work|deliverables)\b"),
    re.compile(r"(?i)\b(subcontract(?:or|ing)?|overflow (?:work|capacity)|external (?:engineer|developer))\b"),
    re.compile(r"(?i)\b(partner with|technical (?:co-?founder|partner)|development partner)\b"),
]

_STRONG_PATTERNS = [
    re.compile(r"(?i)\b(recent(?:ly)? (?:funded|raised|closed)|series [abc]|seed round)\b"),
    re.compile(r"(?i)\b(launched|launching|shipping|mvp|product launch)\b"),
    re.compile(r"(?i)\b(engineering (?:team|capacity)|scaling (?:the )?(?:product|platform|engineering))\b"),
    re.compile(r"(?i)\b(tech debt|rebuild|moderni[sz]e|legacy (?:stack|system))\b"),
]


def classify_intent(
    *,
    title: str,
    description: str,
    lead_type_hint: Optional[str] = None,
    source_kind: str = "job_listing",
) -> tuple[IntentClass, str]:
    """Return intent class and a short evidence-based explanation.

    `source_kind`:
      - job_listing / project_listing / hiring_post → active request surfaces
      - funding_news / launch_news → signals only unless text also has explicit ask
      - directory / company_profile → potential fit at best
    """
    blob = sanitize_text(f"{title}\n{description}", max_len=6000)
    explicit_hits = [p.pattern for p in _EXPLICIT_PATTERNS if p.search(blob)]
    strong_hits = [p.pattern for p in _STRONG_PATTERNS if p.search(blob)]

    if source_kind in ("job_listing", "project_listing", "hiring_post"):
        # An active listing is itself explicit demand for that role/project.
        if explicit_hits or source_kind in ("job_listing", "project_listing"):
            reason = (
                f"Active {source_kind.replace('_', ' ')} with public application/project URL"
            )
            if explicit_hits:
                reason += "; text contains an explicit hiring/project request"
            if lead_type_hint:
                reason += f" (typed as {lead_type_hint})"
            return "EXPLICIT_DEMAND", reason

    if explicit_hits:
        return (
            "EXPLICIT_DEMAND",
            "Public text explicitly requests developers, partners, or subcontractors",
        )

    if strong_hits or source_kind in ("funding_news", "launch_news"):
        return (
            "STRONG_SIGNAL",
            "Credible recent activity (funding, launch, or scaling language) without an "
            "explicit request for your services",
        )

    return (
        "POTENTIAL_FIT",
        "Business could benefit from software services, but no current buying/hiring "
        "intent was established from public evidence",
    )
