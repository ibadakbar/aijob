"""Incremental discovery: fetch only when the search changed, keep new or updated rows."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from .dedupe import company_title_key, domain_of, normalize_url
from .model import Lead, SearchCriteria
from .persist import DEFAULT_STORE, atomic_write_json

FETCH_TTL_HOURS = 12


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def utcnow_iso() -> str:
    return utcnow().replace(microsecond=0).isoformat()


def runtime_paths(store_path: Path | None = None) -> dict[str, Path]:
    base = (store_path or DEFAULT_STORE).parent
    return {
        "base": base,
        "state": base / "discovery_state.json",
        "cache": base / "research_cache.json",
        "evidence": base / "evidence.jsonl",
        "runs": base / "runs",
    }


def content_fingerprint(lead: Lead) -> str:
    """Stable hash of the fields that make a vacancy worth scoring again."""
    excerpts = " ".join((e.excerpt or e.summary or "") for e in lead.evidence)[:500]
    raw = "|".join(
        [
            normalize_url(lead.url),
            company_title_key(lead.company, lead.title),
            lead.published_date or "",
            excerpts,
            "1" if lead.expired else "0",
            lead.intent or "",
        ]
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def query_fingerprint(criteria: SearchCriteria, source: str) -> str:
    payload = json.dumps(
        {
            "source": source,
            "technologies": sorted(t.lower() for t in criteria.technologies),
            "lead_types": sorted(criteria.lead_types),
            "geographies": sorted(criteria.geographies),
            "workplace": sorted(criteria.workplace),
            "freshness_days": criteria.freshness_days,
            "query_text": criteria.query_text,
            "limit": criteria.limit,
            "require_sponsorship": criteria.require_sponsorship,
            "require_relocation": criteria.require_relocation,
            "excluded_companies": sorted(c.lower() for c in criteria.excluded_companies),
        },
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def empty_state() -> dict[str, Any]:
    return {"version": 1, "sources": {}, "logged": {}}


def load_state(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return empty_state()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return empty_state()
    if not isinstance(data, dict):
        return empty_state()
    data.setdefault("version", 1)
    data.setdefault("sources", {})
    data.setdefault("logged", {})
    return data


def save_state(path: Path, state: dict[str, Any]) -> None:
    atomic_write_json(path, state)


def _parse_iso(value: str) -> Optional[datetime]:
    try:
        ts = datetime.fromisoformat(value)
    except ValueError:
        return None
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts


def fetch_is_fresh(entry: dict[str, Any], query: str, *, now: Optional[datetime] = None) -> bool:
    if entry.get("query") != query:
        return False
    ts = _parse_iso(str(entry.get("fetched_at") or ""))
    if ts is None:
        return False
    current = now or utcnow()
    return current - ts < timedelta(hours=FETCH_TTL_HOURS)


def merged_records(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for entry in (state.get("sources") or {}).values():
        records = entry.get("records") or {}
        if isinstance(records, dict):
            merged.update(records)
    return merged


def remember_fetch(
    state: dict[str, Any],
    *,
    source: str,
    query: str,
    leads: list[Lead],
) -> None:
    records: dict[str, dict[str, str]] = {}
    for lead in leads:
        url = normalize_url(lead.url)
        if not url:
            continue
        digest = lead.content_hash or content_fingerprint(lead)
        lead.content_hash = digest
        records[url] = {
            "hash": digest,
            "published": lead.published_date or "",
            "lead_id": lead.id,
            "domain": domain_of(lead.url),
        }
    sources = state.setdefault("sources", {})
    sources[source] = {
        "query": query,
        "fetched_at": utcnow_iso(),
        "records": records,
    }


def select_records(
    leads: list[Lead],
    *,
    previous_records: dict[str, dict[str, Any]],
    store_index: dict[str, dict[str, Any]],
) -> tuple[list[Lead], list[Lead], list[Lead]]:
    """Split a fetch into disjoint new, changed, and unchanged vacancies.

    The caller decides whether unchanged rows are scored again. Hashes are
    always assigned so the next run can tell a real edit from a repeat.
    """
    fresh: list[Lead] = []
    changed: list[Lead] = []
    unchanged: list[Lead] = []
    for lead in leads:
        digest = content_fingerprint(lead)
        lead.content_hash = digest
        url = normalize_url(lead.url)
        prev = previous_records.get(url) or {}
        prev_hash = str(prev.get("hash") or "")
        stored = store_index.get(url) or store_index.get(lead.id) or {}
        stored_hash = str(stored.get("content_hash") or "")
        same = (prev_hash and prev_hash == digest) or (stored_hash and stored_hash == digest)
        legacy_known = bool(stored) and not stored_hash and not prev_hash
        if same or legacy_known:
            unchanged.append(lead)
            continue
        if prev_hash or stored_hash:
            changed.append(lead)
            continue
        fresh.append(lead)
    return fresh, changed, unchanged
