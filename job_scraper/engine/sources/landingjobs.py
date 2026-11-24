"""Landing.jobs public offers API — EU tech / relocation-friendly board (ever-jobs source).

GET https://landing.jobs/api/v1/offers — no company slug required.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

from ..http import fetch_json
from ..model import NormalizedJob
from ..normalize import detect_country, detect_workplace, strip_html, title_matches_roles
from ..sponsorship import classify_sponsorship
from .base import FetchResult, SourceAdapter, SourceMeta

URL = "https://landing.jobs/api/v1/offers"


class LandingJobsSource(SourceAdapter):
    meta = SourceMeta(
        name="landingjobs",
        official_api=True,
        notes="Public Landing.jobs API; strong for EU tech + relocation signals.",
    )

    def fetch(
        self,
        *,
        role_filter: bool = True,
        max_jobs: int = 80,
        pages: int = 3,
        **_: Any,
    ) -> FetchResult:
        jobs: list[NormalizedJob] = []
        errors: list[str] = []
        page = 1
        while page <= pages and len(jobs) < max_jobs:
            qs = urlencode({"page": page})
            try:
                data = fetch_json(f"{URL}?{qs}")
            except Exception as exc:  # noqa: BLE001
                errors.append(f"landingjobs page={page}: {exc}")
                break
            rows = data if isinstance(data, list) else (data.get("offers") or data.get("data") or [])
            if not isinstance(rows, list) or not rows:
                break
            for row in rows:
                if not isinstance(row, dict):
                    continue
                title = (row.get("title") or "").strip()
                if role_filter and not title_matches_roles(title):
                    continue
                company = ""
                company_obj = row.get("company") or {}
                if isinstance(company_obj, dict):
                    company = (company_obj.get("name") or "").strip()
                company = company or (row.get("company_name") or "Landing.jobs").strip()
                url = (row.get("url") or row.get("apply_url") or "").strip()
                if url and url.startswith("/"):
                    url = "https://landing.jobs" + url
                if not title or not url:
                    continue
                loc = row.get("city") or row.get("location") or ""
                if isinstance(loc, dict):
                    loc = loc.get("name") or ""
                country_name = row.get("country_name") or row.get("country") or ""
                loc_blob = ", ".join(str(p) for p in (loc, country_name) if p)
                desc = strip_html(row.get("description") or row.get("body") or "")
                # Relocation / visa flags when present
                flags = []
                if row.get("relocation_paid") or row.get("relocation"):
                    flags.append("Relocation support mentioned on Landing.jobs listing.")
                if row.get("visa_sponsorship") or row.get("visa"):
                    flags.append("Visa sponsorship flagged on Landing.jobs listing.")
                if flags:
                    desc = (desc + "\n\n" + " ".join(flags)).strip()
                published = None
                for key in ("published_at", "created_at", "updated_at"):
                    val = row.get(key)
                    if isinstance(val, str) and len(val) >= 10:
                        published = val[:10]
                        break
                remote = row.get("remote")
                workplace = detect_workplace(
                    loc_blob,
                    desc,
                    explicit="remote" if remote in (True, "true", "yes", 1) else None,
                )
                country = detect_country(loc_blob, desc)
                sponsorship = classify_sponsorship(desc, source_url=url)
                jobs.append(
                    NormalizedJob(
                        title=title,
                        company=company,
                        url=url,
                        source="landingjobs",
                        location=loc_blob,
                        country=country,
                        workplace=workplace,
                        published_date=published,
                        description=desc,
                        sponsorship=sponsorship,
                        status="open",
                        source_job_id=str(row.get("id") or "") or None,
                        raw={"board": "landing.jobs"},
                    )
                )
                if len(jobs) >= max_jobs:
                    break
            page += 1
        return FetchResult(jobs=jobs, errors=errors, meta={"pages": page - 1})
