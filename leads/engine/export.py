"""Export lead runs to Markdown + CSV (+ outreach drafts)."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .export_records import records_for_leads
from .model import Lead, SearchCriteria

ROOT = Path(__file__).resolve().parents[2]
EXPORT_ROOT = ROOT / "leads" / "exports"

CSV_FIELDS = [
    "id",
    "name",
    "lead_type",
    "company",
    "title",
    "url",
    "source",
    "intent",
    "intent_explanation",
    "intent_score",
    "fit_score",
    "overall_score",
    "technical_requirements",
    "budget_or_salary",
    "location",
    "published_date",
    "checked_date",
    "contact_channels",
    "contact_verification",
    "status",
    "confidence",
    "review_reason",
    "opportunity_event",
    "demand_proven",
    "partnership_fit",
    "preferred_contact_role",
    "preferred_contact_value",
    "contact_relevance",
    "expired",
    "risks",
    "next_action",
    "verification_status",
    "company_domain",
    "visa_sponsorship_status",
    "missing_information",
]

# Spec §11 recommended lead record (flat CSV — nested score_breakdown as JSON string)
RECORD_CSV_FIELDS = [
    "lead_id",
    "opportunity_type",
    "company_name",
    "company_domain",
    "company_website",
    "company_country",
    "industry",
    "company_size",
    "opportunity_title",
    "opportunity_description",
    "required_skills",
    "employment_type",
    "remote_status",
    "eligible_countries",
    "visa_sponsorship_status",
    "relocation_status",
    "salary_or_budget",
    "currency",
    "publication_date",
    "last_checked_at",
    "opportunity_status",
    "original_source_url",
    "supporting_evidence",
    "evidence_confidence",
    "decision_maker_name",
    "decision_maker_title",
    "professional_profile_url",
    "business_email",
    "email_verification_status",
    "official_contact_url",
    "contact_source_url",
    "lead_score",
    "score_breakdown",
    "verification_status",
    "missing_information",
    "duplicate_group",
    "discovery_timestamp",
    "source",
    "intent",
    "status",
    "confidence",
]


def _run_dir(run_id: Optional[str] = None) -> Path:
    rid = run_id or datetime.now().strftime("%Y%m%d-%H%M%S")
    path = EXPORT_ROOT / rid
    path.mkdir(parents=True, exist_ok=True)
    return path


def export_run(
    leads: list[Lead],
    criteria: SearchCriteria,
    *,
    source_meta: dict[str, Any],
    run_id: Optional[str] = None,
) -> dict[str, Path]:
    out_dir = _run_dir(run_id)
    md_path = out_dir / "report.md"
    csv_path = out_dir / "leads.csv"
    records_csv = out_dir / "lead_records.csv"
    outreach_path = out_dir / "outreach-drafts.md"
    meta_path = out_dir / "sources-and-limitations.md"
    json_path = out_dir / "leads.json"
    records_json = out_dir / "lead_records.json"

    records = records_for_leads(leads)
    rows = [lead.to_dict() for lead in leads]
    json_path.write_text(
        json.dumps(
            {"criteria": criteria.to_dict(), "leads": rows, "coverage": source_meta.get("coverage")},
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    records_json.write_text(
        json.dumps({"criteria": criteria.to_dict(), "records": records}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for lead in leads:
            contacts = lead.contacts or []
            raw = lead.raw or {}
            writer.writerow(
                {
                    "id": lead.id,
                    "name": lead.name,
                    "lead_type": lead.lead_type,
                    "company": lead.company,
                    "title": lead.title,
                    "url": lead.url,
                    "source": lead.source,
                    "intent": lead.intent,
                    "intent_explanation": lead.intent_explanation,
                    "intent_score": lead.scores.intent_score if lead.scores else "",
                    "fit_score": lead.scores.fit_score if lead.scores else "",
                    "overall_score": lead.scores.overall if lead.scores else "",
                    "technical_requirements": "; ".join(lead.technical_requirements),
                    "budget_or_salary": lead.budget_or_salary or "",
                    "location": lead.location,
                    "published_date": lead.published_date or "",
                    "checked_date": lead.checked_date or "",
                    "contact_channels": "; ".join(
                        f"{c.channel_type}:{c.value}" for c in contacts if c.value
                    ),
                    "contact_verification": "; ".join(
                        c.verification_status for c in contacts
                    ),
                    "status": lead.status,
                    "confidence": "" if lead.confidence is None else f"{lead.confidence:.3f}",
                    "review_reason": lead.review_reason,
                    "opportunity_event": (
                        lead.opportunity.event_type if lead.opportunity else ""
                    ),
                    "demand_proven": (
                        lead.opportunity.demand_proven if lead.opportunity else ""
                    ),
                    "partnership_fit": (
                        lead.partnership.partnership_fit if lead.partnership else ""
                    ),
                    "preferred_contact_role": (
                        lead.preferred_contact.role if lead.preferred_contact else ""
                    ),
                    "preferred_contact_value": (
                        lead.preferred_contact.value if lead.preferred_contact else ""
                    ),
                    "contact_relevance": (
                        lead.preferred_contact.relevance if lead.preferred_contact else ""
                    ),
                    "expired": lead.expired,
                    "risks": "; ".join(lead.risks),
                    "next_action": lead.next_action,
                    "verification_status": raw.get("verification_status") or "",
                    "company_domain": raw.get("company_domain") or "",
                    "visa_sponsorship_status": raw.get("visa_sponsorship_status") or "",
                    "missing_information": "; ".join(raw.get("missing_information") or []),
                }
            )

    with records_csv.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=RECORD_CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for rec in records:
            row = dict(rec)
            breakdown = row.get("score_breakdown")
            if isinstance(breakdown, dict):
                row["score_breakdown"] = json.dumps(breakdown, ensure_ascii=False)
            writer.writerow(row)

    md_path.write_text(_render_report(leads, criteria, source_meta), encoding="utf-8")
    outreach_path.write_text(_render_outreach(leads), encoding="utf-8")
    meta_path.write_text(_render_meta(criteria, source_meta), encoding="utf-8")

    return {
        "dir": out_dir,
        "report": md_path,
        "csv": csv_path,
        "records_csv": records_csv,
        "outreach": outreach_path,
        "meta": meta_path,
        "json": json_path,
        "records_json": records_json,
    }


def _render_report(leads: list[Lead], criteria: SearchCriteria, source_meta: dict[str, Any]) -> str:
    lines = [
        f"# Lead report — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Search criteria",
        f"- Prompt: {criteria.raw_prompt or '(none)'}",
        f"- Types: {', '.join(criteria.lead_types)}",
        f"- Technologies: {', '.join(criteria.technologies)}",
        f"- Geographies: {', '.join(criteria.geographies) or 'any'}",
        f"- Limit: {criteria.limit}; freshness ≤ {criteria.freshness_days} days",
        "",
        f"Found **{len(leads)}** leads after dedupe/scoring "
        f"({sum(1 for l in leads if l.intent == 'EXPLICIT_DEMAND')} explicit, "
        f"{sum(1 for l in leads if l.intent == 'STRONG_SIGNAL')} strong signal, "
        f"{sum(1 for l in leads if l.intent == 'POTENTIAL_FIT')} potential).",
        "",
        "| # | Intent | Fit | Overall | Type | Company | Title | Contact | URL |",
        "|---|--------|-----|---------|------|---------|-------|---------|-----|",
    ]
    for i, lead in enumerate(leads, 1):
        sc = lead.scores
        contact = "—"
        for c in lead.contacts:
            if c.channel_type == "email" and c.value:
                contact = f"{c.value} ({c.verification_status})"
                break
            if c.channel_type in ("application_page", "contact_form") and c.value:
                contact = c.channel_type
        lines.append(
            f"| {i} | {lead.intent} | {sc.fit_score if sc else '—':.2f} | "
            f"{sc.overall if sc else '—':.2f} | {lead.lead_type} | {lead.company} | "
            f"{lead.title} | {contact} | [link]({lead.url}) |"
        )

    lines.extend(["", "## Lead details", ""])
    for i, lead in enumerate(leads, 1):
        lines.append(f"### {i}. {lead.company} — {lead.title}")
        lines.append(f"- **ID:** `{lead.id}`")
        lines.append(f"- **Intent:** {lead.intent} — {lead.intent_explanation}")
        if lead.confidence is not None:
            lines.append(
                f"- **Confidence:** {lead.confidence:.2f} — status `{lead.status}`. {lead.review_reason}"
            )
        if lead.opportunity and lead.opportunity.event_type != "none":
            lines.append(
                f"- **Opportunity radar:** {lead.opportunity.event_type} — "
                f"{lead.opportunity.summary}. demand_proven={lead.opportunity.demand_proven}. "
                f"{lead.opportunity.reason}"
            )
        if lead.partnership and lead.partnership.is_agency:
            lines.append(
                f"- **Agency partnership:** fit=`{lead.partnership.partnership_fit}`. "
                f"{lead.partnership.pitch_angle or '; '.join(lead.partnership.reasons)}"
            )
        if lead.preferred_contact:
            pc = lead.preferred_contact
            lines.append(
                f"- **Preferred contact path:** `{pc.role}` via {pc.channel_type} "
                f"`{pc.value or '(use listing URL)'}` — {pc.relevance}"
            )
            if pc.avoid_reason:
                lines.append(f"  - Avoid: {pc.avoid_reason}")
        if lead.scores:
            lines.append(
                f"- **Scores:** intent={lead.scores.intent_score:.2f}, "
                f"fit={lead.scores.fit_score:.2f}, overall={lead.scores.overall:.2f}"
            )
            lines.append(f"- **Score reasons:** {'; '.join(lead.scores.reasons)}")
        lines.append(f"- **Why profile matches:** {'; '.join(lead.profile_match_reasons) or 'see fit score'}")
        lines.append(f"- **Recommended service:** {lead.recommended_service or '—'}")
        lines.append(f"- **Budget/salary:** {lead.budget_or_salary or 'not stated'}")
        lines.append(f"- **Risks:** {'; '.join(lead.risks) or 'none noted'}")
        lines.append(f"- **Next action:** {lead.next_action}")
        for ev in lead.evidence:
            lines.append(
                f"- **Evidence:** {ev.summary} "
                f"(published {ev.published_date or 'unknown'}, checked {ev.checked_date or 'unknown'})"
            )
            if ev.excerpt:
                lines.append(f"  - Excerpt: {ev.excerpt}")
            lines.append(f"  - Source: {ev.source_url}")
        lines.append("- **Contacts:**")
        for c in lead.contacts:
            lines.append(
                f"  - {c.channel_type}: `{c.value or '(empty)'}` — "
                f"{c.verification_status} via {c.verification_method or 'n/a'}"
            )
            if c.notes:
                lines.append(f"    - {c.notes}")
        lines.append("")
    return "\n".join(lines) + "\n"


def _render_outreach(leads: list[Lead]) -> str:
    lines = [
        "# Outreach drafts (review only — do not send without explicit approval)",
        "",
        "Every draft has `send_approved: false`. No messages are sent by this engine.",
        "",
    ]
    for lead in leads:
        o = lead.outreach
        if o is None:
            continue
        lines.append(f"## {lead.company} — {lead.title} (`{lead.id}`)")
        lines.append(f"**Subject:** {o.subject}")
        lines.append("")
        lines.append("### Email")
        lines.append(o.email_body)
        lines.append("")
        if o.networking_message:
            lines.append("### Networking message")
            lines.append(o.networking_message)
            lines.append("")
        if o.service_proposal:
            lines.append("### Service proposal")
            lines.append(o.service_proposal)
            lines.append("")
        if o.application_message:
            lines.append("### Application message")
            lines.append(o.application_message)
            lines.append("")
        if o.recruiter_outreach:
            lines.append("### Recruiter outreach")
            lines.append(o.recruiter_outreach)
            lines.append("")
        if o.partnership_pitch:
            lines.append("### Agency partnership pitch")
            lines.append(o.partnership_pitch)
            lines.append("")
        lines.append(f"**CTA:** {o.call_to_action}")
        lines.append("**Personalization facts:**")
        for f in o.personalization_facts:
            lines.append(f"- {f}")
        lines.append(f"**send_approved:** `{o.send_approved}`")
        lines.append("")
    if len(lines) <= 5:
        lines.append("_No outreach drafts generated for this run._")
        lines.append("")
    return "\n".join(lines)


def _render_meta(criteria: SearchCriteria, source_meta: dict[str, Any]) -> str:
    lines = [
        "# Sources and limitations",
        "",
        "## Criteria snapshot",
        "```json",
        json.dumps(criteria.to_dict(), indent=2),
        "```",
        "",
        "## Source results",
        "```json",
        json.dumps(source_meta, indent=2, default=str)[:12000],
        "```",
        "",
        "## Coverage",
        "```json",
        json.dumps(source_meta.get("coverage") or {}, indent=2, default=str)[:8000],
        "```",
        "",
        "## Limitations",
        "- Only publicly accessible, ToS-compatible sources are queried by the CLI.",
        "- Remotive requires attribution and linking back to Remotive listing URLs.",
        "- ATS adapters (Greenhouse/Ashby/Lever) use curated public board tokens only.",
        "- Stub sources (Upwork, LinkedIn posts, etc.) are not scraped.",
        "- Emails are never fabricated; MX/A checks do not prove mailbox existence.",
        "- Verification never invents companies, URLs, salaries, or contacts.",
        "- This run is not a claim that the entire internet was searched.",
        "- POTENTIAL_FIT rows are speculative and ranked below explicit demand.",
        "- Identical searches reuse the last fetch for 12 hours and return only new or changed vacancies. Use `--full` to search again.",
        "- Leads below the confidence threshold, or without explicit demand, are stored as `needs_review` and are not auto-qualified.",
        "- Extraction results are cached. Ambiguous companies are marked for a stronger research pass and are not researched automatically.",
        "- Transient source failures are retried, recorded on the run, and can be resumed with `--resume`.",
        "- External messages are never sent without your explicit approval.",
        "",
    ]
    return "\n".join(lines)
