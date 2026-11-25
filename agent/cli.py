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
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
