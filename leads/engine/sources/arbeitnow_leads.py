"""Arbeitnow public API adapted into lead records (visa-friendly remote/contract)."""

from __future__ import annotations

import re
from datetime import date
from typing import Any

from job_scraper.engine.sources.arbeitnow import ArbeitnowSource

from ..contacts import build_contacts_from_listing
from ..dedupe import make_lead_id
from ..intent import classify_intent
from ..model import Evidence, Lead, SearchCriteria
from ..sanitize import safe_excerpt
from .base import FetchResult, LeadSourceAdapter, SourceMeta

_STACK_RE = re.compile(
    r"(?i)\b(react(?:\.?js)?|next\.?js|typescript|javascript|node\.?js|full[-\s]?stack|"
    r"saas|mongodb|postgres(?:ql)?)\b"
)


class ArbeitnowLeadsSource(LeadSourceAdapter):
    meta = SourceMeta(
        name="arbeitnow",
        official_api=True,
        notes="Reuses job_scraper Arbeitnow adapter; attribute arbeitnow.com.",
    )

    def fetch(self, criteria: SearchCriteria, **kwargs: Any) -> FetchResult:
        if "arbeitnow" in {s.lower() for s in criteria.excluded_sources}:
            return FetchResult(meta={"skipped": "excluded_sources"})

        pages = int(kwargs.get("arbeitnow_pages", 2))
        visa = bool(criteria.require_sponsorship or kwargs.get("visa_sponsorship", True))
        result = ArbeitnowSource().fetch(
            pages=pages,
            visa_sponsorship=visa,
            role_filter=True,
            max_jobs=max(40, criteria.limit * 2),
        )
        today = date.today().isoformat()
        leads: list[Lead] = []
        excluded = {c.lower() for c in criteria.excluded_companies}
        wanted = set(criteria.lead_types)
        if "all" in wanted or not wanted:
            wanted = {"client", "freelance", "contract", "full_time"}

        for job in result.jobs:
            if job.company.lower() in excluded:
                continue
            emp = (job.employment_type or "").lower()
            if "contract" in emp or "freelance" in emp:
                lead_type = "contract" if "contract" in emp else "freelance"
            else:
                lead_type = "full_time"
            if lead_type not in wanted and "all" not in criteria.lead_types:
                # Sponsorship-focused full-time searches keep full_time
                if not (criteria.require_sponsorship and lead_type == "full_time"):
                    if lead_type not in wanted:
                        continue

            blob = f"{job.title} {job.description}"
            if criteria.technologies and not any(
                t.lower() in blob.lower() for t in criteria.technologies
            ):
                if not _STACK_RE.search(blob):
                    continue

            techs = sorted({m.group(0).lower() for m in _STACK_RE.finditer(blob)})
            intent, expl = classify_intent(
                title=job.title,
                description=job.description,
                lead_type_hint=lead_type,
                source_kind="job_listing",
            )
            if criteria.require_sponsorship and job.sponsorship:
                if job.sponsorship.classification == "not_available":
                    continue
                expl += f"; sponsorship={job.sponsorship.classification}"

            contacts = build_contacts_from_listing(
                description=job.description,
                listing_url=job.url,
                company=job.company,
                check_mx=False,
            )
            lead = Lead(
                id=make_lead_id(
                    source="arbeitnow",
                    company=job.company,
                    title=job.title,
                    url=job.url,
                ),
                name=f"{job.company} — {job.title}",
                lead_type=lead_type,
                company=job.company,
                title=job.title,
                url=job.url,
                source="arbeitnow",
                intent=intent,
                intent_explanation=expl,
                evidence=[
                    Evidence(
                        summary=f"Arbeitnow listing: {job.title}",
                        excerpt=safe_excerpt(job.description, max_len=280),
                        source_url=job.url,
                        published_date=job.published_date,
                        checked_date=today,
                    )
                ],
                technical_requirements=techs or list(job.skills[:8]),
                recommended_service="Product engineering (React/Next/Node) with sponsorship/relocation awareness.",
                contacts=contacts,
                budget_or_salary=job.salary,
                location=job.location,
                workplace=job.workplace,
                country=job.country,
                published_date=job.published_date,
                checked_date=today,
                expired=job.status == "expired",
                risks=["Confirm sponsorship language on employer careers page"]
                if criteria.require_sponsorship
                else [],
                next_action="Open Arbeitnow listing; apply only via official employer URL after review.",
                raw={"sponsorship": job.sponsorship.to_dict() if job.sponsorship else None},
            )
            leads.append(lead)
            if len(leads) >= criteria.limit * 2:
                break

        return FetchResult(
            leads=leads,
            errors=list(result.errors),
            meta={
                "attribution": "Source: Arbeitnow (https://www.arbeitnow.com).",
                **result.meta,
            },
        )
