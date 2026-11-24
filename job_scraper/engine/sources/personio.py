"""Personio public XML job feed — curated hostnames only.

Endpoint: GET https://{company}.jobs.personio.{com|de}/xml?language=en
No auth. Descriptions are included as HTML in <jobDescriptions>.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any
from urllib.request import Request, urlopen

from ..http import UA
from ..model import NormalizedJob
from ..normalize import detect_country, detect_workplace, strip_html, title_matches_roles
from ..sponsorship import classify_sponsorship
from .base import FetchResult, SourceAdapter, SourceMeta


def _text(el: ET.Element | None) -> str:
    if el is None or el.text is None:
        return ""
    return el.text.strip()


def _fetch_xml(url: str, *, timeout: float = 30.0) -> bytes:
    req = Request(url, headers={"User-Agent": UA, "Accept": "application/xml,text/xml,*/*"})
    with urlopen(req, timeout=timeout) as resp:  # noqa: S310 — curated HTTPS hosts only
        return resp.read()


def _description(position: ET.Element) -> str:
    parts: list[str] = []
    for block in position.findall("./jobDescriptions/jobDescription"):
        name = _text(block.find("name"))
        value = _text(block.find("value"))
        if name and value:
            parts.append(f"{name}\n{value}")
        elif value:
            parts.append(value)
    return strip_html("\n\n".join(parts))


class PersonioSource(SourceAdapter):
    meta = SourceMeta(
        name="personio",
        official_api=True,
        notes="Public XML feed per employer host; curated hosts only.",
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

        for board in boards or []:
            # token = full host (e.g. casavi.jobs.personio.com) OR slug → .jobs.personio.com
            token = (board.get("token") or "").strip()
            company = (board.get("company") or token).strip()
            if not token or token.startswith("//") or company.upper() == "SKIP":
                continue
            if "." in token:
                host = token
            else:
                host = f"{token}.jobs.personio.com"
            url = f"https://{host}/xml?language=en"
            try:
                raw = _fetch_xml(url)
                root = ET.fromstring(raw)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"personio/{host}: {exc}")
                continue
            kept = 0
            for position in root.findall("position"):
                title = _text(position.find("name"))
                if role_filter and not title_matches_roles(title):
                    continue
                job_id = _text(position.find("id"))
                office = _text(position.find("office"))
                department = _text(position.find("department"))
                employment = _text(position.find("employmentType"))
                schedule = _text(position.find("schedule"))
                created = _text(position.find("createdAt"))
                loc_parts = [p for p in (office, department) if p]
                loc = ", ".join(loc_parts)
                desc = _description(position)
                if schedule:
                    desc = f"{desc}\n\nSchedule: {schedule}".strip()
                apply_url = f"https://{host}/job/{job_id}?language=en" if job_id else f"https://{host}"
                workplace = detect_workplace(loc, desc)
                # Personio often encodes remote in office name
                if "remote" in office.lower() or "home office" in office.lower():
                    workplace = "remote"
                country = detect_country(loc, desc)
                sponsorship = classify_sponsorship(desc, source_url=apply_url)
                published = created[:10] if len(created) >= 10 else None
                sub = _text(position.find("subcompany"))
                company_name = sub or company
                jobs.append(
                    NormalizedJob(
                        title=title,
                        company=company_name,
                        url=apply_url,
                        source="personio",
                        location=loc or office,
                        country=country,
                        workplace=workplace,
                        employment_type=employment or None,
                        published_date=published,
                        description=desc,
                        sponsorship=sponsorship,
                        status="open",
                        source_job_id=job_id or None,
                        raw={"board": host},
                    )
                )
                kept += 1
                if kept >= max_per_board or len(jobs) >= max_jobs:
                    break
            if len(jobs) >= max_jobs:
                break
        return FetchResult(jobs=jobs, errors=errors, meta={"boards": len(boards or [])})
