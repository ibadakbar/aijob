"""Contact-path intelligence: pick the most relevant public route into the org."""

from __future__ import annotations

import re
from typing import Optional

from .model import ContactChannel, ContactPathRole, Lead, PreferredContactPath
from .sanitize import sanitize_text

# Role cues that may appear next to a published name or email in public text.
# Role keywords use (?i:...); name capture stays case-sensitive Title Case so
# trailing words like "listed" are not swallowed into the person name.
_ROLE_PATTERNS: list[tuple[ContactPathRole, re.Pattern[str], str]] = [
    (
        "founder",
        re.compile(
            r"\b(?i:founder|co-?founder|ceo|owner)\b[:\s-]*"
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})?"
        ),
        "Founder/owner path fits a small startup decision on hiring or buying engineering help",
    ),
    (
        "engineering_manager",
        re.compile(
            r"\b(?i:engineering manager|eng(?:ineering)? lead|head of engineering|"
            r"vp engineering|cto|tech lead|hiring manager)\b[:\s-]*"
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})?"
        ),
        "Engineering manager / tech lead is the right path for a technical role discussion",
    ),
    (
        "recruiter",
        re.compile(
            r"\b(?i:recruiter|talent (?:partner|acquisition)|people partner|"
            r"recruiting)\b[:\s-]*"
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})?"
        ),
        "Recruiter / talent partner is the right path for a published vacancy",
    ),
    (
        "hiring_contact",
        re.compile(
            r"(?i)\b(contact|email|reach)\b.{0,20}"
            r"([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,24})"
        ),
        "Published hiring/project contact on the source",
    ),
]

_EXECUTIVE_AVOID = re.compile(
    r"(?i)\b(chief marketing officer|cmo|chief financial officer|cfo|"
    r"board member|investor relations|press@|media@)\b"
)


def _role_from_title(title: Optional[str]) -> ContactPathRole:
    t = (title or "").lower()
    if any(k in t for k in ("founder", "co-founder", "ceo", "owner")):
        return "founder"
    if any(
        k in t
        for k in (
            "engineering manager",
            "eng lead",
            "head of engineering",
            "vp engineering",
            "cto",
            "tech lead",
            "hiring manager",
        )
    ):
        return "engineering_manager"
    if any(k in t for k in ("recruiter", "talent", "people partner")):
        return "recruiter"
    return "unknown"


def _preferred_for_lead_context(lead: Lead) -> ContactPathRole:
    """Heuristic: who is most relevant for this opportunity type."""
    if lead.partnership and lead.partnership.is_agency and lead.partnership.partnership_fit != "none":
        return "founder"
    if lead.source in ("ycombinator", "yc") or (lead.raw or {}).get("founders"):
        return "founder"
    if lead.opportunity and lead.opportunity.event_type == "funding" and not lead.opportunity.demand_proven:
        return "founder"
    if lead.lead_type == "full_time":
        return "recruiter"
    if lead.lead_type in ("contract", "freelance"):
        return "engineering_manager"
    if lead.lead_type == "client":
        return "founder"
    return "application_form"


def choose_contact_path(lead: Lead) -> PreferredContactPath:
    """Pick the best *published* path. Never invent people or emails."""
    blob = sanitize_text(
        " ".join(
            [lead.title, lead.intent_explanation or ""]
            + [f"{e.summary} {e.excerpt}" for e in lead.evidence]
            + [str(lead.raw.get("description") or "")]
        ),
        max_len=8000,
    )
    desired = _preferred_for_lead_context(lead)
    avoid = ""
    if _EXECUTIVE_AVOID.search(blob):
        avoid = (
            "Ignore marketing/finance/press contacts for this opportunity — "
            "they are unlikely to own hiring or engineering purchasing."
        )

    # 1) Prefer published contacts that already have a relevant title/name.
    ranked: list[tuple[int, PreferredContactPath]] = []
    for contact in lead.contacts:
        if not contact.value and contact.channel_type == "unknown":
            continue
        if contact.channel_type == "email" and _EXECUTIVE_AVOID.search(
            f"{contact.title or ''} {contact.value}"
        ):
            continue
        role = _role_from_title(contact.title)
        if role == "unknown" and contact.channel_type == "email":
            # Infer soft role from mailbox local-part when published.
            local = contact.value.split("@", 1)[0].lower()
            if any(k in local for k in ("career", "job", "hire", "recruit", "talent")):
                role = "recruiter"
            elif any(k in local for k in ("founder", "ceo", "hello", "team", "partner")):
                role = "founder" if desired == "founder" else "hiring_contact"
            elif any(k in local for k in ("project", "eng", "dev", "tech")):
                role = "engineering_manager" if desired == "engineering_manager" else "hiring_contact"
            else:
                role = "hiring_contact"
        if contact.channel_type == "application_page":
            role = "application_form" if role == "unknown" else role
        if contact.channel_type == "contact_form":
            role = "application_form"

        relevance = _relevance(role, desired, lead)
        score = _score(role, desired, contact)
        ranked.append(
            (
                score,
                PreferredContactPath(
                    role=role if role != "unknown" else (
                        "application_form"
                        if contact.channel_type in ("application_page", "contact_form")
                        else "hiring_contact"
                    ),
                    channel_type=contact.channel_type,
                    value=contact.value,
                    name=contact.name,
                    title=contact.title,
                    source_url=contact.source_url or lead.url,
                    relevance=relevance,
                    avoid_reason=avoid,
                ),
            )
        )

    # 2) Text-mined role mentions (name only if literally present; never invent email).
    for role, pattern, why in _ROLE_PATTERNS:
        m = pattern.search(blob)
        if not m:
            continue
        name = None
        if m.lastindex and m.group(m.lastindex) and "@" not in (m.group(m.lastindex) or ""):
            maybe = m.group(m.lastindex)
            if maybe and maybe[0].isupper() and "http" not in maybe.lower():
                name = maybe.strip()
        path = PreferredContactPath(
            role=role,
            channel_type="hiring_post" if role != "hiring_contact" else "email",
            value="",
            name=name,
            title=role.replace("_", " "),
            source_url=lead.url,
            relevance=why,
            avoid_reason=avoid,
        )
        # Named role matching the desired path outranks a bare application form.
        boost = 4 if role == desired and name else (1 if role == desired else -1)
        ranked.append((_score(role, desired, None) + boost, path))

    if ranked:
        ranked.sort(key=lambda item: item[0], reverse=True)
        best = ranked[0][1]
        if not best.value:
            # Fall back to application/contact form URL already on the lead.
            for contact in lead.contacts:
                if contact.channel_type in ("application_page", "contact_form") and contact.value:
                    best.channel_type = contact.channel_type
                    best.value = contact.value
                    best.source_url = contact.source_url or lead.url
                    if best.role in ("unknown", "hiring_contact") and desired == "application_form":
                        best.role = "application_form"
                    best.relevance = (
                        best.relevance
                        + " Use the official application/contact URL; no private email was published."
                    ).strip()
                    break
        return best

    # 3) Last resort: official listing URL as application form.
    return PreferredContactPath(
        role="application_form",
        channel_type="application_page",
        value=lead.url,
        source_url=lead.url,
        relevance=(
            "No named hiring contact was published. Use the official application or "
            "project page rather than guessing a senior executive."
        ),
        avoid_reason=avoid
        or "Do not invent founder/CEO emails or cold-pitch unrelated executives.",
    )


def _relevance(role: ContactPathRole, desired: ContactPathRole, lead: Lead) -> str:
    if role == desired:
        mapping = {
            "founder": "Founder path matches a small-team buying/hiring decision",
            "engineering_manager": "Engineering manager path matches a technical delivery conversation",
            "recruiter": "Recruiter path matches a published vacancy process",
            "application_form": "Official application/contact form is the published route",
            "hiring_contact": "Published hiring/project contact on the source",
        }
        return mapping.get(role, "Relevant published contact")
    if role == "application_form":
        return (
            "Official application/contact form is available when a named "
            f"{desired.replace('_', ' ')} contact was not published"
        )
    if lead.partnership and lead.partnership.is_agency:
        return "Agency partnership outreach should go to delivery ownership, not a random executive"
    return f"Published {role.replace('_', ' ')}; preferred path for this lead type is {desired.replace('_', ' ')}"


def _score(
    role: ContactPathRole,
    desired: ContactPathRole,
    contact: Optional[ContactChannel],
) -> int:
    score = 0
    if role == desired:
        score += 5
    if role == "application_form":
        score += 2
    if contact and contact.channel_type == "email" and contact.value:
        score += 3
    if contact and contact.channel_type in ("application_page", "contact_form") and contact.value:
        score += 2
    if contact and contact.verification_status == "published_on_official_source":
        score += 1
    return score


def attach_contact_path(lead: Lead) -> PreferredContactPath:
    path = choose_contact_path(lead)
    lead.preferred_contact = path
    if path.relevance and path.relevance not in lead.profile_match_reasons:
        # Keep profile_match_reasons for skills; put contact note on next_action lightly.
        pass
    if path.role == "application_form" and not any(
        "application" in (lead.next_action or "").lower() for _ in [0]
    ):
        if "contact" not in (lead.next_action or "").lower():
            lead.next_action = (
                (lead.next_action + " " if lead.next_action else "")
                + f"Preferred path: official {path.channel_type} ({path.value or lead.url})."
            ).strip()
    return path
