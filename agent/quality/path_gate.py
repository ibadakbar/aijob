"""Path A/B + fake-remote hard filter for OpportunityRecord before Excel."""

from __future__ import annotations

from typing import Optional

from agent.models.opportunity import OpportunityRecord
from job_scraper.engine.model import NormalizedJob, SponsorshipResult
from job_scraper.engine.path_filter import path_ab_verdict


def _workplace(rec: OpportunityRecord) -> str:
    w = (rec.remote_type or "").strip().lower()
    if w in ("remote", "hybrid", "onsite", "unknown"):
        return w
    blob = f"{rec.role_or_title} {rec.location} {rec.description}".casefold()
    if "hybrid" in blob:
        return "hybrid"
    if "onsite" in blob or "on-site" in blob or "in office" in blob:
        return "onsite"
    if "remote" in blob:
        return "remote"
    return "unknown"


def _to_normalized(rec: OpportunityRecord) -> NormalizedJob:
    sclass = (rec.sponsorship_class or "unknown").strip() or "unknown"
    if sclass not in (
        "verified_in_listing",
        "sponsor_company_only",
        "possible",
        "not_available",
        "unknown",
    ):
        sclass = "unknown"
    # Infer from path / visa fields when class missing
    if sclass == "unknown":
        if (rec.visa_sponsorship or "").lower() in ("yes", "true", "1"):
            sclass = "verified_in_listing"
        elif (rec.path or "").upper() == "A" and "worldwide" in (
            rec.international_eligibility or rec.description or ""
        ).casefold():
            sclass = "possible"
    reloc: bool | None = None
    if (rec.relocation_support or "").lower() in ("yes", "true", "1"):
        reloc = True
    elif (rec.relocation_support or "").lower() in ("no", "false", "0"):
        reloc = False

    country = (rec.country or "").strip().upper() or None
    if country and len(country) != 2:
        country = None

    return NormalizedJob(
        title=rec.role_or_title or "",
        company=rec.company or "",
        url=rec.source_url or "",
        source=rec.source_name or "agent",
        location=rec.location or "",
        country=country,
        workplace=_workplace(rec),  # type: ignore[arg-type]
        description=rec.description or "",
        sponsorship=SponsorshipResult(
            classification=sclass,  # type: ignore[arg-type]
            confidence=0.5,
            relocation_support=reloc,
        ),
        raw={"path": rec.path},
    )


def path_gate(rec: OpportunityRecord) -> tuple[bool, str, Optional[str]]:
    """Return (keep, reason, path A|B|PK|None).

    Non-job types (founder/client/recruiter/agency) get a softer gate:
    drop fake-remote / unsponsored onsite language; keep otherwise.
    """
    otype = (rec.opportunity_type or "").lower()
    if otype in ("founder", "client", "recruiter", "agency", "company"):
        job = _to_normalized(rec)
        path, reason = path_ab_verdict(job)
        # Soft: if workplace unknown and no remote/onsite cue, keep for contact hunting
        if path:
            rec.path = path
            return True, reason, path
        if "fake-remote" in reason or "country-only" in reason:
            return False, reason, None
        if "without verified sponsorship" in reason:
            return False, reason, None
        # contact-led rows without clear workplace stay
        return True, f"soft_keep_contact_type:{reason}", rec.path or None

    job = _to_normalized(rec)
    path, reason = path_ab_verdict(job)
    if path:
        rec.path = path
        if path == "A":
            rec.international_eligibility = rec.international_eligibility or "remote-international"
        return True, reason, path
    return False, reason, None
