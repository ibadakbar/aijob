"""Recruiter hunter — published recruiter/talent emails from leads_store."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from agent.models.opportunity import OpportunityRecord, make_opportunity_id, now_discovered
from agent.quality.contact_ladder import apply_contact_ladder_to_record
from agent.quality.pipeline import apply_quality_gates
from agent.scoring.scores import score_client
from agent.storage.excel_store import ExcelStore

ROOT = Path(__file__).resolve().parents[3]
LEADS_STORE = ROOT / "leads" / "store" / "leads_store.json"

_RECRUITER_HINTS = ("recruit", "talent", "people partner", "hiring manager", "hr ")


def _is_recruiter_contact(ch: dict[str, Any]) -> bool:
    title = str(ch.get("title") or "").lower()
    email = str(ch.get("value") or "").lower()
    if any(h in title for h in _RECRUITER_HINTS):
        return True
    local = email.split("@", 1)[0] if "@" in email else ""
    return local in ("recruiting", "talent", "careers", "jobs", "hiring", "hr")


def run_recruiter_discovery(store: ExcelStore | None = None, *, limit: int = 30) -> dict[str, Any]:
    store = store or ExcelStore()
    store.ensure_workbook()
    if not LEADS_STORE.is_file():
        return {"ok": True, "fetched": 0, "note": "no leads_store"}
    try:
        data = json.loads(LEADS_STORE.read_text(encoding="utf-8"))
        leads = list((data.get("leads") or {}).values())
        records: list[OpportunityRecord] = []
        for lead in leads:
            if not isinstance(lead, dict):
                continue
            contacts = lead.get("contacts") or []
            if not isinstance(contacts, list):
                continue
            recr = [c for c in contacts if isinstance(c, dict) and _is_recruiter_contact(c)]
            if not recr:
                continue
            company = str(lead.get("company") or "")
            title = str(lead.get("title") or "Recruiter contact")
            url = str(lead.get("url") or "")
            ch = recr[0]
            rec = OpportunityRecord(
                id=make_opportunity_id(
                    "recruiter", company, str(ch.get("name") or ch.get("value") or title), url
                ),
                opportunity_type="recruiter",
                company=company,
                role_or_title=f"{ch.get('name') or 'Recruiter'} — {title}"[:200],
                description=str(lead.get("intent_explanation") or "")[:2000],
                location=str(lead.get("location") or ""),
                remote_type=str(lead.get("workplace") or "unknown"),
                posted_date=str(lead.get("published_date") or "")[:10],
                discovered_date=now_discovered(),
                last_verified=date.today().isoformat(),
                source_name=str(lead.get("source") or "leads_store_recruiters"),
                source_url=url,
                contact_name=str(ch.get("name") or ""),
                contact_position=str(ch.get("title") or "Recruiter"),
                intent_classification=str(lead.get("intent") or "EXPLICIT_DEMAND"),
                evidence="published_recruiter_contact",
                status="new",
            )
            apply_contact_ladder_to_record(rec, contacts=contacts)
            records.append(score_client(rec))
            if len(records) >= limit * 2:
                break

        existing = store.load_all_opportunities()
        gated = apply_quality_gates(records, existing_rows=existing, enforce_path=True)
        result = store.upsert_opportunities(
            gated.kept[:limit], history_summary="recruiter collector"
        )
        store.record_source_run(
            "recruiters",
            success=True,
            new_records=result.get("added", 0),
            duplicates=result.get("updated", 0),
        )
        return {
            "ok": True,
            "fetched": len(records),
            "kept": len(gated.kept),
            "dropped": len(gated.dropped),
            "gate": gated.stats,
            **result,
        }
    except Exception as exc:  # noqa: BLE001
        store.record_source_run("recruiters", success=False, error=str(exc))
        return {"ok": False, "error": str(exc)}
