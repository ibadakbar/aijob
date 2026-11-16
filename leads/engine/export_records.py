"""Map Lead → recommended export record (empty/unknown when unverified — never invent)."""

from __future__ import annotations

from typing import Any

from .model import Lead
from .verify import attach_verification, infer_company_domain


def lead_export_record(lead: Lead) -> dict[str, Any]:
    """Structured opportunity row for CSV/JSON consumers."""
    raw = lead.raw or {}
    ver = raw.get("verification") if isinstance(raw.get("verification"), dict) else None
    if ver is None:
        report = attach_verification(lead)
        ver = report.to_dict()
        raw = lead.raw or {}

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
    contact_url = next(
        (
            c
            for c in lead.contacts
            if c.channel_type in ("application_page", "contact_form") and c.value
        ),
        None,
    )
    dm = lead.preferred_contact
    domain = raw.get("company_domain") or infer_company_domain(lead) or ""
    website = raw.get("company_website") or (f"https://{domain}" if domain else "")

    evidence_bits = []
    for e in lead.evidence:
        bit = e.summary
        if e.excerpt:
            bit += f" | {e.excerpt[:160]}"
        if e.source_url:
            bit += f" | {e.source_url}"
        evidence_bits.append(bit)

    scores = lead.scores
    breakdown = scores.to_dict() if scores else {}

    return {
        "lead_id": lead.id,
        "opportunity_type": lead.lead_type,
        "company_name": lead.company,
        "company_domain": domain,
        "company_website": website,
        "company_country": lead.country or "",
        "industry": "",
        "company_size": "",
        "opportunity_title": lead.title,
        "opportunity_description": (lead.evidence[0].excerpt if lead.evidence else "") or "",
        "required_skills": "; ".join(lead.technical_requirements),
        "employment_type": lead.lead_type,
        "remote_status": lead.workplace,
        "eligible_countries": lead.location or "",
        "visa_sponsorship_status": raw.get("visa_sponsorship_status")
        or ver.get("visa_sponsorship_status")
        or "unknown",
        "relocation_status": raw.get("relocation_status") or ver.get("relocation_status") or "unknown",
        "salary_or_budget": lead.budget_or_salary or "",
        "currency": "",
        "publication_date": lead.published_date or "",
        "last_checked_at": lead.checked_date or ver.get("last_checked_at") or "",
        "opportunity_status": raw.get("opportunity_status")
        or ver.get("opportunity_status")
        or ("expired" if lead.expired else "uncertain"),
        "original_source_url": lead.url,
        "supporting_evidence": " || ".join(evidence_bits),
        "evidence_confidence": raw.get("evidence_confidence")
        if raw.get("evidence_confidence") is not None
        else ver.get("evidence_confidence", ""),
        "decision_maker_name": (dm.name if dm else None) or "",
        "decision_maker_title": (dm.title if dm else None) or "",
        "professional_profile_url": (
            dm.value
            if dm and dm.channel_type == "professional_profile"
            else next(
                (
                    c.value
                    for c in lead.contacts
                    if c.channel_type == "professional_profile" and c.value
                ),
                "",
            )
        ),
        "business_email": email.value if email else "",
        "email_verification_status": email.verification_status if email else "",
        "official_contact_url": contact_url.value if contact_url else lead.url,
        "contact_source_url": (email.source_url if email else "")
        or (contact_url.source_url if contact_url else "")
        or lead.url,
        "lead_score": scores.overall if scores else "",
        "score_breakdown": breakdown,
        "verification_status": raw.get("verification_status") or ver.get("status") or "unverified",
        "missing_information": "; ".join(
            raw.get("missing_information") or ver.get("missing_information") or []
        ),
        "duplicate_group": "",
        "discovery_timestamp": lead.checked_date or "",
        "source": lead.source,
        "intent": lead.intent,
        "status": lead.status,
        "confidence": lead.confidence if lead.confidence is not None else "",
    }


def records_for_leads(leads: list[Lead]) -> list[dict[str, Any]]:
    return [lead_export_record(lead) for lead in leads]
