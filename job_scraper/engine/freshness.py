"""Freshness and new-only filters (inspired by mherzog4/job-boards --since / --new-only)."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional
from urllib.parse import urlsplit

from .model import NormalizedJob


def parse_since(value: str | int | None) -> Optional[int]:
    """Parse ``7d``, ``2w``, ``30``, or int → days. None means no filter."""
    if value is None:
        return None
    if isinstance(value, int):
        return max(0, value)
    s = str(value).strip().lower()
    if not s:
        return None
    if s.isdigit():
        return int(s)
    unit = s[-1]
    num = s[:-1]
    if not num.isdigit():
        raise ValueError(f"invalid --since value: {value!r}")
    n = int(num)
    if unit == "d":
        return n
    if unit == "w":
        return n * 7
    if unit == "m":
        return n * 30
    raise ValueError(f"invalid --since unit in {value!r} (use d/w/m)")


def _pub_day(job: NormalizedJob) -> Optional[date]:
    if not job.published_date:
        return None
    try:
        return datetime.strptime(job.published_date[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def filter_since(jobs: list[NormalizedJob], days: Optional[int]) -> list[NormalizedJob]:
    """Keep jobs with published_date within N days, or unknown date (do not drop undated)."""
    if days is None:
        return jobs
    cutoff = date.today() - timedelta(days=days)
    out: list[NormalizedJob] = []
    for job in jobs:
        pub = _pub_day(job)
        if pub is None or pub >= cutoff:
            out.append(job)
    return out


def _norm(s: str) -> str:
    return "".join(ch for ch in (s or "").lower() if ch.isalnum())


_APPLIED_STATUSES = frozenset(
    {
        "applied",
        "rejected",
        "closed",
        "interview",
        "offer",
        "withdrawn",
        "skipped",
        "expired",
    }
)


def load_blocked_companies(
    block_path: str | None = None,
    tracker_path: str | None = None,
) -> set[str]:
    """Companies already applied/rejected (or manually blocked) — drop any title."""
    import csv
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent.parent
    companies: set[str] = set()
    path = Path(block_path) if block_path else root / "job_scraper" / "block_companies.txt"
    track_path = Path(tracker_path) if tracker_path else root / "job_search_tracker.csv"

    if path.exists():
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                name = line.split("#", 1)[0].strip()
                if name:
                    companies.add(_norm(name))
        except OSError:
            pass

    if track_path.exists():
        try:
            with track_path.open(encoding="utf-8-sig", newline="") as fh:
                for row in csv.DictReader(fh):
                    status = (row.get("status") or "").strip().lower()
                    if status and status not in _APPLIED_STATUSES:
                        continue
                    company = row.get("company") or row.get("Company") or ""
                    if company.strip():
                        companies.add(_norm(company))
        except OSError:
            pass
    return companies


def load_seen_identities(
    seen_jobs_path: str | None = None,
    tracker_path: str | None = None,
) -> tuple[set[str], set[tuple[str, str]]]:
    """Load URL + company/title identities from seen_jobs + tracker (best-effort)."""
    import csv
    import json
    from pathlib import Path

    urls: set[str] = set()
    pairs: set[tuple[str, str]] = set()
    root = Path(__file__).resolve().parent.parent.parent
    seen_path = Path(seen_jobs_path) if seen_jobs_path else root / "job_scraper" / "seen_jobs.json"
    track_path = Path(tracker_path) if tracker_path else root / "job_search_tracker.csv"

    if seen_path.exists():
        try:
            data = json.loads(seen_path.read_text(encoding="utf-8"))
            # scrape_state writes {"seen": {key: entry}}; older shapes used "jobs" or a bare list.
            if isinstance(data, dict):
                entries = data.get("seen")
                if entries is None:
                    entries = data.get("jobs")
                if entries is None and all(isinstance(v, dict) for v in data.values()):
                    entries = data
            else:
                entries = data
            if isinstance(entries, dict):
                entries = list(entries.values())
            for entry in entries or []:
                if not isinstance(entry, dict):
                    continue
                url = entry.get("url")
                if isinstance(url, str) and url.strip():
                    urls.add(url.rstrip("/"))
                pairs.add((_norm(str(entry.get("company") or "")), _norm(str(entry.get("title") or ""))))
        except (OSError, json.JSONDecodeError, TypeError):
            pass

    if track_path.exists():
        try:
            with track_path.open(encoding="utf-8", newline="") as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    url = (row.get("url") or row.get("URL") or row.get("source") or "").strip()
                    if url.startswith("http"):
                        urls.add(url.rstrip("/"))
                    pairs.add(
                        (
                            _norm(row.get("company") or row.get("Company") or ""),
                            _norm(row.get("title") or row.get("Title") or row.get("role") or ""),
                        )
                    )
        except OSError:
            pass
    return urls, pairs


def filter_new_only(
    jobs: list[NormalizedJob],
    *,
    seen_urls: set[str],
    seen_pairs: set[tuple[str, str]],
    blocked_companies: set[str] | None = None,
) -> list[NormalizedJob]:
    blocked = blocked_companies or set()
    out: list[NormalizedJob] = []
    for job in jobs:
        url = (job.url or "").rstrip("/")
        company = _norm(job.company)
        pair = (company, _norm(job.title))
        if company and company in blocked:
            continue
        if url in seen_urls or pair in seen_pairs:
            continue
        # also fold queryless host+path
        parts = urlsplit(url)
        if parts.scheme and parts.netloc:
            bare = f"{parts.scheme}://{parts.netloc}{parts.path}".rstrip("/")
            if bare in seen_urls:
                continue
        out.append(job)
    return out
