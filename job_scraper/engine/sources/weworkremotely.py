"""We Work Remotely public RSS — programming remote jobs (jobdrop-style)."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any
from urllib.request import Request, urlopen

from ..http import UA
from ..model import NormalizedJob
from ..normalize import detect_country, detect_workplace, strip_html, title_matches_roles
from ..sponsorship import classify_sponsorship
from .base import FetchResult, SourceAdapter, SourceMeta

FEED = "https://weworkremotely.com/categories/remote-programming-jobs.rss"


class WeWorkRemotelySource(SourceAdapter):
    meta = SourceMeta(
        name="weworkremotely",
        official_api=True,
        notes="Public WWR programming RSS feed.",
    )

    def fetch(
        self,
        *,
        role_filter: bool = True,
        max_jobs: int = 40,
        **_: Any,
    ) -> FetchResult:
        jobs: list[NormalizedJob] = []
        errors: list[str] = []
        try:
            req = Request(FEED, headers={"User-Agent": UA, "Accept": "application/rss+xml,*/*"})
            with urlopen(req, timeout=30) as resp:  # noqa: S310
                raw = resp.read()
            root = ET.fromstring(raw)
        except Exception as exc:  # noqa: BLE001
            return FetchResult(jobs=[], errors=[f"weworkremotely: {exc}"], meta={})

        channel = root.find("channel")
        items = channel.findall("item") if channel is not None else root.findall(".//item")
        for item in items:
            title_raw = (item.findtext("title") or "").strip()
            # WWR titles often "Company: Role"
            company, title = "We Work Remotely", title_raw
            if ":" in title_raw:
                company, title = [p.strip() for p in title_raw.split(":", 1)]
            if role_filter and not title_matches_roles(title) and not title_matches_roles(title_raw):
                continue
            url = (item.findtext("link") or "").strip()
            if not title or not url:
                continue
            desc = strip_html(item.findtext("description") or "")
            desc = (desc + "\n\nFully remote / work from anywhere (We Work Remotely listing).").strip()
            pub = item.findtext("pubDate")
            published = None
            if pub:
                # leave undated if unparsable; freshness filter keeps undated
                published = None
            loc = "Worldwide Remote"
            workplace = detect_workplace(loc, desc, explicit="remote")
            country = detect_country(loc, desc)
            sponsorship = classify_sponsorship(desc, source_url=url)
            jobs.append(
                NormalizedJob(
                    title=title,
                    company=company,
                    url=url,
                    source="weworkremotely",
                    location=loc,
                    country=country,
                    workplace=workplace,
                    published_date=published,
                    description=desc,
                    sponsorship=sponsorship,
                    status="open",
                    source_job_id=None,
                    raw={"board": "weworkremotely"},
                )
            )
            if len(jobs) >= max_jobs:
                break
        return FetchResult(jobs=jobs, errors=errors, meta={"feed": FEED})
