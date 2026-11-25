"""Zero-repeat freshness: fingerprints, applied blocklist, N-day kill switch.

Hard rule: listings older than ``MAX_LISTING_AGE_DAYS`` (3 months) are dropped
everywhere — posted date, LinkedIn activity snowflake, or relative age text.
"""

from __future__ import annotations

import hashlib
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit

from agent.models.opportunity import OpportunityRecord, norm_key

ROOT = Path(__file__).resolve().parents[2]

# Global ceiling: keep only listings from the last ~3 months
MAX_LISTING_AGE_DAYS = 90

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

# LinkedIn / UI relative ages: "4mo", "3 months ago", "2w", "12d", "5yr"
_RELATIVE_AGE = re.compile(
    r"(?i)\b(\d+)\s*"
    r"(years?|yrs?|y|months?|mos?|mo|weeks?|wks?|w|days?|d|hours?|hrs?|h|minutes?|mins?|m)"
    r"(?:\s+ago)?\b"
)
_LINKEDIN_ACTIVITY = re.compile(
    r"(?i)(?:activity|ugcPost|share)[_:-]?(\d{15,22})"
)


def fingerprint(company: str, title: str, url: str = "") -> str:
    """Stable company+title+URL fingerprint for zero-repeat."""
    host_path = ""
    u = (url or "").strip().rstrip("/")
    if u:
        parts = urlsplit(u)
        host_path = f"{parts.netloc}{parts.path}".rstrip("/").casefold()
    raw = f"{norm_key(company)}|{norm_key(title)}|{host_path}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _parse_day(value: str) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def relative_age_to_date(text: str, *, today: date | None = None) -> date | None:
    """Parse first relative age token (e.g. ``4mo``, ``3 months ago``) → approx date."""
    if not text:
        return None
    today = today or date.today()
    m = _RELATIVE_AGE.search(str(text))
    if not m:
        return None
    n = int(m.group(1))
    unit = m.group(2).lower()
    if unit.startswith("y"):
        days = n * 365
    elif unit.startswith("mo") or unit in ("month", "months"):
        days = n * 30
    elif unit.startswith("w"):
        days = n * 7
    elif unit.startswith("d"):
        days = n
    elif unit.startswith("h"):
        days = 0 if n < 48 else 1
    elif unit in ("m", "min", "mins", "minute", "minutes"):
        days = 0
    else:
        return None
    return today - timedelta(days=days)


def linkedin_activity_posted_date(url: str) -> date | None:
    """Decode LinkedIn activity/ugcPost snowflake (id >> 22 → ms since epoch)."""
    if not url or "linkedin.com" not in url.casefold():
        return None
    m = _LINKEDIN_ACTIVITY.search(url)
    if not m:
        return None
    try:
        activity_id = int(m.group(1))
        ms = activity_id >> 22
        if ms < 1_000_000_000_000 or ms > 2_500_000_000_000:
            return None
        return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).date()
    except (ValueError, OSError, OverflowError):
        return None


def infer_posted_date(rec: OpportunityRecord, *, today: date | None = None) -> date | None:
    """Best posted/published day from explicit date, LinkedIn URL, or relative age text."""
    today = today or date.today()
    posted = _parse_day(rec.posted_date)
    if posted:
        return posted

    li = linkedin_activity_posted_date(rec.source_url or "")
    if li:
        return li

    blob = " ".join(
        [
            str(rec.evidence or ""),
            str(rec.description or ""),
            str(rec.notes or ""),
            str(rec.raw_json or ""),
            str(rec.role_or_title or ""),
        ]
    )
    return relative_age_to_date(blob, today=today)


def listing_age_days(rec: OpportunityRecord, *, today: date | None = None) -> int | None:
    """Age in days when we can infer a post date; else None (unknown)."""
    today = today or date.today()
    day = infer_posted_date(rec, today=today)
    if day is None:
        return None
    return (today - day).days


def is_too_old(
    rec: OpportunityRecord,
    *,
    max_age_days: int = MAX_LISTING_AGE_DAYS,
    today: date | None = None,
) -> tuple[bool, str]:
    """Hard drop when listing is older than ``max_age_days`` (~3 months)."""
    if max_age_days <= 0:
        return False, ""
    age = listing_age_days(rec, today=today)
    if age is None:
        return False, ""
    if age > max_age_days:
        return True, f"stale_older_than_{max_age_days}d_age_{age}d"
    return False, ""


def enrich_posted_date(rec: OpportunityRecord) -> None:
    """Fill empty ``posted_date`` from LinkedIn snowflake / relative age when possible."""
    if _parse_day(rec.posted_date):
        return
    inferred = infer_posted_date(rec)
    if inferred:
        rec.posted_date = inferred.isoformat()


def load_blocked_companies(
    block_path: Path | None = None,
    tracker_path: Path | None = None,
) -> set[str]:
    """Reuse job_scraper blocklist + tracker applied companies."""
    try:
        from job_scraper.engine.freshness import load_blocked_companies as _load

        return _load(
            str(block_path) if block_path else None,
            str(tracker_path) if tracker_path else None,
        )
    except Exception:  # noqa: BLE001
        companies: set[str] = set()
        path = block_path or (ROOT / "job_scraper" / "block_companies.txt")
        if path.is_file():
            for line in path.read_text(encoding="utf-8").splitlines():
                name = line.split("#", 1)[0].strip()
                if name:
                    companies.add(norm_key(name))
        return companies


def index_from_excel_rows(rows: Iterable[OpportunityRecord]) -> dict[str, Any]:
    """Build seen fingerprints / urls / pairs / blocked from current workbook."""
    fps: set[str] = set()
    urls: set[str] = set()
    pairs: set[tuple[str, str]] = set()
    blocked: set[str] = set()
    recent: dict[str, date] = {}  # fingerprint -> discovered/posted day

    for r in rows:
        fp = fingerprint(r.company, r.role_or_title, r.source_url)
        fps.add(fp)
        pair = (norm_key(r.company), norm_key(r.role_or_title))
        pairs.add(pair)
        if r.source_url:
            urls.add(r.source_url.rstrip("/"))
        day = _parse_day(r.posted_date) or _parse_day(r.discovered_date)
        if day:
            recent[fp] = max(day, recent.get(fp, day))
        status = (r.status or "").strip().lower()
        if status in _APPLIED_STATUSES and r.company:
            blocked.add(norm_key(r.company))
    return {
        "fingerprints": fps,
        "urls": urls,
        "pairs": pairs,
        "blocked": blocked,
        "recent": recent,
    }


def merge_external_seen(index: dict[str, Any]) -> dict[str, Any]:
    """Fold seen_jobs.json + tracker into the Excel index."""
    try:
        from job_scraper.engine.freshness import load_seen_identities

        urls, pairs = load_seen_identities()
        index["urls"] = set(index.get("urls") or set()) | urls
        index["pairs"] = set(index.get("pairs") or set()) | pairs
    except Exception:  # noqa: BLE001
        pass
    blocked_ext = load_blocked_companies()
    index["blocked"] = set(index.get("blocked") or set()) | blocked_ext
    return index


def is_repeat(
    rec: OpportunityRecord,
    index: dict[str, Any],
    *,
    kill_days: int = 14,
    max_age_days: int = MAX_LISTING_AGE_DAYS,
) -> tuple[bool, str]:
    """Return (drop?, reason)."""
    company = norm_key(rec.company)
    if company and company in (index.get("blocked") or set()):
        return True, "blocked_company_applied_or_list"

    # Absolute age ceiling (3 months) — applies to all opportunity types
    too_old, why = is_too_old(rec, max_age_days=max_age_days)
    if too_old:
        return True, why

    fp = fingerprint(rec.company, rec.role_or_title, rec.source_url)
    url = (rec.source_url or "").rstrip("/")
    pair = (company, norm_key(rec.role_or_title))

    if url and url in (index.get("urls") or set()):
        # Allow refresh if already in workbook (upsert) — caller decides NEW vs update.
        # For zero-repeat NEW: treat as repeat.
        return True, "seen_url"
    if pair in (index.get("pairs") or set()) and pair != ("", ""):
        return True, "seen_company_title"
    if fp in (index.get("fingerprints") or set()):
        return True, "seen_fingerprint"

    recent: dict[str, date] = index.get("recent") or {}
    if kill_days > 0 and fp in recent:
        age = (date.today() - recent[fp]).days
        if age <= kill_days:
            return True, f"seen_within_{kill_days}d"

    return False, ""


def register_kept(rec: OpportunityRecord, index: dict[str, Any]) -> None:
    """Add a kept record into the in-memory index (batch dedupe)."""
    fp = fingerprint(rec.company, rec.role_or_title, rec.source_url)
    index.setdefault("fingerprints", set()).add(fp)
    index.setdefault("pairs", set()).add((norm_key(rec.company), norm_key(rec.role_or_title)))
    if rec.source_url:
        index.setdefault("urls", set()).add(rec.source_url.rstrip("/"))
    day = _parse_day(rec.posted_date) or _parse_day(rec.discovered_date) or date.today()
    index.setdefault("recent", {})[fp] = day
