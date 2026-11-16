"""Append-only evidence log so later AI output can be checked against the source."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from .incremental import utcnow_iso
from .model import Lead


def append_evidence(
    path: Path,
    leads: list[Lead],
    *,
    logged: dict[str, Any],
) -> int:
    """Append one JSON line per new evidence observation. Returns rows written."""
    path.parent.mkdir(parents=True, exist_ok=True)
    wrote = 0
    with path.open("a", encoding="utf-8") as fh:
        for lead in leads:
            digest = lead.content_hash or lead.id
            marker = f"{lead.id}:{digest}"
            if logged.get(marker):
                continue
            excerpts = lead.evidence or []
            if not excerpts:
                payload = {
                    "lead_id": lead.id,
                    "source": lead.source,
                    "source_url": lead.url,
                    "recorded_at": utcnow_iso(),
                    "checked_date": lead.checked_date,
                    "published_date": lead.published_date,
                    "excerpt": "",
                    "summary": "",
                    "content_hash": lead.content_hash,
                    "confidence": lead.confidence,
                    "intent": lead.intent,
                }
                fh.write(json.dumps(payload, ensure_ascii=False) + "\n")
                wrote += 1
            for ev in excerpts:
                payload = {
                    "lead_id": lead.id,
                    "source": lead.source,
                    "source_url": ev.source_url or lead.url,
                    "recorded_at": utcnow_iso(),
                    "checked_date": ev.checked_date or lead.checked_date,
                    "published_date": ev.published_date or lead.published_date,
                    "excerpt": ev.excerpt,
                    "summary": ev.summary,
                    "content_hash": lead.content_hash,
                    "confidence": lead.confidence,
                    "intent": lead.intent,
                }
                fh.write(json.dumps(payload, ensure_ascii=False) + "\n")
                wrote += 1
            logged[marker] = utcnow_iso()
    return wrote


def read_evidence(path: Path, lead_id: Optional[str] = None) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(row, dict):
            continue
        if lead_id and row.get("lead_id") != lead_id:
            continue
        rows.append(row)
    return rows
