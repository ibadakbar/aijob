"""Authenticity verification — explicit statuses, never fabricate evidence."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Any, Literal, Optional
from urllib.parse import urlparse

from .dedupe import domain_of, fold_name
from .model import Lead

VerificationStatus = Literal[
    "verified",
    "partially_verified",
    "unverified",
    "contradictory",
    "stale",
    "rejected",
]


@dataclass
class VerificationReport:
    status: VerificationStatus
    company_domain: str = ""
    company_website: str = ""
    original_source_url: str = ""
    evidence_confidence: float = 0.0
    missing_information: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    checks: list[str] = field(default_factory=list)
    visa_sponsorship_status: str = "unknown"
    relocation_status: str = "unknown"
    opportunity_status: str = "uncertain"
    last_checked_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["evidence_confidence"] = round(self.evidence_confidence, 3)
        return d


_SPONSOR_YES = re.compile(
    r"(?i)\b(visa sponsorship|will sponsor|sponsorship available|relocation (?:support|package))\b"
)
_SPONSOR_NO = re.compile(
    r"(?i)\b(no sponsorship|cannot sponsor|must (?:already )?have (?:a )?(?:visa|work permit)|"
    r"citizens? (?:and|or) (?:permanent )?residents? only)\b"
)


def _parse_day(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def infer_company_domain(lead: Lead) -> str:
    """Best-effort public domain from listing URL or company name — not invented email."""
    host = domain_of(lead.url)
    # Job-board hosts are not the employer domain
    boards = (
        "remotive.com",
        "arbeitnow.com",
        "arbeitnow.co.uk",
        "arbeitnow.nl",
        "arbeitnow.ch",
        "arbeitnow.fr",
        "greenhouse.io",
        "boards.greenhouse.io",
        "lever.co",
        "jobs.lever.co",
        "ashbyhq.com",
        "jobs.ashbyhq.com",
    )
    if host and not any(host == b or host.endswith("." + b) for b in boards):
        return host
    # Prefer domain from published email on official source
    for c in lead.contacts:
        if c.channel_type == "email" and "@" in (c.value or ""):
            if c.verification_status in ("published_on_official_source", "domain_mx_present"):
                return c.value.split("@", 1)[1].lower()
    return ""


def verify_lead(lead: Lead, *, freshness_days: int = 30) -> VerificationReport:
    """Score authenticity from stored evidence only — never invent missing facts."""
    today = date.today().isoformat()
    missing: list[str] = []
    issues: list[str] = []
    checks: list[str] = []
    conf = 0.15

    url = (lead.url or "").strip()
    if url and urlparse(url).scheme in ("http", "https") and urlparse(url).netloc:
        checks.append("original_source_url_present")
        conf += 0.2
    else:
        missing.append("original_source_url")
        issues.append("Missing or invalid opportunity URL")

    if lead.company and fold_name(lead.company):
        checks.append("company_name_present")
        conf += 0.1
    else:
        missing.append("company_name")

    if lead.title:
        checks.append("opportunity_title_present")
        conf += 0.05
    else:
        missing.append("opportunity_title")

    has_excerpt = any((e.excerpt or e.summary) and (e.source_url or url) for e in lead.evidence)
    if has_excerpt:
        checks.append("evidence_excerpt_with_source")
        conf += 0.2
    else:
        missing.append("supporting_evidence_excerpt")

    domain = infer_company_domain(lead)
    website = f"https://{domain}" if domain else ""
    if domain:
        checks.append("company_domain_inferred")
        conf += 0.05
    else:
        missing.append("company_domain")

    # Prefer explicit published_date; else LinkedIn activity snowflake (~3mo hard ceiling)
    pub = _parse_day(lead.published_date)
    if pub is None and lead.url and "linkedin.com" in (lead.url or "").casefold():
        m = re.search(r"(?i)(?:activity|ugcPost|share)[_:-]?(\d{15,22})", lead.url)
        if m:
            try:
                ms = int(m.group(1)) >> 22
                if 1_000_000_000_000 < ms < 2_500_000_000_000:
                    from datetime import timezone as _tz

                    pub = datetime.fromtimestamp(ms / 1000, tz=_tz.utc).date()
                    if not lead.published_date:
                        lead.published_date = pub.isoformat()
            except (ValueError, OSError, OverflowError):
                pub = None
    max_age_days = 90  # hard ceiling: last 3 months only
    if pub is None:
        missing.append("publication_date")
        conf -= 0.02
    else:
        checks.append("publication_date_present")
        age = (date.today() - pub).days
        if age > max_age_days or lead.expired:
            issues.append(f"Listing older than {max_age_days}d (age {age}d) — drop")
            conf -= 0.45

    email = next(
        (
            c
            for c in lead.contacts
            if c.channel_type == "email"
            and c.value
            and c.verification_status
            in ("published_on_official_source", "domain_mx_present")
        ),
        None,
    )
    if email:
        checks.append("published_business_email")
        conf += 0.12
    else:
        missing.append("business_email")
        if not any(c.channel_type in ("application_page", "contact_form") and c.value for c in lead.contacts):
            missing.append("official_contact_url")
        else:
            checks.append("official_application_or_contact_url")
            conf += 0.08

    if lead.budget_or_salary:
        checks.append("compensation_stated")
        conf += 0.05
    else:
        missing.append("salary_or_budget")

    blob = " ".join(
        [lead.title, lead.intent_explanation or ""]
        + [f"{e.summary} {e.excerpt}" for e in lead.evidence]
        + [str((lead.raw or {}).get("description") or "")]
    )
    visa = "unknown"
    reloc = "unknown"
    if _SPONSOR_YES.search(blob):
        visa = "mentioned_positive"
        checks.append("visa_or_relocation_language")
        conf += 0.03
    if _SPONSOR_NO.search(blob):
        if visa == "mentioned_positive":
            visa = "contradictory"
            issues.append("Sponsorship language conflicts across text")
        else:
            visa = "not_available"
    if re.search(r"(?i)\brelocati", blob):
        reloc = "mentioned"

    if lead.intent == "EXPLICIT_DEMAND" and has_excerpt and url:
        conf += 0.1
        checks.append("explicit_demand_with_evidence")
    elif lead.intent == "POTENTIAL_FIT":
        conf -= 0.08
        issues.append("No established buying/hiring intent from public evidence")

    conf = max(0.0, min(1.0, conf))

    # Status ladder — hard-expire anything older than 3 months
    if lead.expired or (pub and (date.today() - pub).days > 90):
        status: VerificationStatus = "stale"
        opp_status = "expired" if lead.expired else "stale"
        lead.expired = True
    elif visa == "contradictory":
        status = "contradictory"
        opp_status = "uncertain"
    elif not url or not lead.company:
        status = "rejected"
        opp_status = "rejected"
    elif lead.intent == "EXPLICIT_DEMAND" and has_excerpt and url and conf >= 0.72:
        status = "verified"
        opp_status = "active"
    elif has_excerpt and url and lead.company:
        status = "partially_verified"
        opp_status = "active" if lead.intent == "EXPLICIT_DEMAND" else "uncertain"
    else:
        status = "unverified"
        opp_status = "uncertain"

    return VerificationReport(
        status=status,
        company_domain=domain,
        company_website=website,
        original_source_url=url,
        evidence_confidence=conf,
        missing_information=sorted(set(missing)),
        issues=issues,
        checks=checks,
        visa_sponsorship_status=visa,
        relocation_status=reloc,
        opportunity_status=opp_status,
        last_checked_at=lead.checked_date or today,
    )


def attach_verification(lead: Lead, *, freshness_days: int = 30) -> VerificationReport:
    report = verify_lead(lead, freshness_days=freshness_days)
    lead.raw = dict(lead.raw or {})
    lead.raw["verification"] = report.to_dict()
    # Surface common fields for export without breaking older readers
    lead.raw["company_domain"] = report.company_domain
    lead.raw["company_website"] = report.company_website
    lead.raw["verification_status"] = report.status
    lead.raw["missing_information"] = report.missing_information
    lead.raw["evidence_confidence"] = report.evidence_confidence
    lead.raw["visa_sponsorship_status"] = report.visa_sponsorship_status
    lead.raw["relocation_status"] = report.relocation_status
    lead.raw["opportunity_status"] = report.opportunity_status
    if report.status == "stale" and "stale verification" not in " ".join(lead.risks).lower():
        lead.risks.append("Verification: listing appears stale")
    if report.status == "rejected":
        lead.risks.append("Verification rejected — incomplete core fields")
    return report
