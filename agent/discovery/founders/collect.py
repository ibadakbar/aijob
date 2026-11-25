"""Founder hunter — extract founder LinkedIn / hiring signals from leads_store + YC raw."""

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


def _founder_records_from_lead(lead: dict[str, Any]) -> list[OpportunityRecord]:
    raw = lead.get("raw") or {}
    founders = raw.get("founders") if isinstance(raw, dict) else None
    if not isinstance(founders, list) or not founders:
        # Prefer contact path labeled founder
        contacts = lead.get("contacts") or []
        founders = []
        for ch in contacts if isinstance(contacts, list) else []:
            if not isinstance(ch, dict):
                continue
            title = str(ch.get("title") or "").lower()
            if any(k in title for k in ("founder", "co-founder", "ceo", "cto")):
                founders.append(
                    {
                        "name": ch.get("name"),
                        "title": ch.get("title"),
                        "linkedin_url": ch.get("value")
                        if "linkedin" in str(ch.get("value") or "").lower()
                        else "",
                        "email": ch.get("value") if ch.get("channel_type") == "email" else "",
                    }
                )
        if not founders and (lead.get("source") or "").lower() not in ("ycombinator", "yc"):
            return []

    company = str(lead.get("company") or "")
    title = str(lead.get("title") or "Founder outreach")
    url = str(lead.get("url") or "")
    intent = str(lead.get("intent") or "")
    if raw.get("isHiring") and not intent:
        intent = "EXPLICIT_DEMAND"

    out: list[OpportunityRecord] = []
    contacts = lead.get("contacts") if isinstance(lead.get("contacts"), list) else []

    if founders:
        for f in founders:
            if not isinstance(f, dict):
                continue
            name = str(f.get("name") or "Founder")
            li = str(f.get("linkedin_url") or f.get("linkedin") or "")
            email = str(f.get("email") or "")
            role = f"{name} — {f.get('title') or 'Founder'}"
            rec = OpportunityRecord(
                id=make_opportunity_id("founder", company, role, li or url),
                opportunity_type="founder",
                company=company,
                role_or_title=role[:200],
                description=str(lead.get("intent_explanation") or title)[:2000],
                location=str(lead.get("location") or ""),
                remote_type=str(lead.get("workplace") or "unknown"),
                posted_date=str(lead.get("published_date") or "")[:10],
                discovered_date=now_discovered(),
                last_verified=date.today().isoformat(),
                source_name=str(lead.get("source") or "leads_store_founders"),
                source_url=url,
                contact_name=name,
                contact_position=str(f.get("title") or "Founder"),
                contact_email=email,
                linkedin_url=li,
                intent_classification=intent or "STRONG_SIGNAL",
                evidence=f"founder_signal; isHiring={bool(raw.get('isHiring'))}",
                status="new",
            )
            apply_contact_ladder_to_record(rec, contacts=contacts, founders=[f])
            out.append(score_client(rec))
    else:
        # YC hiring shell without founder enrich yet
        if raw.get("isHiring"):
            rec = OpportunityRecord(
                id=make_opportunity_id("founder", company, title, url),
                opportunity_type="founder",
                company=company,
                role_or_title=title[:200],
                description="YC/isHiring signal — enrich founder LinkedIn before outreach",
                source_name=str(lead.get("source") or "yc"),
                source_url=url,
                intent_classification="EXPLICIT_DEMAND",
                discovered_date=now_discovered(),
                last_verified=date.today().isoformat(),
                remote_type=str(lead.get("workplace") or "unknown"),
            )
            apply_contact_ladder_to_record(rec, contacts=contacts)
            out.append(score_client(rec))
    return out


def run_founder_discovery(store: ExcelStore | None = None, *, limit: int = 40) -> dict[str, Any]:
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
            records.extend(_founder_records_from_lead(lead))
            if len(records) >= limit * 3:
                break
        existing = store.load_all_opportunities()
        gated = apply_quality_gates(records[: limit * 2], existing_rows=existing, enforce_path=True)
        result = store.upsert_opportunities(
            gated.kept[:limit], history_summary="founder collector leads_store"
        )
        store.record_source_run(
            "founders",
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
        store.record_source_run("founders", success=False, error=str(exc))
        return {"ok": False, "error": str(exc)}
