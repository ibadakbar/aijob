"""Cross-source deduplication for normalized jobs."""

from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit

from .model import NormalizedJob

_SOURCE_RANK = {
    "greenhouse": 0,
    "ashby": 0,
    "lever": 0,
    "workable": 0,
    "personio": 0,
    "teamtailor": 0,
    "smartrecruiters": 0,
    "recruitee": 0,
    "hiringcafe": 0,
    "landingjobs": 1,
    "arbeitnow": 1,
    "remoteok": 2,
    "weworkremotely": 2,
    "jobspy": 2,
    "freehire": 2,
    "linkedin": 2,
}


def normalize_url(url: str) -> str:
    parts = urlsplit((url or "").strip())
    if not parts.scheme or not parts.netloc:
        return (url or "").rstrip("/").lower()
    path = parts.path.rstrip("/") or "/"
    host = parts.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return urlunsplit((parts.scheme.lower(), host, path, "", "")).lower()


def company_title_key(company: str, title: str) -> str:
    def fold(s: str) -> str:
        return "".join(ch for ch in (s or "").lower() if ch.isalnum())

    return f"{fold(company)}::{fold(title)}"


def ats_job_key(job: NormalizedJob) -> str | None:
    """Stable ATS identity: source + source_job_id when both present."""
    sid = (job.source_job_id or "").strip()
    src = (job.source or "").strip().lower()
    if not sid or not src:
        return None
    return f"{src}::{sid}"


def _better(a: NormalizedJob, b: NormalizedJob) -> NormalizedJob:
    ra = _SOURCE_RANK.get(a.source, 9)
    rb = _SOURCE_RANK.get(b.source, 9)
    if ra != rb:
        return a if ra < rb else b
    return a if len(a.description or "") >= len(b.description or "") else b


def dedupe_jobs(jobs: list[NormalizedJob]) -> list[NormalizedJob]:
    """Collapse duplicates by ATS id, then normalized URL, then company+title."""
    winners: dict[str, NormalizedJob] = {}
    url_to_ct: dict[str, str] = {}
    ats_to_url: dict[str, str] = {}

    for job in jobs:
        url_key = normalize_url(job.url)
        ct = company_title_key(job.company, job.title)
        ats = ats_job_key(job)

        # 1) Same ATS job id already kept under another URL?
        if ats and ats in ats_to_url:
            existing = ats_to_url[ats]
            winners[existing] = _better(winners[existing], job)
            continue

        if url_key in winners:
            winners[url_key] = _better(winners[url_key], job)
            if ats:
                ats_to_url[ats] = url_key
            continue

        # 2) Same company+title already kept under another URL?
        existing_url = next((u for u, c in url_to_ct.items() if c == ct), None)
        if existing_url is not None:
            winners[existing_url] = _better(winners[existing_url], job)
            if ats:
                ats_to_url[ats] = existing_url
            continue

        winners[url_key] = job
        url_to_ct[url_key] = ct
        if ats:
            ats_to_url[ats] = url_key

    out: list[NormalizedJob] = []
    for url_key, job in winners.items():
        job.dedupe_key = ats_job_key(job) or url_to_ct[url_key]
        out.append(job)
    return out
