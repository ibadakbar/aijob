"""RemoteOK public JSON feed — worldwide remote jobs (jobdrop-style source).

GET https://remoteok.com/api — must link back to RemoteOK when presenting results.
Filter client-side to React/TS roles; Path A/B applied upstream.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ..http import fetch_json
from ..model import NormalizedJob
from ..normalize import detect_country, detect_workplace, strip_html, title_matches_roles
from ..sponsorship import classify_sponsorship
from .base import FetchResult, SourceAdapter, SourceMeta

URL = "https://remoteok.com/api"


class RemoteOKSource(SourceAdapter):
    meta = SourceMeta(
        name="remoteok",
        official_api=True,
        notes="Public RemoteOK JSON; attribute/link back to remoteok.com.",
    )

    def fetch(
        self,
        *,
        role_filter: bool = True,
        max_jobs: int = 60,
        **_: Any,
    ) -> FetchResult:
        jobs: list[NormalizedJob] = []
        errors: list[str] = []
        try:
            data = fetch_json(URL)
        except Exception as exc:  # noqa: BLE001
            return FetchResult(jobs=[], errors=[f"remoteok: {exc}"], meta={})
        if not isinstance(data, list):
            return FetchResult(jobs=[], errors=["remoteok: unexpected payload"], meta={})

        for row in data:
            if not isinstance(row, dict) or "id" not in row:
                continue  # first row is often legal metadata
            title = (row.get("position") or row.get("title") or "").strip()
            if role_filter and not title_matches_roles(title):
                # also allow tag hits for react/typescript/next
                tags = " ".join(str(t) for t in (row.get("tags") or [])).lower()
                if not any(k in tags for k in ("react", "typescript", "nextjs", "next.js", "javascript", "frontend")):
                    continue
            company = (row.get("company") or "").strip() or "RemoteOK"
            url = (row.get("url") or row.get("apply_url") or "").strip()
            if url and url.startswith("/"):
                url = "https://remoteok.com" + url
            if not title or not url:
                continue
            loc = (row.get("location") or "Worldwide Remote").strip()
            desc = strip_html(row.get("description") or "")
            # RemoteOK is worldwide-remote by product — strengthen Path A signal
            desc = (desc + "\n\nWork from anywhere / worldwide remote (RemoteOK listing).").strip()
            published = None
            epoch = row.get("epoch") or row.get("date")
            try:
                if isinstance(epoch, (int, float)):
                    published = datetime.fromtimestamp(epoch, tz=timezone.utc).date().isoformat()
                elif isinstance(epoch, str) and len(epoch) >= 10:
                    published = epoch[:10]
            except (OverflowError, OSError, ValueError):
                published = None
            workplace = detect_workplace(loc, desc, explicit="remote")
            country = detect_country(loc, desc)
            sponsorship = classify_sponsorship(desc, source_url=url)
            salary = None
            if row.get("salary_min") or row.get("salary_max"):
                salary = f"{row.get('salary_min') or ''}-{row.get('salary_max') or ''} USD"
            jobs.append(
                NormalizedJob(
                    title=title,
                    company=company,
                    url=url,
                    source="remoteok",
                    location=loc or "Worldwide",
                    country=country,
                    workplace=workplace,
                    published_date=published,
                    description=desc,
                    salary=salary,
                    sponsorship=sponsorship,
                    status="open",
                    source_job_id=str(row.get("id") or "") or None,
                    raw={"board": "remoteok", "tags": row.get("tags")},
                )
            )
            if len(jobs) >= max_jobs:
                break
        return FetchResult(
            jobs=jobs,
            errors=errors,
            meta={"attribution": "Job data from RemoteOK.com — link back required."},
        )
