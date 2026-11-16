"""Offline fixture adapter for tests — no network."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from ..contacts import build_contacts_from_listing
from ..dedupe import make_lead_id
from ..intent import classify_intent
from ..model import Evidence, Lead, LeadType, SearchCriteria
from ..sanitize import safe_excerpt
from .base import FetchResult, LeadSourceAdapter, SourceMeta

DEFAULT_FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "sample_leads.json"


class FixtureSource(LeadSourceAdapter):
    meta = SourceMeta(
        name="fixture",
        official_api=False,
        notes="Loads tests/fixtures or leads/fixtures JSON; no live network.",
    )

    def __init__(self, path: Path | None = None):
        self.path = path or DEFAULT_FIXTURE

    def fetch(self, criteria: SearchCriteria, **kwargs: Any) -> FetchResult:
        path = Path(kwargs.get("fixture_path") or self.path)
        if not path.is_file():
            return FetchResult(errors=[f"fixture missing: {path}"], meta={"path": str(path)})
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return FetchResult(errors=[f"fixture read: {exc}"], meta={"path": str(path)})

        today = date.today().isoformat()
        leads: list[Lead] = []
        for row in data.get("leads") or []:
            try:
                leads.append(self._row_to_lead(row, today=today))
            except Exception as exc:  # noqa: BLE001
                continue
        # Apply soft tech filter when criteria specify technologies
        if criteria.technologies:
            filtered = []
            for lead in leads:
                blob = f"{lead.title} {' '.join(lead.technical_requirements)}".lower()
                if any(t.lower() in blob for t in criteria.technologies):
                    filtered.append(lead)
            leads = filtered or leads
        return FetchResult(leads=leads, meta={"path": str(path), "fixture": True})

    def _row_to_lead(self, row: dict, *, today: str) -> Lead:
        title = row["title"]
        company = row["company"]
        url = row["url"]
        desc = row.get("description") or ""
        lead_type: LeadType = row.get("lead_type") or "full_time"
        source_kind = row.get("source_kind") or "job_listing"
        intent, expl = classify_intent(
            title=title,
            description=desc,
            lead_type_hint=lead_type,
            source_kind=source_kind,
        )
        if row.get("intent_override"):
            intent = row["intent_override"]
            expl = row.get("intent_explanation") or expl
        contacts = build_contacts_from_listing(
            description=desc,
            listing_url=url,
            company=company,
            check_mx=False,
        )
        # Allow fixture to declare contact_form without inventing email
        if row.get("contact_form_url"):
            from ..model import ContactChannel

            contacts.insert(
                0,
                ContactChannel(
                    channel_type="contact_form",
                    value=row["contact_form_url"],
                    source_url=row["contact_form_url"],
                    verification_status="published_on_official_source",
                    verification_method="fixture_declared_contact_form",
                    date_checked=today,
                    notes="Official contact form URL from fixture (not invented).",
                ),
            )
        return Lead(
            id=make_lead_id(source="fixture", company=company, title=title, url=url),
            name=f"{company} — {title}",
            lead_type=lead_type,
            company=company,
            title=title,
            url=url,
            source="fixture",
            intent=intent,
            intent_explanation=expl,
            evidence=[
                Evidence(
                    summary=row.get("evidence_summary") or f"Fixture evidence for {title}",
                    excerpt=safe_excerpt(desc, max_len=280),
                    source_url=url,
                    published_date=row.get("published_date"),
                    checked_date=today,
                )
            ],
            technical_requirements=list(row.get("technologies") or []),
            recommended_service=row.get("recommended_service")
            or "Full-stack React/Next.js product engineering",
            contacts=contacts,
            budget_or_salary=row.get("budget_or_salary"),
            location=row.get("location") or "",
            workplace=row.get("workplace") or "remote",
            published_date=row.get("published_date"),
            checked_date=today,
            expired=bool(row.get("expired")),
            risks=list(row.get("risks") or []),
            next_action=row.get("next_action") or "Review evidence and decide whether to outreach.",
            raw={
                "fixture": True,
                "description": desc,
                "source_kind": source_kind,
            },
        )
