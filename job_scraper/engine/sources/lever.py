"""Lever public Postings API — curated site names only."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

from ..http import fetch_json
from ..model import NormalizedJob
from ..normalize import detect_country, detect_workplace, strip_html, title_matches_roles
from ..sponsorship import classify_sponsorship
from .base import FetchResult, SourceAdapter, SourceMeta

URL = "https://api.lever.co/v0/postings/{site}"


class LeverSource(SourceAdapter):
    meta = SourceMeta(
        name="lever",
        official_api=True,
        notes="Public postings API; mode=json. EU host api.eu.lever.co not auto-probed.",
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
            site = (board.get("token") or "").strip()
            company = (board.get("company") or site).strip()
            if not site or site.startswith("//"):
                continue
            qs = urlencode({"mode": "json", "limit": 100})
            try:
                data = fetch_json(f"{URL.format(site=site)}?{qs}")
            except Exception as exc:  # noqa: BLE001
                errors.append(f"lever/{site}: {exc}")
                continue
            if not isinstance(data, list):
                errors.append(f"lever/{site}: unexpected payload type")
                continue
            kept = 0
            for row in data:
                title = (row.get("text") or row.get("title") or "").strip()
                if role_filter and not title_matches_roles(title):
                    continue
                url = (row.get("hostedUrl") or row.get("applyUrl") or "").strip()
                if not title or not url:
                    continue
                cats = row.get("categories") or {}
                loc = (cats.get("location") or row.get("location") or "")
                if isinstance(loc, dict):
                    loc = loc.get("name") or ""
                desc = strip_html(row.get("descriptionPlain") or row.get("description") or "")
                # Lever lists often include structured lists
                for block in row.get("lists") or []:
                    content = block.get("content") if isinstance(block, dict) else None
                    if content:
                        desc += "\n" + strip_html(str(content))
                published = None
                created = row.get("createdAt")
                if isinstance(created, (int, float)):
                    from datetime import datetime

                    try:
                        published = datetime.utcfromtimestamp(created / 1000).date().isoformat()
                    except (OverflowError, OSError, ValueError):
                        published = None
                workplace = detect_workplace(str(loc), desc)
                country = detect_country(str(loc), desc)
                sponsorship = classify_sponsorship(desc, source_url=url)
                jobs.append(
                    NormalizedJob(
                        title=title,
                        company=company,
                        url=url,
                        source="lever",
                        location=str(loc),
                        country=country,
                        workplace=workplace,
                        employment_type=cats.get("commitment"),
                        published_date=published,
                        description=desc,
                        sponsorship=sponsorship,
                        status="open",
                        source_job_id=str(row.get("id") or ""),
                        raw={"board": site},
                    )
                )
                kept += 1
                if kept >= max_per_board or len(jobs) >= max_jobs:
                    break
            if len(jobs) >= max_jobs:
                break
        return FetchResult(jobs=jobs, errors=errors, meta={"boards": len(boards or [])})
