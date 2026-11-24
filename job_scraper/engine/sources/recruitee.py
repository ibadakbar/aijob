"""Recruitee public offers API — curated tenant slugs only.

GET https://{slug}.recruitee.com/api/offers — full descriptions inline.
"""

from __future__ import annotations

from typing import Any

from ..http import fetch_json
from ..model import NormalizedJob
from ..normalize import detect_country, detect_workplace, strip_html, title_matches_roles
from ..sponsorship import classify_sponsorship
from .base import FetchResult, SourceAdapter, SourceMeta


class RecruiteeSource(SourceAdapter):
    meta = SourceMeta(
        name="recruitee",
        official_api=True,
        notes="Public /api/offers JSON per tenant; curated slugs only.",
    )

    def fetch(
        self,
        *,
        boards: list[dict[str, str]] | None = None,
        role_filter: bool = True,
        max_jobs: int = 120,
        max_per_board: int = 25,
        **_: Any,
    ) -> FetchResult:
        jobs: list[NormalizedJob] = []
        errors: list[str] = []
        for board in boards or []:
            slug = (board.get("token") or "").strip()
            company = (board.get("company") or slug).strip()
            if not slug or slug.startswith("//") or company.upper() == "SKIP":
                continue
            if slug.startswith("http://") or slug.startswith("https://"):
                host = slug.rstrip("/")
                api = f"{host}/api/offers"
            else:
                api = f"https://{slug}.recruitee.com/api/offers"
            try:
                data = fetch_json(api)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"recruitee/{slug}: {exc}")
                continue
            offers = data.get("offers") if isinstance(data, dict) else None
            if not isinstance(offers, list):
                errors.append(f"recruitee/{slug}: unexpected payload")
                continue
            kept = 0
            for row in offers:
                if not isinstance(row, dict):
                    continue
                if row.get("status") and str(row.get("status")).lower() not in ("published", "open", ""):
                    # keep when status absent
                    if str(row.get("status")).lower() in ("closed", "archived", "draft"):
                        continue
                title = (row.get("title") or "").strip()
                if role_filter and not title_matches_roles(title):
                    continue
                url = (row.get("careers_url") or row.get("url") or "").strip()
                if not title or not url:
                    continue
                loc_parts = []
                for key in ("location", "city", "country_code", "country"):
                    val = row.get(key)
                    if isinstance(val, str) and val.strip():
                        loc_parts.append(val.strip())
                loc = ", ".join(dict.fromkeys(loc_parts))
                desc = strip_html(
                    "\n\n".join(
                        str(row.get(k) or "")
                        for k in ("description", "requirements", "offer_description")
                        if row.get(k)
                    )
                )
                published = None
                for key in ("published_at", "created_at", "updated_at"):
                    val = row.get(key)
                    if isinstance(val, str) and len(val) >= 10:
                        published = val[:10]
                        break
                remote_flag = row.get("remote") or row.get("remote_anywhere")
                explicit = "remote" if remote_flag in (True, "true", "yes", 1) else None
                workplace = detect_workplace(loc, desc, explicit=explicit)
                country = detect_country(loc, desc)
                cc = row.get("country_code")
                if isinstance(cc, str) and len(cc.strip()) == 2:
                    country = cc.strip().upper()
                sponsorship = classify_sponsorship(desc, source_url=url)
                company_name = (row.get("company_name") or company).strip() or company
                jobs.append(
                    NormalizedJob(
                        title=title,
                        company=company_name,
                        url=url,
                        source="recruitee",
                        location=loc,
                        country=country,
                        workplace=workplace,
                        employment_type=row.get("employment_type_code") or row.get("employment_type"),
                        published_date=published,
                        description=desc,
                        sponsorship=sponsorship,
                        status="open",
                        source_job_id=str(row.get("id") or "") or None,
                        raw={"board": slug},
                    )
                )
                kept += 1
                if kept >= max_per_board or len(jobs) >= max_jobs:
                    break
            if len(jobs) >= max_jobs:
                break
        return FetchResult(jobs=jobs, errors=errors, meta={"boards": len(boards or [])})
