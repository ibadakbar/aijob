"""Greenhouse public Job Board API — curated board tokens only."""

from __future__ import annotations

from typing import Any

from ..http import fetch_json
from ..model import NormalizedJob
from ..normalize import detect_country, detect_workplace, strip_html, title_matches_roles
from ..sponsorship import classify_sponsorship
from .base import FetchResult, SourceAdapter, SourceMeta

LIST_URL = "https://boards-api.greenhouse.io/v1/boards/{token}/jobs"
DETAIL_URL = "https://boards-api.greenhouse.io/v1/boards/{token}/jobs/{job_id}?questions=false"


class GreenhouseSource(SourceAdapter):
    meta = SourceMeta(
        name="greenhouse",
        official_api=True,
        notes="Public boards-api; no auth for GET. Requires board token per company.",
    )

    def fetch(
        self,
        *,
        boards: list[dict[str, str]] | None = None,
        role_filter: bool = True,
        fetch_content: bool = True,
        max_jobs: int = 200,
        max_per_board: int = 12,
        **_: Any,
    ) -> FetchResult:
        jobs: list[NormalizedJob] = []
        errors: list[str] = []
        for board in boards or []:
            token = (board.get("token") or "").strip()
            company = (board.get("company") or token).strip()
            if not token or token.startswith("//") or company.upper() == "SKIP":
                continue
            try:
                data = fetch_json(LIST_URL.format(token=token))
            except Exception as exc:  # noqa: BLE001
                errors.append(f"greenhouse/{token}: {exc}")
                continue
            listed = data.get("jobs") or []
            kept = 0
            for row in listed:
                title = (row.get("title") or "").strip()
                if role_filter and not title_matches_roles(title):
                    continue
                job_id = row.get("id")
                loc = ((row.get("location") or {}).get("name") if isinstance(row.get("location"), dict) else row.get("location")) or ""
                url = (row.get("absolute_url") or "").strip()
                if not url or job_id is None:
                    continue
                desc = ""
                if fetch_content:
                    try:
                        detail = fetch_json(DETAIL_URL.format(token=token, job_id=job_id))
                        desc = strip_html(detail.get("content") or "")
                    except Exception as exc:  # noqa: BLE001
                        errors.append(f"greenhouse/{token}/{job_id} detail: {exc}")
                published = None
                for key in ("first_published", "updated_at"):
                    val = row.get(key)
                    if isinstance(val, str) and len(val) >= 10:
                        published = val[:10]
                        break
                country = detect_country(str(loc), desc)
                workplace = detect_workplace(str(loc), desc)
                sponsorship = classify_sponsorship(desc, source_url=url)
                jobs.append(
                    NormalizedJob(
                        title=title,
                        company=company,
                        url=url,
                        source="greenhouse",
                        location=str(loc),
                        country=country,
                        workplace=workplace,
                        published_date=published,
                        description=desc,
                        sponsorship=sponsorship,
                        status="open",
                        source_job_id=str(job_id),
                        raw={"board": token},
                    )
                )
                kept += 1
                if kept >= max_per_board or len(jobs) >= max_jobs:
                    break
            if len(jobs) >= max_jobs:
                break
        return FetchResult(jobs=jobs, errors=errors, meta={"boards": len(boards or [])})
