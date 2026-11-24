"""SmartRecruiters public postings API — curated company slugs only.

List:  GET https://api.smartrecruiters.com/v1/companies/{slug}/postings
Detail: GET .../postings/{id}  (description sections)
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

from ..http import fetch_json
from ..model import NormalizedJob
from ..normalize import detect_country, detect_workplace, strip_html, title_matches_roles
from ..sponsorship import classify_sponsorship
from .base import FetchResult, SourceAdapter, SourceMeta

LIST_URL = "https://api.smartrecruiters.com/v1/companies/{slug}/postings"
DETAIL_URL = "https://api.smartrecruiters.com/v1/companies/{slug}/postings/{job_id}"


def _loc_blob(row: dict[str, Any]) -> str:
    loc = row.get("location") or {}
    if not isinstance(loc, dict):
        return str(loc or "")
    parts = [
        str(loc.get(k)).strip()
        for k in ("city", "region", "country")
        if isinstance(loc.get(k), str) and str(loc.get(k)).strip()
    ]
    return ", ".join(parts)


def _detail_desc(detail: dict[str, Any]) -> str:
    ad = detail.get("jobAd") or {}
    sections = ad.get("sections") or {}
    parts: list[str] = []
    if isinstance(sections, dict):
        for key in (
            "companyDescription",
            "jobDescription",
            "qualifications",
            "additionalInformation",
        ):
            block = sections.get(key) or {}
            if isinstance(block, dict):
                text = block.get("text") or ""
                if text:
                    parts.append(str(text))
    return strip_html("\n\n".join(parts))


class SmartRecruitersSource(SourceAdapter):
    meta = SourceMeta(
        name="smartrecruiters",
        official_api=True,
        notes="Public v1 postings API; detail fetch for descriptions.",
    )

    def fetch(
        self,
        *,
        boards: list[dict[str, str]] | None = None,
        role_filter: bool = True,
        fetch_content: bool = True,
        max_jobs: int = 120,
        max_per_board: int = 20,
        **_: Any,
    ) -> FetchResult:
        jobs: list[NormalizedJob] = []
        errors: list[str] = []
        for board in boards or []:
            slug = (board.get("token") or "").strip()
            company = (board.get("company") or slug).strip()
            if not slug or slug.startswith("//") or company.upper() == "SKIP":
                continue
            kept = 0
            offset = 0
            try:
                while True:
                    qs = urlencode({"limit": 100, "offset": offset})
                    data = fetch_json(f"{LIST_URL.format(slug=slug)}?{qs}")
                    rows = data.get("content") or []
                    if not rows:
                        break
                    for row in rows:
                        if not isinstance(row, dict):
                            continue
                        title = (row.get("name") or row.get("title") or "").strip()
                        if role_filter and not title_matches_roles(title):
                            continue
                        job_id = str(row.get("id") or "").strip()
                        url = (
                            row.get("postingUrl")
                            or row.get("applyUrl")
                            or (
                                f"https://jobs.smartrecruiters.com/{slug}/{job_id}"
                                if job_id
                                else ""
                            )
                        )
                        url = str(url).strip()
                        if not title or not url:
                            continue
                        desc = ""
                        if fetch_content and job_id:
                            try:
                                detail = fetch_json(DETAIL_URL.format(slug=slug, job_id=job_id))
                                desc = _detail_desc(detail if isinstance(detail, dict) else {})
                            except Exception as exc:  # noqa: BLE001
                                errors.append(f"smartrecruiters/{slug}/{job_id} detail: {exc}")
                        loc = _loc_blob(row)
                        published = None
                        for key in ("releasedDate", "createdOn"):
                            val = row.get(key)
                            if isinstance(val, str) and len(val) >= 10:
                                published = val[:10]
                                break
                        workplace = detect_workplace(loc, desc)
                        country = detect_country(loc, desc)
                        loc_obj = row.get("location") or {}
                        if isinstance(loc_obj, dict):
                            cc = loc_obj.get("country")
                            if isinstance(cc, str) and len(cc.strip()) == 2:
                                country = cc.strip().upper()
                        sponsorship = classify_sponsorship(desc, source_url=url)
                        jobs.append(
                            NormalizedJob(
                                title=title,
                                company=company,
                                url=url,
                                source="smartrecruiters",
                                location=loc,
                                country=country,
                                workplace=workplace,
                                published_date=published,
                                description=desc,
                                sponsorship=sponsorship,
                                status="open",
                                source_job_id=job_id or None,
                                raw={"board": slug},
                            )
                        )
                        kept += 1
                        if kept >= max_per_board or len(jobs) >= max_jobs:
                            break
                    if kept >= max_per_board or len(jobs) >= max_jobs:
                        break
                    total = data.get("totalFound")
                    offset += len(rows)
                    if total is not None and offset >= int(total):
                        break
                    if len(rows) < 100:
                        break
            except Exception as exc:  # noqa: BLE001
                errors.append(f"smartrecruiters/{slug}: {exc}")
            if len(jobs) >= max_jobs:
                break
        return FetchResult(jobs=jobs, errors=errors, meta={"boards": len(boards or [])})
