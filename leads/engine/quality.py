"""Reply-ability quality tiers — prefer warm, reachable leads over cold ATS spam."""

from __future__ import annotations

from typing import Literal, Optional

from .model import Lead

QualityTier = Literal["A", "B", "C", "D"]

# Companies / patterns that rarely produce replies for cold outreach.
_COLD_PATTERNS = (
    "lemon.io",
    "toptal",
    "upwork",
    "fiverr",
    "remoteok",
    "we work remotely",
)


def has_published_email(lead: Lead) -> bool:
    for c in lead.contacts or []:
        if c.channel_type == "email" and c.verification_status in (
            "published_on_official_source",
            "domain_mx_present",
        ):
            return True
    return False


def has_founder_linkedin(lead: Lead) -> bool:
    founders = (lead.raw or {}).get("founders") or []
    if any(isinstance(f, dict) and f.get("linkedin_url") for f in founders):
        return True
    for c in lead.contacts or []:
        if (
            c.channel_type == "professional_profile"
            and c.verification_status == "published_on_official_source"
            and "linkedin.com/in/" in (c.value or "").lower()
        ):
            return True
    return False


def is_likely_cold_marketplace(lead: Lead) -> bool:
    blob = f"{lead.company} {lead.source} {lead.url}".lower()
    return any(p in blob for p in _COLD_PATTERNS)


def quality_tier(lead: Lead) -> QualityTier:
    """A = reply-able warm · B = named founder path · C = apply URL · D = cold/skip."""
    demand = lead.intent == "EXPLICIT_DEMAND"
    email = has_published_email(lead)
    founder_li = has_founder_linkedin(lead)
    proven = bool(lead.opportunity and lead.opportunity.demand_proven)
    hiring = bool((lead.raw or {}).get("isHiring")) or demand

    if is_likely_cold_marketplace(lead) and not email:
        return "D"
    if lead.intent == "POTENTIAL_FIT" and not proven and not hiring and not email:
        return "D"
    if email and (demand or hiring or proven):
        return "A"
    if email:
        return "A"
    if founder_li and (demand or hiring):
        return "B"
    if founder_li:
        return "B"
    if demand or hiring:
        return "C"
    return "D"


def tier_label(tier: QualityTier) -> str:
    return {
        "A": "A · warm (published email)",
        "B": "B · founder LinkedIn path",
        "C": "C · apply URL only",
        "D": "D · cold / skip",
    }[tier]


def next_action_for_tier(lead: Lead, tier: Optional[QualityTier] = None) -> str:
    t = tier or quality_tier(lead)
    if t == "A":
        return "Email published address (draft only — send_approved false)"
    if t == "B":
        return "LinkedIn message to published founder profile"
    if t == "C":
        return "Apply via ATS/URL (not cold email — no published mailbox)"
    return "Skip or park — weak demand / no reachable contact"


__all__ = [
    "QualityTier",
    "quality_tier",
    "tier_label",
    "next_action_for_tier",
    "has_published_email",
    "has_founder_linkedin",
    "is_likely_cold_marketplace",
]
