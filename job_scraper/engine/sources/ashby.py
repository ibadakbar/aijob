"""Ashby public job posting API — curated board slugs only."""

from __future__ import annotations

from typing import Any

from ..http import fetch_json
from ..model import NormalizedJob
from ..normalize import detect_country, detect_workplace, strip_html, title_matches_roles
from ..sponsorship import classify_sponsorship
from .base import FetchResult, SourceAdapter, SourceMeta

URL = "https://api.ashbyhq.com/posting-api/job-board/{slug}"


class AshbySource(SourceAdapter):
    meta = SourceMeta(
        name="ashby",
        official_api=True,
        notes="Public posting-api; description included by default.",
    )

    def fetch(
        self,
        *,
        boards: list[dict[str, str]] | None = None,
        role_filter: bool = True,
        max_jobs: int = 200,
        max_per_board: int = 12,
        **_: Any,
    ) -> FetchResult:
        jobs: list[NormalizedJob] = []
        errors: list[str] = []
        for board in boards or []:
            slug = (board.get("token") or "").strip()
            company = (board.get("company") or slug).strip()
            if not slug or slug.startswith("//"):
                continue
            try:
                data = fetch_json(URL.format(slug=slug))
            except Exception as exc:  # noqa: BLE001
                errors.append(f"ashby/{slug}: {exc}")
                continue
            kept = 0
            for row in data.get("jobs") or []:
                if row.get("isListed") is False:
                    continue
                title = (row.get("title") or "").strip()
                if role_filter and not title_matches_roles(title):
                    continue
                url = (row.get("jobUrl") or row.get("applyUrl") or "").strip()
                if not title or not url:
                    continue
                loc = (row.get("location") or "").strip()
                desc = strip_html(row.get("descriptionPlain") or row.get("descriptionHtml") or "")
                published = None
                pub = row.get("publishedAt")
                if isinstance(pub, str) and len(pub) >= 10:
                    published = pub[:10]
                wt = row.get("workplaceType")
                workplace = detect_workplace(loc, desc, explicit=str(wt) if wt else None)
                country = detect_country(loc, desc)
                # Prefer address country when present
                addr = ((row.get("address") or {}).get("postalAddress") or {})
                cc = addr.get("addressCountry")
                if isinstance(cc, str) and len(cc) == 2:
                    country = cc.upper()
                sponsorship = classify_sponsorship(desc, source_url=url)
                jobs.append(
                    NormalizedJob(
                        title=title,
                        company=company,
                        url=url,
                        source="ashby",
                        location=loc,
                        country=country,
                        workplace=workplace,
                        employment_type=row.get("employmentType"),
                        published_date=published,
                        description=desc,
                        salary=(row.get("compensation") or {}).get("compensationTierSummary")
                        if isinstance(row.get("compensation"), dict)
                        else None,
                        sponsorship=sponsorship,
                        status="open",
                        source_job_id=str(row.get("id") or ""),
                        raw={"board": slug},
                    )
                )
                kept += 1
                if kept >= max_per_board or len(jobs) >= max_jobs:
                    break
            if len(jobs) >= max_jobs:
                break
        return FetchResult(jobs=jobs, errors=errors, meta={"boards": len(boards or [])})
