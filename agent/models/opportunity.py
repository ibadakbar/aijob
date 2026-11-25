"""Opportunity record model for Excel persistence."""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Any


def norm_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").casefold())


def make_opportunity_id(
    opportunity_type: str,
    company: str,
    title: str,
    url: str = "",
) -> str:
    """Stable id from type + company + title (+ URL host/path when present)."""
    raw = f"{opportunity_type}|{norm_key(company)}|{norm_key(title)}|{norm_key(url)}"
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
    prefix = norm_key(opportunity_type)[:8] or "opp"
    return f"{prefix}_{digest}"


@dataclass
class OpportunityRecord:
    id: str
    opportunity_type: str  # job | contract | freelance | founder | recruiter | agency | company | client
    company: str
    role_or_title: str
    description: str = ""
    required_skills: str = ""
    country: str = ""
    location: str = ""
    remote_type: str = ""  # remote | hybrid | onsite | unknown
    international_eligibility: str = ""
    visa_sponsorship: str = ""  # yes | no | unknown
    relocation_support: str = ""  # yes | no | unknown
    salary_or_budget: str = ""
    currency: str = ""
    posted_date: str = ""
    discovered_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %I:%M:%S %p"))
    last_verified: str = ""
    source_name: str = ""
    source_url: str = ""
    company_website: str = ""
    contact_name: str = ""
    contact_position: str = ""
    contact_email: str = ""
    contact_phone: str = ""  # published only — never inferred
    email_status: str = "NOT_FOUND"  # VERIFIED | PUBLIC_UNVERIFIED | INFERRED | NOT_FOUND
    linkedin_url: str = ""
    intent_classification: str = ""  # EXPLICIT_DEMAND | STRONG_SIGNAL | POTENTIAL_FIT | ""
    evidence: str = ""
    opportunity_score: float = 0.0
    grade: str = ""  # A | B | C | Low
    status: str = "new"
    next_action: str = ""
    notes: str = ""
    path: str = ""  # A | B | PK | ""
    sponsorship_class: str = ""
    skill_score: float = 0.0
    raw_json: str = ""

    def to_row(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "OpportunityRecord":
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        data = {k: ("" if v is None else v) for k, v in row.items() if k in known}
        if "opportunity_score" in data:
            try:
                data["opportunity_score"] = float(data["opportunity_score"] or 0)
            except (TypeError, ValueError):
                data["opportunity_score"] = 0.0
        if "skill_score" in data:
            try:
                data["skill_score"] = float(data["skill_score"] or 0)
            except (TypeError, ValueError):
                data["skill_score"] = 0.0
        return cls(**data)  # type: ignore[arg-type]


def grade_from_score(score: float) -> str:
    if score >= 85:
        return "A"
    if score >= 70:
        return "B"
    if score >= 50:
        return "C"
    return "Low"


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat(sep=" ")


def now_discovered() -> str:
    """Local discovery timestamp stored in Excel (sortable)."""
    return datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")


def parse_datetime_flexible(value: Any) -> datetime | None:
    """Parse Excel cell / string / date into a datetime (date-only → midnight)."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    raw = str(value).strip()
    if not raw:
        return None
    if raw[-2:].upper() in ("AM", "PM") and len(raw) >= 10:
        for fmt in (
            "%Y-%m-%d %I:%M:%S %p",
            "%Y-%m-%d %I:%M %p",
            "%Y-%m-%d %I:%M:%S%p",
            "%Y-%m-%d %I:%M%p",
        ):
            try:
                return datetime.strptime(raw[:22].strip(), fmt)
            except ValueError:
                continue
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d",
    ):
        try:
            chunk = raw.replace("Z", "")[:19] if ("T" in raw or len(raw) > 10) else raw[:10]
            return datetime.strptime(chunk, fmt)
        except ValueError:
            continue
    try:
        return datetime.strptime(raw[:10], "%Y-%m-%d")
    except ValueError:
        return None


def to_discovered_str(value: Any) -> str:
    """Normalize any cell value to the stored 12-hour discovered timestamp string."""
    dt = parse_datetime_flexible(value)
    if dt is None:
        return "" if value is None else str(value).strip()
    # Preserve date-only legacy strings as YYYY-MM-DD (no fake clock) when input had no time
    if isinstance(value, date) and not isinstance(value, datetime):
        return value.isoformat()
    raw = str(value).strip() if not isinstance(value, (date, datetime)) else ""
    if raw and len(raw) <= 10:
        return raw[:10]
    return dt.strftime("%Y-%m-%d %I:%M:%S %p")


def is_date_only_timestamp(value: Any) -> bool:
    """True when value has no real clock time (date-only or midnight placeholder)."""
    if value is None or value == "":
        return True
    if isinstance(value, datetime):
        return value.hour == 0 and value.minute == 0 and value.second == 0
    if isinstance(value, date):
        return True
    raw = str(value).strip()
    if len(raw) <= 10:
        return True
    dt = parse_datetime_flexible(raw)
    if dt is None:
        return True
    return dt.hour == 0 and dt.minute == 0 and dt.second == 0


def format_12h(value: str) -> str:
    """Display date/datetime as ``YYYY-MM-DD hh:mm AM/PM`` (12-hour)."""
    if not value:
        return ""
    dt = parse_datetime_flexible(value)
    if dt is None:
        return str(value).strip()
    return dt.strftime("%Y-%m-%d %I:%M %p")
