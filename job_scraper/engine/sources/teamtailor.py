"""Teamtailor public JSON Feed — curated career-site hosts only.

Endpoint: GET https://{host}/jobs.json  (JSON Feed 1.1, no API key)
Follow ``next_url`` for pagination (100/page). Descriptions in ``content_html``.
"""

from __future__ import annotations

from typing import Any

from ..http import fetch_json
from ..model import NormalizedJob
from ..normalize import detect_country, detect_workplace, strip_html, title_matches_roles
from ..sponsorship import classify_sponsorship
from .base import FetchResult, SourceAdapter, SourceMeta


def _job_location(item: dict[str, Any]) -> str:
    jp = item.get("_jobposting") or {}
    locs = jp.get("jobLocation") or []
    parts: list[str] = []
    if isinstance(locs, dict):
        locs = [locs]
    for loc in locs:
        if not isinstance(loc, dict):
            continue
        addr = loc.get("address") or {}
        if not isinstance(addr, dict):
            continue
        chunk = ", ".join(
            str(addr.get(k)).strip()
            for k in ("addressLocality", "addressRegion", "addressCountry")
            if isinstance(addr.get(k), str) and str(addr.get(k)).strip()
        )
        if chunk:
            parts.append(chunk)
    return "; ".join(parts)


def _job_id(item: dict[str, Any]) -> str:
    jp = item.get("_jobposting") or {}
    ident = jp.get("identifier") if isinstance(jp, dict) else None
    if isinstance(ident, dict):
        val = ident.get("value")
        if val is not None:
            return str(val)
    raw_id = item.get("id")
    if raw_id is None:
        return ""
    # JSON Feed ids look like ".../jobs/12345-slug" — keep trailing numeric when present
    s = str(raw_id)
    if "/jobs/" in s:
        tail = s.rsplit("/jobs/", 1)[-1]
        num = tail.split("-", 1)[0]
        if num.isdigit():
            return num
    return s


class TeamtailorSource(SourceAdapter):
    meta = SourceMeta(
        name="teamtailor",
        official_api=True,
        notes="Public /jobs.json JSON Feed per career host; curated hosts only.",
    )

    def fetch(
        self,
        *,
        boards: list[dict[str, str]] | None = None,
        role_filter: bool = True,
        max_jobs: int = 80,
        max_per_board: int = 30,
        max_pages: int = 3,
        **_: Any,
    ) -> FetchResult:
        jobs: list[NormalizedJob] = []
        errors: list[str] = []

        for board in boards or []:
            token = (board.get("token") or "").strip()
            company = (board.get("company") or token).strip()
            if not token or token.startswith("//") or company.upper() == "SKIP":
                continue
            host = token if "." in token else f"{token}.teamtailor.com"
            feed_url: str | None = f"https://{host}/jobs.json"
            kept = 0
            pages = 0
            company_name = company
            while feed_url and pages < max_pages:
                pages += 1
                try:
                    data = fetch_json(feed_url)
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"teamtailor/{host}: {exc}")
                    break
                if not isinstance(data, dict):
                    errors.append(f"teamtailor/{host}: unexpected payload type")
                    break
                if isinstance(data.get("title"), str) and data["title"].strip():
                    company_name = data["title"].strip()
                for item in data.get("items") or []:
                    if not isinstance(item, dict):
                        continue
                    title = (item.get("title") or "").strip()
                    if role_filter and not title_matches_roles(title):
                        continue
                    url = (item.get("url") or "").strip()
                    if not title or not url:
                        continue
                    loc = _job_location(item)
                    desc = strip_html(item.get("content_html") or item.get("content_text") or "")
                    published = None
                    pub = item.get("date_published")
                    if isinstance(pub, str) and len(pub) >= 10:
                        published = pub[:10]
                    workplace = detect_workplace(loc, desc)
                    country = detect_country(loc, desc)
                    sponsorship = classify_sponsorship(desc, source_url=url)
                    jobs.append(
                        NormalizedJob(
                            title=title,
                            company=company_name,
                            url=url,
                            source="teamtailor",
                            location=loc,
                            country=country,
                            workplace=workplace,
                            published_date=published,
                            description=desc,
                            sponsorship=sponsorship,
                            status="open",
                            source_job_id=_job_id(item) or None,
                            raw={"board": host},
                        )
                    )
                    kept += 1
                    if kept >= max_per_board or len(jobs) >= max_jobs:
                        feed_url = None
                        break
                else:
                    nxt = data.get("next_url")
                    feed_url = nxt if isinstance(nxt, str) and nxt.strip() else None
                    continue
                break
            if len(jobs) >= max_jobs:
                break
        return FetchResult(jobs=jobs, errors=errors, meta={"boards": len(boards or [])})
