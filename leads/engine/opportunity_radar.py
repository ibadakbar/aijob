"""Opportunity radar: demand-creating events need corroborating evidence."""

from __future__ import annotations

import re
from typing import Optional

from .model import Lead, OpportunityEvent, OpportunityEventType, SearchCriteria
from .sanitize import sanitize_text

_EVENT_PATTERNS: list[tuple[OpportunityEventType, re.Pattern[str], str]] = [
    (
        "funding",
        re.compile(
            r"(?i)\b(raised|closed|secured)\b.{0,40}\b(seed|series [a-d]|pre-seed|"
            r"funding|round|investment)\b|\b(seed|series [a-d])\s+round\b|"
            r"\brecent(?:ly)?\s+funded\b"
        ),
        "Recently funded / raised capital",
    ),
    (
        "saas_launch",
        re.compile(
            r"(?i)\b(launched|launching|announc(?:ed|ing)|shipping)\b.{0,40}\b"
            r"(saas|product|platform|mvp|app)\b|\b(product launch|went live|public beta)\b"
        ),
        "Newly launched or shipping SaaS / product",
    ),
    (
        "agency_client_win",
        re.compile(
            r"(?i)\b(won|selected|appointed|awarded)\b.{0,40}\b"
            r"(client|account|retainer|project)\b|\bnew client (?:win|wins|announcement)\b"
        ),
        "Agency announcing a new client win",
    ),
    (
        "eng_team_expansion",
        re.compile(
            r"(?i)\b(expand(?:ing|ed)?|grow(?:ing|th)?|scaling|doubl(?:e|ing))\b.{0,40}\b"
            r"(engineering|dev(?:elopment)?|product)\s+(team|org|headcount|capacity)\b|"
            r"\bhiring (?:more|additional) (?:engineers|developers)\b"
        ),
        "Company expanding its engineering team",
    ),
    (
        "tech_hiring",
        re.compile(
            r"(?i)\b(we(?:'re| are)?\s+(?:hiring|looking for|seeking)|now hiring|"
            r"open (?:role|position)|apply (?:now|today))\b.{0,80}\b"
            r"(react|next\.?js|typescript|node\.?js|full[-\s]?stack|frontend|front-end|"
            r"software engineer)\b|"
            r"\b(react|next\.?js|typescript|node\.?js)\b.{0,40}\b"
            r"(engineer|developer|role|position|hiring)\b"
        ),
        "Hiring for a technology matching the candidate stack",
    ),
]

_EXPLICIT_DEMAND = re.compile(
    r"(?i)\b(we(?:'re| are)?\s+(?:hiring|looking for|seeking)|now hiring|"
    r"open (?:role|position)|apply (?:now|today)|freelance(?:r)?|"
    r"contract(?:or)?|project brief|rfp|deliverables|"
    r"white-?label|subcontract)\b"
)
_BUDGET = re.compile(r"(?i)\b(budget|salary|compensation|\$\d|€\d|£\d|\d+\s*k\b)\b")
_CAREERS = re.compile(r"(?i)\b(careers? page|jobs? board|apply at|greenhouse|lever\.co|ashbyhq)\b")
_STACK = re.compile(
    r"(?i)\b(react|next\.?js|typescript|node\.?js|full[-\s]?stack|frontend|front-end)\b"
)


def detect_opportunity(
    *,
    title: str,
    description: str,
    source_kind: str = "",
    technologies: Optional[list[str]] = None,
) -> OpportunityEvent:
    """Detect a demand-creating event and whether corroboration proves demand.

    A funding announcement alone never sets ``demand_proven``.
    """
    blob = sanitize_text(f"{title}\n{description}", max_len=8000)
    event_type: OpportunityEventType = "none"
    summary = ""
    for etype, pattern, label in _EVENT_PATTERNS:
        matched = bool(pattern.search(blob))
        if not matched and etype == "funding" and source_kind == "funding_news":
            matched = True
        if not matched and etype == "saas_launch" and source_kind == "launch_news":
            matched = True
        if matched:
            event_type = etype
            summary = label
            break

    if event_type == "none":
        return OpportunityEvent(
            event_type="none",
            summary="",
            demand_proven=False,
            reason="No demand-creating event detected in the public text.",
        )

    corroborating: list[str] = []
    if _EXPLICIT_DEMAND.search(blob):
        corroborating.append("explicit_hiring_or_project_request")
    if _BUDGET.search(blob):
        corroborating.append("budget_or_compensation_stated")
    if _CAREERS.search(blob):
        corroborating.append("careers_or_application_path")
    if _STACK.search(blob):
        tech = [t.lower() for t in (technologies or [])]
        if not tech or any(t.replace(".", "") in blob.replace(".", "").lower() for t in tech):
            corroborating.append("stack_match_in_text")

    has_explicit = "explicit_hiring_or_project_request" in corroborating
    has_budget = "budget_or_compensation_stated" in corroborating
    alone_is_not_demand = event_type in ("funding", "saas_launch", "agency_client_win")

    if event_type == "tech_hiring" and has_explicit:
        demand_proven = True
        reason = (
            f"{summary}, and the text also contains an explicit hiring/project request "
            f"({', '.join(corroborating)})."
        )
    elif event_type == "eng_team_expansion" and (has_explicit or has_budget):
        demand_proven = True
        reason = f"{summary}, corroborated by hiring/budget evidence."
    elif alone_is_not_demand and not (has_explicit or has_budget):
        demand_proven = False
        reason = (
            f"{summary} was detected, but a funding/launch/client-win announcement "
            "alone does not prove buying intent. Need a hiring ask, project brief, "
            "or other corroborating demand signal before treating this as a lead."
        )
    elif alone_is_not_demand and (has_explicit or has_budget):
        demand_proven = True
        reason = (
            f"{summary}, plus corroborating demand evidence: "
            f"{', '.join(s for s in corroborating if s != 'stack_match_in_text')}."
        )
    else:
        demand_proven = has_explicit or has_budget
        reason = (
            f"{summary}. "
            + (
                f"Corroboration: {', '.join(corroborating)}."
                if corroborating
                else "No second demand signal found yet."
            )
        )

    return OpportunityEvent(
        event_type=event_type,
        summary=summary,
        corroborating_signals=corroborating,
        demand_proven=demand_proven,
        reason=reason,
    )


def lead_text_blob(lead: Lead) -> str:
    parts = [
        lead.title,
        lead.intent_explanation or "",
        lead.recommended_service or "",
        " ".join(lead.technical_requirements),
    ]
    for ev in lead.evidence:
        parts.append(ev.summary or "")
        parts.append(ev.excerpt or "")
    if isinstance(lead.raw, dict) and lead.raw.get("description"):
        parts.append(str(lead.raw["description"]))
    return " ".join(parts)


def attach_opportunity(lead: Lead, *, criteria: Optional[SearchCriteria] = None) -> OpportunityEvent:
    """Attach radar analysis to a lead and adjust risks / next action."""
    techs = list(lead.technical_requirements)
    if criteria and criteria.technologies:
        techs = list(dict.fromkeys(techs + list(criteria.technologies)))
    source_kind = ""
    if isinstance(lead.raw, dict):
        source_kind = str(lead.raw.get("source_kind") or "")
    event = detect_opportunity(
        title=lead.title,
        description=lead_text_blob(lead),
        source_kind=source_kind,
        technologies=techs,
    )
    lead.opportunity = event
    if event.event_type != "none" and not event.demand_proven:
        note = (
            "Opportunity radar: event without proven demand — keep as signal, "
            "not a qualified lead."
        )
        if note not in lead.risks:
            lead.risks.append(note)
        lead.next_action = (
            "Watch for a public hiring/project ask before outreach; "
            "funding alone is not enough."
        )
    elif event.demand_proven:
        lead.next_action = lead.next_action or (
            "Event is corroborated by demand evidence — review listing and preferred contact path."
        )
    return event


def wants_radar(criteria: SearchCriteria) -> bool:
    return "radar" in (criteria.discovery_modes or [])
