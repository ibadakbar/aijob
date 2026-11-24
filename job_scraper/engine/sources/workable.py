"""Workable public widget API — curated account shortcodes only.

Endpoint: GET https://apply.workable.com/api/v1/widget/accounts/{shortcode}?details=true
No auth. ``details=true`` includes full HTML descriptions (required for Path A/B).
"""

from __future__ import annotations

from typing import Any

from ..http import fetch_json
from ..model import NormalizedJob
from ..normalize import detect_country, detect_workplace, strip_html, title_matches_roles
from ..sponsorship import classify_sponsorship
from .base import FetchResult, SourceAdapter, SourceMeta

URL = "https://apply.workable.com/api/v1/widget/accounts/{shortcode}?details=true"


def _location_blob(row: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("city", "state", "country"):
        val = row.get(key)
        if isinstance(val, str) and val.strip():
            parts.append(val.strip())
    locs = row.get("locations") or []
    if isinstance(locs, list):
        for loc in locs:
            if not isinstance(loc, dict):
                continue
            if loc.get("hidden"):
                continue
            chunk = ", ".join(
                str(loc.get(k)).strip()
                for k in ("city", "state", "country")
                if isinstance(loc.get(k), str) and str(loc.get(k)).strip()
            )
            if chunk:
                parts.append(chunk)
    # de-dupe while preserving order
    seen: set[str] = set()
    out: list[str] = []
    for p in parts:
        if p.lower() not in seen:
            seen.add(p.lower())
            out.append(p)
    return "; ".join(out)


class WorkableSource(SourceAdapter):
    meta = SourceMeta(
        name="workable",
        official_api=True,
        notes="Public widget API; details=true for descriptions. Curated shortcodes only.",
    )

    def fetch(
        self,
        *,
        boards: list[dict[str, str]] | None = None,
        role_filter: bool = True,
        max_jobs: int = 80,
        max_per_board: int = 30,
        **_: Any,
    ) -> FetchResult:
        jobs: list[NormalizedJob] = []
        errors: list[str] = []
        seen_shortcodes: set[str] = set()

        for board in boards or []:
            shortcode = (board.get("token") or "").strip()
            company = (board.get("company") or shortcode).strip()
            if not shortcode or shortcode.startswith("//") or company.upper() == "SKIP":
                continue
            try:
                data = fetch_json(URL.format(shortcode=shortcode))
            except Exception as exc:  # noqa: BLE001
                errors.append(f"workable/{shortcode}: {exc}")
                continue
            if not isinstance(data, dict):
                errors.append(f"workable/{shortcode}: unexpected payload type")
                continue
            company_name = (data.get("name") or company).strip() or company
            kept = 0
            for row in data.get("jobs") or []:
                if not isinstance(row, dict):
                    continue
                title = (row.get("title") or "").strip()
                if role_filter and not title_matches_roles(title):
                    continue
                sc = str(row.get("shortcode") or row.get("code") or "").strip()
                # Widget repeats one shortcode per location — keep first, merge later via dedupe.
                if sc and sc in seen_shortcodes:
                    continue
                url = (
                    (row.get("url") or row.get("application_url") or row.get("shortlink") or "")
                    .strip()
                )
                if not title or not url:
                    continue
                if sc:
                    seen_shortcodes.add(sc)
                loc = _location_blob(row)
                desc = strip_html(row.get("description") or "")
                published = None
                for key in ("published_on", "created_at"):
                    val = row.get(key)
                    if isinstance(val, str) and len(val) >= 10:
                        published = val[:10]
                        break
                tele = row.get("telecommuting")
                explicit = "remote" if tele is True else None
                workplace = detect_workplace(loc, desc, explicit=explicit)
                country = detect_country(loc, desc)
                cc = row.get("country")
                if isinstance(cc, str) and len(cc.strip()) == 2:
                    country = cc.strip().upper()
                sponsorship = classify_sponsorship(desc, source_url=url)
                jobs.append(
                    NormalizedJob(
                        title=title,
                        company=company_name,
                        url=url,
                        source="workable",
                        location=loc,
                        country=country,
                        workplace=workplace,
                        employment_type=row.get("employment_type"),
                        published_date=published,
                        description=desc,
                        sponsorship=sponsorship,
                        status="open",
                        source_job_id=sc or None,
                        raw={"board": shortcode},
                    )
                )
                kept += 1
                if kept >= max_per_board or len(jobs) >= max_jobs:
                    break
            if len(jobs) >= max_jobs:
                break
        return FetchResult(jobs=jobs, errors=errors, meta={"boards": len(boards or [])})
