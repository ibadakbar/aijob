"""Normalized job model for visa-aware discovery."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Optional

SponsorshipClass = Literal[
    "verified_in_listing",
    "sponsor_company_only",
    "possible",
    "not_available",
    "unknown",
]

Workplace = Literal["remote", "hybrid", "onsite", "unknown"]
JobStatus = Literal["open", "expired", "unknown"]


@dataclass
class SponsorshipEvidence:
    excerpt: str
    source_url: str
    pattern: str = ""


@dataclass
class SponsorshipResult:
    classification: SponsorshipClass
    confidence: float
    evidence: list[SponsorshipEvidence] = field(default_factory=list)
    relocation_support: Optional[bool] = None  # None = unknown
    verified_at: Optional[str] = None  # ISO date
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "classification": self.classification,
            "confidence": round(self.confidence, 3),
            "evidence": [asdict(e) for e in self.evidence],
            "relocation_support": self.relocation_support,
            "verified_at": self.verified_at,
            "notes": self.notes,
        }


@dataclass
class NormalizedJob:
    title: str
    company: str
    url: str
    source: str
    location: str = ""
    country: Optional[str] = None  # ISO-3166 alpha-2 when known
    workplace: Workplace = "unknown"
    employment_type: Optional[str] = None
    published_date: Optional[str] = None  # YYYY-MM-DD
    last_seen: Optional[str] = None
    description: str = ""
    skills: list[str] = field(default_factory=list)
    experience_requirements: Optional[str] = None
    salary: Optional[str] = None
    sponsorship: Optional[SponsorshipResult] = None
    application_deadline: Optional[str] = None
    status: JobStatus = "unknown"
    source_job_id: Optional[str] = None
    dedupe_key: Optional[str] = None
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        if self.sponsorship is not None:
            d["sponsorship"] = self.sponsorship.to_dict()
        return d

    def to_scrape_hit(self) -> dict[str, Any]:
        """Shape consumed by tools/scrape_state.py candidates."""
        return {
            "title": self.title,
            "company": self.company,
            "location": self.location or "",
            "url": self.url,
            "date": self.published_date,
            "id": self.source_job_id or "",
            "portal": f"visa-{self.source}",
            "source": "cli",
            "description": (self.description or "")[:2000] or None,
            "sponsorship": self.sponsorship.to_dict() if self.sponsorship else None,
            "country": self.country,
            "workplace": self.workplace,
        }
