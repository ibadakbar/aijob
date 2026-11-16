"""Cross-source deduplication for normalized jobs."""

from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit

from .model import NormalizedJob

_SOURCE_RANK = {
    "greenhouse": 0,
    "ashby": 0,
    "lever": 0,
    "arbeitnow": 1,
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


def _better(a: NormalizedJob, b: NormalizedJob) -> NormalizedJob:
    ra = _SOURCE_RANK.get(a.source, 9)
    rb = _SOURCE_RANK.get(b.source, 9)
    if ra != rb:
        return a if ra < rb else b
    return a if len(a.description or "") >= len(b.description or "") else b


def dedupe_jobs(jobs: list[NormalizedJob]) -> list[NormalizedJob]:
    """Collapse duplicates by normalized URL, then by company+title."""
    winners: dict[str, NormalizedJob] = {}
    url_to_ct: dict[str, str] = {}

    for job in jobs:
        url_key = normalize_url(job.url)
        ct = company_title_key(job.company, job.title)
        if url_key in winners:
            winners[url_key] = _better(winners[url_key], job)
            continue
        # Same company+title already kept under another URL?
        existing_url = next((u for u, c in url_to_ct.items() if c == ct), None)
        if existing_url is not None:
            winners[existing_url] = _better(winners[existing_url], job)
            continue
        winners[url_key] = job
        url_to_ct[url_key] = ct

    out: list[NormalizedJob] = []
    for url_key, job in winners.items():
        job.dedupe_key = url_to_ct[url_key]
        out.append(job)
    return out
