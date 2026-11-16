"""Lead store: durable JSON map keyed by stable lead id."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from .model import Lead, LeadStatus, OutreachDraft

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STORE = ROOT / "leads" / "store" / "leads_store.json"

VALID_STATUSES = {
    "new",
    "qualified",
    "shortlisted",
    "contacted",
    "replied",
    "meeting",
    "proposal",
    "won",
    "lost",
    "disqualified",
    "expired",
    "needs_review",
}


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    _atomic_write(path, payload)


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            try:
                os.remove(tmp_name)
            except OSError:
                pass


def load_store(path: Path | None = None) -> dict[str, Any]:
    p = path or DEFAULT_STORE
    if not p.is_file():
        return {"version": 1, "leads": {}, "updated": None}
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("leads store must be a JSON object")
    data.setdefault("version", 1)
    data.setdefault("leads", {})
    return data


def save_store(data: dict[str, Any], path: Path | None = None) -> Path:
    p = path or DEFAULT_STORE
    data["updated"] = date.today().isoformat()
    _atomic_write(p, data)
    return p


def upsert_leads(leads: list[Lead], path: Path | None = None) -> dict[str, Any]:
    """Insert new leads; refresh evidence on duplicates without wiping status/outreach."""
    store = load_store(path)
    bucket: dict[str, Any] = store.setdefault("leads", {})
    added = 0
    updated = 0
    for lead in leads:
        existing = bucket.get(lead.id)
        payload = lead.to_dict()
        if existing is None:
            bucket[lead.id] = payload
            added += 1
            continue
        # Preserve lifecycle fields
        for key in (
            "status",
            "outreach",
            "last_contact_date",
            "next_followup_date",
            "notes",
            "outcome",
        ):
            if existing.get(key) not in (None, "", [], {}):
                payload[key] = existing[key]
        # If new evidence URL/date differs, keep status but note refresh
        if payload.get("url") == existing.get("url") and payload.get("intent") == existing.get("intent"):
            # Same lead resurfaced — bump checked_date only unless expired flipped
            pass
        bucket[lead.id] = payload
        updated += 1
    store["leads"] = bucket
    save_store(store, path)
    return {"added": added, "updated": updated, "total": len(bucket)}


def get_lead(lead_id: str, path: Path | None = None) -> Optional[dict[str, Any]]:
    return load_store(path).get("leads", {}).get(lead_id)


def set_status(
    lead_id: str,
    status: LeadStatus,
    *,
    notes: str = "",
    outcome: str = "",
    path: Path | None = None,
) -> dict[str, Any]:
    if status not in VALID_STATUSES:
        raise ValueError(f"invalid status: {status}")
    store = load_store(path)
    lead = store.get("leads", {}).get(lead_id)
    if lead is None:
        raise KeyError(lead_id)
    lead["status"] = status
    if notes:
        prev = lead.get("notes") or ""
        stamp = date.today().isoformat()
        lead["notes"] = (prev + f"\n[{stamp}] {notes}").strip()
    if outcome:
        lead["outcome"] = outcome
    if status == "contacted":
        lead["last_contact_date"] = date.today().isoformat()
        lead["next_followup_date"] = (date.today() + timedelta(days=7)).isoformat()
    store["leads"][lead_id] = lead
    save_store(store, path)
    return lead


def save_outreach(lead_id: str, outreach: OutreachDraft, path: Path | None = None) -> dict[str, Any]:
    store = load_store(path)
    lead = store.get("leads", {}).get(lead_id)
    if lead is None:
        raise KeyError(lead_id)
    payload = outreach.to_dict()
    payload["send_approved"] = False  # hard rule
    lead["outreach"] = payload
    store["leads"][lead_id] = lead
    save_store(store, path)
    return lead


def list_leads(
    *,
    status: Optional[str] = None,
    shortlist_only: bool = False,
    review_queue: bool = False,
    path: Path | None = None,
) -> list[dict[str, Any]]:
    store = load_store(path)
    rows = list(store.get("leads", {}).values())
    if review_queue:
        rows = [r for r in rows if r.get("status") == "needs_review"]
    elif shortlist_only:
        rows = [r for r in rows if r.get("status") in ("qualified", "shortlisted", "new")]
    if status and not review_queue:
        rows = [r for r in rows if r.get("status") == status]
    rows.sort(
        key=lambda r: (
            0 if (r.get("scores") or {}).get("overall") is None else 1,
            -float((r.get("scores") or {}).get("overall") or 0),
            r.get("company") or "",
        ),
        reverse=False,
    )
    # Fix sort: highest overall first
    rows.sort(key=lambda r: float((r.get("scores") or {}).get("overall") or 0), reverse=True)
    return rows


def due_followups(*, today: Optional[date] = None, path: Path | None = None) -> list[dict[str, Any]]:
    today = today or date.today()
    out = []
    for row in list_leads(path=path):
        if row.get("status") not in ("contacted", "replied", "meeting", "proposal"):
            continue
        nxt = row.get("next_followup_date")
        if not nxt:
            continue
        try:
            due = datetime.strptime(nxt[:10], "%Y-%m-%d").date()
        except ValueError:
            continue
        if due <= today:
            out.append(row)
    return out


def known_keys(path: Path | None = None) -> set[str]:
    store = load_store(path)
    keys = set(store.get("leads", {}).keys())
    for row in store.get("leads", {}).values():
        url = (row.get("url") or "").strip().lower()
        if url:
            keys.add(url)
        company = (row.get("company") or "").lower()
        title = (row.get("title") or "").lower()
        if company and title:
            keys.add(f"{company}::{title}")
    return keys
