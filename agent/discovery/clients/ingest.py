"""Ingest leads from existing leads_store.json / leads_cli into Excel."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

from agent.models.opportunity import (
    OpportunityRecord,
    make_opportunity_id,
    now_discovered,
)
from agent.quality.contact_ladder import apply_contact_ladder_to_record
from agent.quality.pipeline import apply_quality_gates
from agent.scoring.scores import score_client, score_job
from agent.storage.excel_store import ExcelStore

ROOT = Path(__file__).resolve().parents[3]
LEADS_STORE = ROOT / "leads" / "store" / "leads_store.json"


def _lead_to_record(lead: dict[str, Any]) -> OpportunityRecord:
    company = str(lead.get("company") or lead.get("company_name") or "")
    title = str(lead.get("title") or lead.get("role") or lead.get("opportunity_title") or "")
    url = str(lead.get("url") or lead.get("source_url") or "")
    lead_type = str(lead.get("lead_type") or lead.get("type") or "client").lower()
    otype = "job" if lead_type in ("full_time", "job") else (
        "contract" if lead_type in ("contract", "freelance") else "client"
    )
    contacts = lead.get("contacts") or lead.get("contact_channels") or []
    raw = lead.get("raw") if isinstance(lead.get("raw"), dict) else {}
    founders = raw.get("founders") if isinstance(raw.get("founders"), list) else []
    intent = str(lead.get("intent") or lead.get("intent_classification") or "")
    evidence = str(lead.get("evidence_summary") or lead.get("evidence") or "")[:800]
    workplace = str(lead.get("workplace") or "unknown")
    # Map Path hints from lead raw if present
    path = str((raw or {}).get("path") or lead.get("path") or "")
    visa = "unknown"
    reloc = "unknown"
    sclass = str((raw or {}).get("sponsorship_class") or "")
    if path.upper() in ("A", "B") or (raw or {}).get("isHiring"):
        if not intent:
            intent = "EXPLICIT_DEMAND"
    rec = OpportunityRecord(
        id=str(lead.get("id") or make_opportunity_id(otype, company, title, url)),
        opportunity_type=otype,
        company=company,
        role_or_title=title,
        description=str(lead.get("description") or lead.get("summary") or lead.get("intent_explanation") or "")[
            :2000
        ],
        required_skills=", ".join(lead.get("technologies") or [])
        if isinstance(lead.get("technologies"), list)
        else "",
        country=str(lead.get("country") or ""),
        location=str(lead.get("location") or lead.get("geography") or ""),
        remote_type=workplace,
        international_eligibility=path,
        visa_sponsorship=visa,
        relocation_support=reloc,
        salary_or_budget=str(lead.get("budget") or lead.get("budget_or_salary") or lead.get("salary") or ""),
        posted_date=str(
            lead.get("posted_date") or lead.get("published_date") or ""
        )[:10],
        # Found at = current local time when agent saves this listing (shown in table)
        discovered_date=now_discovered(),
        last_verified=date.today().isoformat(),
        source_name=str(lead.get("source") or "leads_store"),
        source_url=url,
        intent_classification=intent,
        evidence=evidence,
        status=str(lead.get("status") or "new"),
        path=path,
        sponsorship_class=sclass,
    )
    apply_contact_ladder_to_record(
        rec,
        contacts=contacts if isinstance(contacts, list) else [],
        founders=founders,
    )
    if otype == "job":
        return score_job(rec)
    return score_client(rec)


def ingest_leads_store(store: ExcelStore | None = None) -> dict[str, Any]:
    store = store or ExcelStore()
    store.ensure_workbook()
    if not LEADS_STORE.is_file():
        return {"ok": True, "fetched": 0, "added": 0, "updated": 0, "note": "no leads_store.json"}
    try:
        data = json.loads(LEADS_STORE.read_text(encoding="utf-8"))
        leads = list((data.get("leads") or {}).values())
        records = [_lead_to_record(L) for L in leads if isinstance(L, dict)]
        records = [r for r in records if r.company and r.role_or_title]
        existing = store.load_all_opportunities()
        gated = apply_quality_gates(
            records,
            existing_rows=existing,
            kill_days=14,
            enforce_path=True,
        )
        result = store.upsert_opportunities(
            gated.kept, history_summary="ingest leads_store.json (gated)"
        )
        store.record_source_run(
            "leads_store",
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
        store.record_source_run("leads_store", success=False, error=str(exc))
        return {"ok": False, "error": str(exc)}


def run_leads_discover(
    prompt: str = "Find React OR Next.js OR TypeScript full-stack SaaS roles remote-international or visa sponsorship",
    store: ExcelStore | None = None,
) -> dict[str, Any]:
    store = store or ExcelStore()
    try:
        proc = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools" / "leads_cli.py"),
                "discover",
                "--prompt",
                prompt,
                "--sources",
                "arbeitnow,greenhouse,ashby,lever",
                "--mode",
                "jobs",
                "--yes",
                "--format",
                "json",
            ],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=600,
        )
        # Always try store ingest after discover
        ingested = ingest_leads_store(store)
        if proc.returncode != 0 and not ingested.get("ok"):
            err = proc.stderr[-1500:] or proc.stdout[-1500:]
            store.record_source_run("leads_cli", success=False, error=err)
            return {"ok": False, "error": err, "ingest": ingested}
        store.record_source_run(
            "leads_cli",
            success=True,
            new_records=ingested.get("added", 0),
            duplicates=ingested.get("updated", 0),
        )
        return {"ok": True, "ingest": ingested, "returncode": proc.returncode}
    except Exception as exc:  # noqa: BLE001
        store.record_source_run("leads_cli", success=False, error=str(exc))
        return {"ok": False, "error": str(exc)}
