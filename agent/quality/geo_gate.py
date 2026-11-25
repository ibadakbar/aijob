"""Geography hard filters for opportunity discovery.

- Drop India-based / India-primary listings (user preference).
- Target markets include New Zealand and other profile geos.
"""

from __future__ import annotations

import re
from typing import Iterable

from agent.models.opportunity import OpportunityRecord

# Markets the agent should hunt into (aligned with CLAUDE.md / preferences)
TARGET_MARKETS: tuple[str, ...] = (
    "Germany",
    "Netherlands",
    "United Kingdom",
    "Ireland",
    "Australia",
    "New Zealand",
    "Canada",
    "United States",
    "Sweden",
    "Finland",
    "Denmark",
    "Norway",
    "Belgium",
    "Czechia",
    "Singapore",
    "UAE",
    "Saudi Arabia",
    "Qatar",
    "Switzerland",
    "Pakistan",
    "Europe",
    "Worldwide remote",
)

# India + common city / region markers (word-boundary safe)
_INDIA_MARKERS = re.compile(
    r"(?i)(?<![a-z])("
    r"india|indian|"
    r"in\s*-\s*only|based in india|india only|india\-only|"
    r"bangalore|bengaluru|mumbai|hyderabad|chennai|pune|noida|"
    r"gurgaon|gurugram|new delhi|delhi ncr|kolkata|ahmedabad|"
    r"jaipur|kochi|trivandrum|thiruvananthapuram|coimbatore|"
    r"indore|chandigarh|lucknow|bhopal|nagpur|"
    r"karnataka|maharashtra|tamil nadu|telangana|andhra pradesh|"
    r"uttar pradesh|west bengal|gujarat|rajasthan|kerala"
    r")(?![a-z])"
)

# Avoid false positives: Indonesia, Indiana, Indianapolis
_INDIA_FALSE_POSITIVE = re.compile(
    r"(?i)\b(indonesia|indonesian|indiana|indianapolis|indianeers)\b"
)


def _blob(rec: OpportunityRecord) -> str:
    return " ".join(
        [
            str(rec.country or ""),
            str(rec.location or ""),
            str(rec.role_or_title or ""),
            str(rec.description or ""),
            str(rec.evidence or ""),
            str(rec.notes or ""),
            str(rec.international_eligibility or ""),
        ]
    )


def is_india_listing(rec: OpportunityRecord) -> bool:
    """True when the role is India-based / India-primary (not mere passing mention)."""
    country = (rec.country or "").strip().upper()
    if country in ("IN", "IND", "INDIA"):
        return True

    loc = (rec.location or "").strip()
    if loc and _INDIA_MARKERS.search(loc) and not _INDIA_FALSE_POSITIVE.search(loc):
        return True

    blob = _blob(rec)
    if _INDIA_FALSE_POSITIVE.search(blob):
        # Still drop if country/location explicitly India
        if loc and _INDIA_MARKERS.search(loc):
            return True
        return False

    # Strong India-primary phrases in title/location/description head
    head = f"{rec.country} {rec.location} {rec.role_or_title} {(rec.description or '')[:400]}"
    if re.search(
        r"(?i)\b(india[\s\-]?only|based in india|hiring in india|"
        r"india applicants?|india location|remote[\s\-]?india|"
        r"work from india|wfH india|india office)\b",
        head,
    ):
        return True

    # Location field empty but evidence/notes scream India city as workplace
    if loc and _INDIA_MARKERS.search(loc):
        return True

    return False


def geo_drop_reason(rec: OpportunityRecord) -> str:
    """Return drop reason if geo-blocked, else empty string."""
    if is_india_listing(rec):
        return "blocked_geo_india"
    return ""


def markets_prompt_fragment(markets: Iterable[str] | None = None) -> str:
    """Short clause for discovery prompts."""
    names = list(markets or TARGET_MARKETS)
    # Keep prompt readable
    focus = [
        m
        for m in names
        if m
        not in (
            "Europe",
            "Worldwide remote",
        )
    ]
    joined = ", ".join(focus[:14])
    return (
        f"Target markets: {joined} (and remote-international into those). "
        "Exclude India / India-only / Bangalore / Mumbai / Hyderabad roles."
    )
