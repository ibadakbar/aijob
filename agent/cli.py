#!/usr/bin/env python3
"""CLI for the Excel-backed opportunity agent."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.discovery.agencies.collect import run_agency_discovery
from agent.discovery.clients.hunt import run_client_discovery
from agent.discovery.clients.ingest import ingest_leads_store
from agent.discovery.companies.careers import run_ats_deep_crawl
from agent.discovery.founders.collect import run_founder_discovery
from agent.discovery.recruiters.collect import run_recruiter_discovery
from agent.scheduler.runner import (
    AgentRunner,
    live_status,
    load_control,
    load_state,
    request_stop_agent,
    set_control,
    start_agent_process,
)
from agent.storage.excel_store import ExcelStore


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Excel-only opportunity discovery agent")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="Create workbook + folders")
    sub.add_parser("status", help="Show agent + workbook stats")
    p_run = sub.add_parser("run-once", help="Run discovery once then exit")
    p_run.add_argument(
        "--engine",
        default="all",
        choices=[
            "all",
            "jobs",
            "ats",
            "leads",
            "clients",
            "founders",
            "recruiters",
            "agencies",
            "enrichment",
            "ingest_only",
        ],
    )
    sub.add_parser("start", help="Start background loop (blocking)")
    sub.add_parser("stop", help="Signal running agent to stop")
    sub.add_parser("pause", help="Pause background agent")
    sub.add_parser("resume", help="Resume background agent")
    sub.add_parser("run-now", help="Ask running agent to run all engines now")
    sub.add_parser("backup", help="Backup workbook")
    sub.add_parser("ingest-leads", help="Sync leads_store.json → Excel (quality-gated)")
    sub.add_parser("hunt-clients", help="Run worldwide client hunter once")
    sub.add_parser("hunt-founders", help="Run founder collector once")
    sub.add_parser("hunt-recruiters", help="Run recruiter collector once")
    sub.add_parser("hunt-agencies", help="Run agency collector once")
    sub.add_parser("hunt-ats", help="Run ATS/careers deep crawl once")
    sub.add_parser(
        "expire-stale",
        help="Mark listings older than 3 months as expired (LinkedIn age + posted date)",
    )
    sub.add_parser(
        "repair-found-at",
        help="Fix bulk-identical Discovered/Found-at times from leads checked/published dates",
    )
    p_enrich = sub.add_parser(
        "enrich-contacts",
        help="Public contact-chain: site → /contact /about /team → published email/phone/WhatsApp",
    )
    p_enrich.add_argument("--limit", type=int, default=20, help="Max rows to enrich this run")
    p_apply = sub.add_parser(
        "apply-assist",
        help="Build review-only apply packet (open URL + draft); never auto-submits",
    )
    p_apply.add_argument("--id", required=True, help="Opportunity ID from Excel")
    p_apply.add_argument("--open-url", action="store_true", help="Open apply URL in browser")
    p_apply.add_argument("--mailto", action="store_true", help="Open mail client draft")

    args = parser.parse_args(argv)
    store = ExcelStore()

    if args.cmd == "init":
        path = store.ensure_workbook()
        print(json.dumps({"workbook": str(path), "ok": True}))
        return 0
    if args.cmd == "status":
        store.ensure_workbook()
        print(
            json.dumps(
                {
                    "workbook": str(store.path),
                    "exists": store.path.is_file(),
                    "stats": store.get_statistics(),
                    "agent": live_status(),
                    "agent_state": load_state(),
                    "control": load_control(),
                },
                indent=2,
                default=str,
            )
        )
        return 0
    if args.cmd == "run-once":
        result = AgentRunner().run_once(args.engine)
        print(json.dumps(result, indent=2, default=str))
        return 0 if result else 1
    if args.cmd == "start":
        # Foreground loop (used by start_agent.bat / detached spawn)
        AgentRunner().loop()
        return 0
    if args.cmd == "stop":
        print(json.dumps(request_stop_agent(force=True), indent=2))
        return 0
    if args.cmd == "pause":
        set_control("pause")
        print('{"ok": true, "command": "pause"}')
        return 0
    if args.cmd == "resume":
        set_control("run")
        print('{"ok": true, "command": "run"}')
        return 0
    if args.cmd == "run-now":
        if not live_status().get("alive"):
            start_agent_process()
        set_control("run_now")
        print('{"ok": true, "command": "run_now"}')
        return 0
    if args.cmd == "backup":
        path = store.backup("manual")
        print(json.dumps({"backup": str(path)}))
        return 0
    if args.cmd == "ingest-leads":
        print(json.dumps(ingest_leads_store(store), indent=2))
        return 0
    if args.cmd == "hunt-clients":
        print(json.dumps(run_client_discovery(store), indent=2, default=str))
        return 0
    if args.cmd == "hunt-founders":
        print(json.dumps(run_founder_discovery(store), indent=2, default=str))
        return 0
    if args.cmd == "hunt-recruiters":
        print(json.dumps(run_recruiter_discovery(store), indent=2, default=str))
        return 0
    if args.cmd == "hunt-agencies":
        print(json.dumps(run_agency_discovery(store), indent=2, default=str))
        return 0
    if args.cmd == "hunt-ats":
        print(json.dumps(run_ats_deep_crawl(store), indent=2, default=str))
        return 0
    if args.cmd == "expire-stale":
        print(json.dumps(store.expire_stale_opportunities(), indent=2))
        return 0
    if args.cmd == "repair-found-at":
        print(json.dumps(store.repair_found_at_times(), indent=2))
        return 0
    if args.cmd == "enrich-contacts":
        from agent.enrichment.contact_chain import run_contact_chain_enrichment

        print(
            json.dumps(
                run_contact_chain_enrichment(store, limit=int(args.limit)),
                indent=2,
                default=str,
            )
        )
        return 0
    if args.cmd == "apply-assist":
        from agent.apply_assist import prepare_application

        rows = {r.id: r for r in store.load_all_opportunities()}
        rec = rows.get(args.id)
        if not rec:
            print(json.dumps({"ok": False, "error": f"id not found: {args.id}"}))
            return 1
        packet = prepare_application(
            rec,
            open_url=bool(args.open_url),
            open_mail=bool(args.mailto),
            save_draft=True,
        )
        store.update_opportunity_fields(
            rec.id,
            status="drafted"
            if (rec.status or "").lower() in ("", "new", "qualified", "needs_review")
            else None,
            notes_append=f"[apply-assist {packet.draft_path}]",
            next_action="review_and_submit_manually",
        )
        print(json.dumps(packet.to_dict(), indent=2))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
