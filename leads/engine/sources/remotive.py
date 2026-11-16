"""Remotive public remote-jobs API (no key). Attribute and link back to Remotive."""

from __future__ import annotations

import html
import re
from datetime import date, datetime
from typing import Any, Optional
from urllib.parse import urlencode

from job_scraper.engine.http import fetch_json
from job_scraper.engine.normalize import detect_country, detect_workplace, strip_html

from ..contacts import build_contacts_from_listing
from ..dedupe import make_lead_id
from ..intent import classify_intent
from ..model import Evidence, Lead, LeadType, SearchCriteria
from ..sanitize import safe_excerpt, sanitize_text
from .base import FetchResult, LeadSourceAdapter, SourceMeta

BASE = "https://remotive.com/api/remote-jobs"

_STACK_RE = re.compile(
    r"(?i)\b(react(?:\.?js)?|next\.?js|typescript|javascript|node\.?js|full[-\s]?stack|"
    r"tailwind|mongodb|postgres(?:ql)?|supabase|stripe|saas|mern|redux)\b"
)


def _map_job_type(raw: Optional[str]) -> LeadType:
    t = (raw or "").lower().replace("-", "_")
    if "freelance" in t:
        return "freelance"
    if "contract" in t:
        return "contract"
    if "part" in t:
        return "contract"
    return "full_time"


def _wanted_types(criteria: SearchCriteria) -> set[str]:
    types = set(criteria.lead_types)
    if "all" in types or not types:
        return {"client", "freelance", "contract", "full_time"}
    # Client searches still benefit from freelance/contract listings as demand signals
    if "client" in types:
        types |= {"freelance", "contract"}
    return types


class RemotiveSource(LeadSourceAdapter):
    meta = SourceMeta(
        name="remotive",
        official_api=True,
        notes=(
            "Free public API at remotive.com/api/remote-jobs. Link back to Remotive "
            "listing URLs; max ~4 requests/day recommended; no third-party re-posting."
        ),
    )

    def fetch(self, criteria: SearchCriteria, **kwargs: Any) -> FetchResult:
        if "remotive" in {s.lower() for s in criteria.excluded_sources}:
            return FetchResult(meta={"skipped": "excluded_sources"})

        search = criteria.query_text or " ".join(criteria.technologies[:3]) or "react"
        limit = min(100, max(criteria.limit * 3, 20))
        qs = urlencode(
            {
                "category": "software-dev",
                "search": search,
                "limit": str(limit),
            }
        )
        url = f"{BASE}?{qs}"
        leads: list[Lead] = []
        errors: list[str] = []
        try:
            data = fetch_json(url)
        except Exception as exc:  # noqa: BLE001
            return FetchResult(errors=[f"remotive: {exc}"], meta={"url": url})

        rows = data.get("jobs") or []
        wanted = _wanted_types(criteria)
        excluded = {c.lower() for c in criteria.excluded_companies}
        today = date.today().isoformat()

        for row in rows:
            try:
                lead = self._normalize(row, criteria=criteria, today=today)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"remotive parse: {exc}")
                continue
            if lead.company.lower() in excluded:
                continue
            if lead.lead_type not in wanted and "all" not in criteria.lead_types:
                # Still keep contract/freelance when searching full_time? No — filter.
                if not (wanted & {lead.lead_type}):
                    continue
            if criteria.technologies:
                blob = f"{lead.title} {' '.join(lead.technical_requirements)}".lower()
                if not any(t.lower() in blob or t.lower().replace(".", "") in blob.replace(".", "") for t in criteria.technologies):
                    # soft filter: keep if stack regex hits title/desc evidence
                    ev = " ".join(e.summary for e in lead.evidence).lower()
                    if not _STACK_RE.search(f"{lead.title} {ev}"):
                        continue
            leads.append(lead)
            if len(leads) >= criteria.limit * 2:
                break

        return FetchResult(
            leads=leads,
            errors=errors,
            meta={
                "url": url,
                "raw_count": len(rows),
                "attribution": "Source: Remotive (https://remotive.com). Link back to listing URLs.",
                "legal_notice": data.get("0-legal-notice") or data.get("00-warning") or "",
            },
        )

    def _normalize(self, row: dict, *, criteria: SearchCriteria, today: str) -> Lead:
        title = (row.get("title") or "").strip()
        company = (row.get("company_name") or "").strip()
        url = (row.get("url") or "").strip()
        if not title or not company or not url:
            raise ValueError("missing title/company/url")

        desc_html = row.get("description") or ""
        desc = sanitize_text(strip_html(html.unescape(desc_html)), max_len=5000)
        job_type = _map_job_type(row.get("job_type"))
        loc = (row.get("candidate_required_location") or "").strip()
        published = None
        pub = row.get("publication_date")
        if isinstance(pub, str) and len(pub) >= 10:
            published = pub[:10]
            try:
                age = (date.today() - datetime.strptime(published, "%Y-%m-%d").date()).days
                expired = age > max(criteria.freshness_days * 3, 90)
            except ValueError:
                expired = False
        else:
            expired = False

        techs = sorted({m.group(0).lower() for m in _STACK_RE.finditer(f"{title} {desc}")})
        intent, intent_expl = classify_intent(
            title=title,
            description=desc,
            lead_type_hint=job_type,
            source_kind="job_listing",
        )
        contacts = build_contacts_from_listing(
            description=desc,
            listing_url=url,
            company=company,
            check_mx=False,  # MX is opt-in in pipeline for speed
        )
        salary = (row.get("salary") or "").strip() or None
        workplace = detect_workplace(loc, desc, explicit="remote")
        country = detect_country(loc, desc)

        return Lead(
            id=make_lead_id(source="remotive", company=company, title=title, url=url),
            name=f"{company} — {title}",
            lead_type=job_type,
            company=company,
            title=title,
            url=url,
            source="remotive",
            intent=intent,
            intent_explanation=intent_expl,
            evidence=[
                Evidence(
                    summary=f"Remotive remote {job_type.replace('_', ' ')} listing: {title}",
                    excerpt=safe_excerpt(desc, max_len=280),
                    source_url=url,
                    published_date=published,
                    checked_date=today,
                )
            ],
            technical_requirements=techs,
            profile_match_reasons=[],
            recommended_service=_recommend(job_type, techs),
            contacts=contacts,
            budget_or_salary=salary,
            location=loc,
            workplace=workplace,
            country=country,
            published_date=published,
            checked_date=today,
            expired=expired,
            risks=_risks(loc, salary, expired),
            next_action="Review listing and apply via official Remotive URL (do not auto-send).",
            raw={"remotive_id": row.get("id"), "job_type": row.get("job_type")},
        )


def _recommend(lead_type: LeadType, techs: list[str]) -> str:
    stack = ", ".join(techs[:5]) or "React/Next.js/Node"
    if lead_type in ("freelance", "contract"):
        return f"Contract/freelance delivery on {stack} (SaaS UI, APIs, dashboards)."
    return f"Full-stack product engineering with {stack}."


def _risks(loc: str, salary: Optional[str], expired: bool) -> list[str]:
    risks: list[str] = []
    if expired:
        risks.append("Listing may be stale relative to freshness window")
    if loc and re.search(r"(?i)\b(us only|usa only|europe only|eu only|must be (in|based))\b", loc):
        risks.append(f"Location constraint: {loc}")
    if not salary:
        risks.append("Compensation not stated on listing")
    return risks
