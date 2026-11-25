"""Agency partnership hunter — leads with partnership.is_agency from store."""

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


def run_agency_discovery(store: ExcelStore | None = None, *, limit: int = 25) -> dict[str, Any]:
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
            part = lead.get("partnership")
            if not isinstance(part, dict) or not part.get("is_agency"):
                continue
            if str(part.get("partnership_fit") or "none") == "none":
                continue
            company = str(lead.get("company") or "")
            title = str(lead.get("title") or "Agency partnership")
            url = str(lead.get("url") or "")
            pitch = str(part.get("pitch_angle") or "")
            rec = OpportunityRecord(
                id=make_opportunity_id("agency", company, title, url),
                opportunity_type="agency",
                company=company,
                role_or_title=title[:200],
                description=(pitch or str(lead.get("intent_explanation") or ""))[:2000],
                location=str(lead.get("location") or ""),
                remote_type=str(lead.get("workplace") or "unknown"),
                salary_or_budget=str(lead.get("budget_or_salary") or ""),
                posted_date=str(lead.get("published_date") or "")[:10],
                discovered_date=now_discovered(),
                last_verified=date.today().isoformat(),
                source_name=str(lead.get("source") or "leads_store_agencies"),
                source_url=url,
                intent_classification=str(lead.get("intent") or "STRONG_SIGNAL"),
                evidence=f"agency_fit={part.get('partnership_fit')}; {'; '.join(part.get('reasons') or [])}"[
                    :800
                ],
                status="new",
                next_action="partnership_pitch",
            )
            apply_contact_ladder_to_record(
                rec, contacts=lead.get("contacts") if isinstance(lead.get("contacts"), list) else []
            )
            records.append(score_client(rec))
            if len(records) >= limit * 2:
                break

        existing = store.load_all_opportunities()
        gated = apply_quality_gates(records, existing_rows=existing, enforce_path=False)
        # Agencies: still drop fake-remote via soft path inside path_gate when enforce True —
        # for partnership we allow enforce_path=False but strip inferred emails already done.
        result = store.upsert_opportunities(
            gated.kept[:limit], history_summary="agency partnership collector"
        )
        store.record_source_run(
            "agencies",
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
        store.record_source_run("agencies", success=False, error=str(exc))
        return {"ok": False, "error": str(exc)}
