"""Sponsorship / relocation classification from listing text + optional registry hints.

Never upgrades a registry hit alone to verified_in_listing for a vacancy.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Iterable, Optional

from .model import SponsorshipEvidence, SponsorshipResult

# Explicit positive offers (listing-level)
_POSITIVE = [
    (r"visa\s+sponsorship\s+(is\s+)?available", "visa sponsorship available"),
    (r"we\s+(do\s+)?sponsor\s+(work\s+)?visas?", "we sponsor visas"),
    (r"sponsorship\s+(is\s+)?available", "sponsorship available"),
    (r"employer[\s-]?sponsored\s+visa", "employer-sponsored visa"),
    (r"will\s+sponsor\s+(a\s+)?(work\s+)?(visa|permit)", "will sponsor visa/permit"),
    (r"skilled\s+worker\s+visa", "skilled worker visa"),
    (r"eu\s+blue\s+card", "EU Blue Card"),
    (r"blue\s+card\s+(eligible|sponsorship|support)", "Blue Card support"),
    (r"relocation\s+(assistance|support|package|help)", "relocation support"),
    (r"international\s+applicants?\s+(are\s+)?welcome", "international applicants welcome"),
    (r"visa\s+assistance", "visa assistance"),
    (r"work\s+permit\s+sponsorship", "work permit sponsorship"),
    (r"iqama\s+(provided|sponsorship|available)", "Iqama provided"),
    (r"visa\s+provided", "visa provided"),
]

# Explicit negatives
_NEGATIVE = [
    (r"no\s+visa\s+sponsorship", "no visa sponsorship"),
    (r"cannot\s+sponsor", "cannot sponsor"),
    (r"unable\s+to\s+sponsor", "unable to sponsor"),
    (r"sponsorship\s+(is\s+)?not\s+available", "sponsorship not available"),
    (r"must\s+have\s+(existing\s+)?(work\s+)?(authorization|authorisation|rights|permit)", "must have existing work authorization"),
    (r"must\s+be\s+(a\s+)?(citizen|permanent\s+resident)", "must be citizen/PR"),
    (r"australian\s+citizenship\s+(is\s+)?required", "Australian citizenship required"),
    (r"only\s+candidates\s+with\s+(valid\s+)?work\s+(authorization|authorisation|rights)", "only with work rights"),
    (r"applicants\s+must\s+already\s+be\s+eligible\s+to\s+work", "must already be eligible"),
    (r"no\s+sponsorship\s+(will\s+be|is)\s+(provided|offered|available)", "no sponsorship offered"),
]

# Ambiguous / weaker positives
_POSSIBLE = [
    (r"visa\s+sponsorship", "visa sponsorship (unqualified)"),
    (r"\bsponsorship\b", "sponsorship (unqualified)"),
    (r"relocation", "relocation (unqualified)"),
    (r"work\s+permit", "work permit (unqualified)"),
    (r"open\s+to\s+international", "open to international"),
]


def _excerpt_around(text: str, match: re.Match[str], radius: int = 120) -> str:
    start = max(0, match.start() - radius)
    end = min(len(text), match.end() + radius)
    chunk = text[start:end].replace("\n", " ").strip()
    return re.sub(r"\s+", " ", chunk)


def _scan(patterns: Iterable[tuple[str, str]], text: str, url: str) -> list[SponsorshipEvidence]:
    found: list[SponsorshipEvidence] = []
    for pattern, label in patterns:
        for m in re.finditer(pattern, text, flags=re.IGNORECASE):
            found.append(
                SponsorshipEvidence(
                    excerpt=_excerpt_around(text, m),
                    source_url=url,
                    pattern=label,
                )
            )
            break  # one hit per pattern is enough
    return found


def classify_sponsorship(
    description: str,
    *,
    source_url: str,
    source_hint: Optional[str] = None,
    company_on_sponsor_registry: bool = False,
    registry_name: Optional[str] = None,
) -> SponsorshipResult:
    """Classify sponsorship for one vacancy from its listing text (+ optional hints)."""
    text = description or ""
    today = date.today().isoformat()

    negatives = _scan(_NEGATIVE, text, source_url)
    if negatives:
        return SponsorshipResult(
            classification="not_available",
            confidence=0.92,
            evidence=negatives[:3],
            relocation_support=False if re.search(r"no\s+relocation", text, re.I) else None,
            verified_at=today,
            notes="Explicit exclusion or existing-authorization requirement in listing.",
        )

    positives = _scan(_POSITIVE, text, source_url)
    relocation = bool(re.search(r"relocation\s+(assistance|support|package|help)", text, re.I))
    if positives:
        # If both strong positive and a soft "must have rights" — already handled above.
        conf = 0.88 if any("available" in e.pattern or "sponsor" in e.pattern for e in positives) else 0.8
        return SponsorshipResult(
            classification="verified_in_listing",
            confidence=conf,
            evidence=positives[:4],
            relocation_support=True if relocation else None,
            verified_at=today,
            notes="Explicit sponsorship/relocation language in the job listing.",
        )

    possibles = _scan(_POSSIBLE, text, source_url)
    evidence = list(possibles[:3])
    notes = []
    classification = "unknown"
    confidence = 0.15

    if source_hint == "arbeitnow_visa_filter":
        evidence.append(
            SponsorshipEvidence(
                excerpt="Returned by Arbeitnow API with visa_sponsorship=true (board-level filter; confirm in listing).",
                source_url=source_url,
                pattern="arbeitnow visa_sponsorship filter",
            )
        )
        classification = "possible"
        confidence = 0.55
        notes.append("Arbeitnow tagged this posting under its visa-sponsorship filter.")

    if company_on_sponsor_registry:
        evidence.append(
            SponsorshipEvidence(
                excerpt=f"Company appears on {registry_name or 'a licensed sponsor registry'} (licence ≠ vacancy offer).",
                source_url=source_url,
                pattern="sponsor registry match",
            )
        )
        if classification in ("unknown", "possible"):
            classification = "sponsor_company_only"
            confidence = max(confidence, 0.45)
        notes.append("Registry match only — vacancy sponsorship unconfirmed.")

    if possibles and classification == "unknown":
        classification = "possible"
        confidence = 0.4
        notes.append("Ambiguous sponsorship-related wording.")

    if not evidence and classification == "unknown":
        return SponsorshipResult(
            classification="unknown",
            confidence=0.1,
            evidence=[],
            relocation_support=None,
            verified_at=today,
            notes="Insufficient evidence in listing text.",
        )

    return SponsorshipResult(
        classification=classification,  # type: ignore[arg-type]
        confidence=confidence,
        evidence=evidence[:5],
        relocation_support=True if relocation else None,
        verified_at=today,
        notes=" ".join(notes),
    )
