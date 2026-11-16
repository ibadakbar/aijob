"""Arbeitnow public job-board API (visa_sponsorship filter)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from urllib.parse import urlencode

from ..http import fetch_json
from ..model import NormalizedJob
from ..normalize import detect_country, detect_workplace, strip_html, title_matches_roles
from ..sponsorship import classify_sponsorship
from .base import FetchResult, SourceAdapter, SourceMeta

BASE = "https://www.arbeitnow.com/api/job-board-api"


class ArbeitnowSource(SourceAdapter):
    meta = SourceMeta(
        name="arbeitnow",
        official_api=True,
        notes="Free public API; link back to arbeitnow.com; visa_sponsorship filter.",
    )

    def fetch(
        self,
        *,
        pages: int = 2,
        visa_sponsorship: bool = True,
        role_filter: bool = True,
        max_jobs: int = 80,
        **_: Any,
    ) -> FetchResult:
        jobs: list[NormalizedJob] = []
        errors: list[str] = []
        for page in range(1, max(1, pages) + 1):
            qs = urlencode({"page": page, "visa_sponsorship": str(visa_sponsorship).lower()})
            url = f"{BASE}?{qs}"
            try:
                data = fetch_json(url)
            except Exception as exc:  # noqa: BLE001 — surface per-source errors
                errors.append(f"arbeitnow page {page}: {exc}")
                break
            rows = data.get("data") or []
            if not rows:
                break
            for row in rows:
                try:
                    job = self._normalize(row, visa_filter=visa_sponsorship)
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"arbeitnow parse: {exc}")
                    continue
                if role_filter and not title_matches_roles(job.title):
                    continue
                jobs.append(job)
                if len(jobs) >= max_jobs:
                    return FetchResult(jobs=jobs, errors=errors, meta={"pages": page})
        return FetchResult(jobs=jobs, errors=errors, meta={"pages_fetched": pages})

    def _normalize(self, row: dict, *, visa_filter: bool) -> NormalizedJob:
        title = (row.get("title") or "").strip()
        company = (row.get("company_name") or row.get("company") or "").strip()
        url = (row.get("url") or "").strip()
        if not title or not company or not url:
            raise ValueError("missing title/company/url")
        loc = (row.get("location") or "").strip()
        desc = strip_html(row.get("description") or "")
        created = row.get("created_at")
        published = None
        if isinstance(created, str) and len(created) >= 10:
            published = created[:10]
        elif isinstance(created, (int, float)):
            try:
                published = datetime.utcfromtimestamp(created).date().isoformat()
            except (OverflowError, OSError, ValueError):
                published = None
        remote_flag = row.get("remote")
        workplace = detect_workplace(
            loc,
            desc,
            explicit="remote" if remote_flag is True else None,
        )
        country = detect_country(loc, desc)
        hint = "arbeitnow_visa_filter" if visa_filter else None
        sponsorship = classify_sponsorship(
            desc,
            source_url=url,
            source_hint=hint,
        )
        return NormalizedJob(
            title=title,
            company=company,
            url=url,
            source="arbeitnow",
            location=loc,
            country=country,
            workplace=workplace,
            published_date=published,
            description=desc,
            skills=list(row.get("tags") or [])[:20],
            sponsorship=sponsorship,
            status="open",
            source_job_id=(row.get("slug") or None),
            raw={"tags": row.get("tags"), "job_types": row.get("job_types")},
        )
