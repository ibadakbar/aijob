"""Agency partnership finder: white-label / overflow capacity, not one-off freelance pitches."""

from __future__ import annotations

import re
from typing import Optional

from .model import AgencyPartnership, Lead, PartnershipFit, SearchCriteria
from .sanitize import sanitize_text

_AGENCY_MARKERS = re.compile(
    r"(?i)\b(agency|agencies|studio|digital (?:shop|collective)|consultancy|"
    r"consulting firm|white-?label|web design (?:agency|studio)|"
    r"creative (?:agency|studio)|software (?:consultancy|consulting))\b"
)

_FIT_PATTERNS: list[tuple[PartnershipFit, re.Pattern[str], str]] = [
    (
        "white_label",
        re.compile(
            r"(?i)\b(white-?label|white label partner|development partner|"
            r"technical partner|overflow partner)\b"
        ),
        "Publicly seeking white-label or technical partners",
    ),
    (
        "overflow_capacity",
        re.compile(
            r"(?i)\b(overflow|extra capacity|bandwidth|subcontract|"
            r"contractor(?:s)? needed|freelance (?:react|next|developer|engineer)|"
            r"need(?:ed)? (?:a )?(?:react|next|frontend|full[-\s]?stack))\b"
        ),
        "Agency publicly seeking contractors or overflow engineering capacity",
    ),
    (
        "design_only_gap",
        re.compile(
            r"(?i)\b(design(?:-|\s)?(?:first|led|focused)|ui/?ux|branding|"
            r"visual design)\b.{0,80}\b"
            r"(limited|no|without|outsourc(?:e|ing)|partner).{0,40}\b"
            r"(dev(?:elopment)?|engineer|build|implementation)\b|"
            r"\b(design agency|creative studio).{0,60}\b"
            r"(partner|outsource|need).{0,40}\b(dev|engineer|react|next)\b"
        ),
        "Design-led agency with limited in-house development",
    ),
    (
        "consultancy_contract",
        re.compile(
            r"(?i)\b(software consultanc(?:y|ies)|digital consultanc(?:y|ies))\b|"
            r"\b(contract|contractor|freelance).{0,40}\b"
            r"(react|next\.?js|full[-\s]?stack|frontend)\b"
        ),
        "Consultancy with relevant contract / React–Next openings",
    ),
]


def classify_agency_partnership(
    *,
    title: str,
    description: str,
    company: str = "",
    lead_type: str = "",
) -> AgencyPartnership:
    blob = sanitize_text(f"{company}\n{title}\n{description}", max_len=8000)
    is_agency = bool(_AGENCY_MARKERS.search(blob))
    fit: PartnershipFit = "none"
    reasons: list[str] = []
    pitch_angle = ""

    for partnership_fit, pattern, reason in _FIT_PATTERNS:
        if pattern.search(blob):
            fit = partnership_fit
            reasons.append(reason)
            break

    if not is_agency and fit == "none":
        return AgencyPartnership()

    if not is_agency and fit != "none":
        is_agency = True
        reasons.append("Partnership language present even if 'agency' was not named")

    if fit == "none" and is_agency:
        # Soft signal: agency without proven capacity gap stays POTENTIAL partnership.
        reasons.append(
            "Appears to be a digital/creative agency, but no public contractor or "
            "white-label ask was found"
        )
        pitch_angle = (
            "Only warm-intro if a public capacity gap appears; do not send a generic "
            "freelance pitch to every agency."
        )
        return AgencyPartnership(
            is_agency=True,
            partnership_fit="none",
            pitch_angle=pitch_angle,
            reasons=reasons,
        )

    pitch_map = {
        "white_label": (
            "Offer a white-label React/Next.js delivery partnership: you keep the "
            "client relationship; I ship the engineering under your brand."
        ),
        "overflow_capacity": (
            "Propose a standing overflow partnership for React/Next/TypeScript spikes "
            "so their team can take more client work without hiring full-time."
        ),
        "design_only_gap": (
            "Partner as the engineering arm for design-led builds: Figma-to-Next.js, "
            "CMS, and SaaS dashboards while they own UX and client strategy."
        ),
        "consultancy_contract": (
            "Pitch a recurring contract capacity relationship for React/Next.js "
            "product work, not a one-off freelance gig."
        ),
    }
    pitch_angle = pitch_map.get(fit, "")
    if lead_type in ("freelance", "contract", "client"):
        reasons.append(f"Lead type {lead_type} fits a partnership conversation")
    return AgencyPartnership(
        is_agency=True,
        partnership_fit=fit,
        pitch_angle=pitch_angle,
        reasons=reasons,
    )


def attach_partnership(lead: Lead, *, criteria: Optional[SearchCriteria] = None) -> AgencyPartnership:
    from .opportunity_radar import lead_text_blob

    partnership = classify_agency_partnership(
        title=lead.title,
        description=lead_text_blob(lead),
        company=lead.company,
        lead_type=lead.lead_type,
    )
    lead.partnership = partnership
    if partnership.is_agency and partnership.partnership_fit != "none":
        lead.recommended_service = partnership.pitch_angle or lead.recommended_service
        lead.next_action = (
            "Send a partnership-specific pitch (white-label / overflow), not a "
            "generic freelance proposal — after user approval."
        )
        if criteria and "agency" in (criteria.discovery_modes or []):
            lead.profile_match_reasons = list(
                dict.fromkeys(
                    lead.profile_match_reasons
                    + [f"agency partnership: {partnership.partnership_fit}"]
                    + partnership.reasons[:2]
                )
            )
    return partnership


def wants_agency(criteria: SearchCriteria) -> bool:
    return "agency" in (criteria.discovery_modes or [])


def partnership_outreach_body(
    lead: Lead,
    *,
    candidate_name: str = "Ibad Akbar",
) -> str:
    """Partnership-specific email body. Never claims fabricated prior work with them."""
    p = lead.partnership
    if p is None or not p.is_agency or p.partnership_fit == "none":
        return ""
    evidence = ""
    if lead.evidence:
        evidence = lead.evidence[0].summary or lead.evidence[0].excerpt or lead.title
    else:
        evidence = lead.title
    angle = p.pitch_angle or "a React/Next.js partnership for overflow delivery"
    return (
        f"Hi {lead.company} team,\n\n"
        f"I noticed your public note about “{evidence}”. "
        f"I am {candidate_name}, a full-stack engineer (React/Next.js/TypeScript/Node) "
        f"who partners with agencies on delivery rather than competing for their clients.\n\n"
        f"{angle}\n\n"
        f"If useful, I can share a short partnership one-pager and recent SaaS/product "
        f"work. No obligation — happy to stay on a preferred-vendor list for overflow.\n\n"
        f"Best regards,\n{candidate_name}"
    )
