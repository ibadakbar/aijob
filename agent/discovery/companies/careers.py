"""Company careers / ATS deep crawl via harvest_boards + board_scrape bridge."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

from agent.discovery.jobs.ingest import job_dict_to_record
from agent.models.opportunity import now_discovered
from agent.quality.pipeline import apply_quality_gates
from agent.storage.excel_store import ExcelStore

ROOT = Path(__file__).resolve().parents[3]


def run_ats_deep_crawl(
    store: ExcelStore | None = None,
    *,
    limit: int = 30,
    since: str = "7d",
    harvest: bool = False,
) -> dict[str, Any]:
    """Run board_scrape (visa_discover --volume Path A/B) and gate into Excel.

    Optional weekly harvest_boards refresh of ATS slugs (greenhouse/ashby/lever).
    """
    store = store or ExcelStore()
    store.ensure_workbook()
    out: dict[str, Any] = {"ok": True}

    if harvest:
        try:
            proc = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tools" / "harvest_boards.py"),
                    "--ats",
                    "greenhouse,ashby,lever",
                    "--limit",
                    "40",
                    "--min-jobs",
                    "1",
                    "--write",
                ],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                timeout=600,
            )
            out["harvest_returncode"] = proc.returncode
        except Exception as exc:  # noqa: BLE001
            out["harvest_error"] = str(exc)

    hits_path = ROOT / "logs" / "agent_ats_hits.json"
    hits_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        proc = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools" / "board_scrape.py"),
                "--limit",
                str(limit),
                "--since",
                since,
                "--format",
                "json",
                "--scrape-hits",
                str(hits_path),
            ],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=900,
        )
        jobs: list[dict[str, Any]] = []
        if hits_path.is_file():
            try:
                data = json.loads(hits_path.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    jobs = data
                elif isinstance(data, dict):
                    jobs = data.get("results") or data.get("jobs") or []
            except json.JSONDecodeError:
                pass
        if not jobs and proc.stdout.strip().startswith(("[", "{")):
            try:
                data = json.loads(proc.stdout)
                jobs = data if isinstance(data, list) else (data.get("results") or [])
            except json.JSONDecodeError:
                pass

        records = [
            job_dict_to_record(j)
            for j in jobs
            if isinstance(j, dict) and j.get("url") and j.get("company") and j.get("title")
        ]
        # Mark source
        for r in records:
            r.source_name = r.source_name or "ats_deep"
            if not r.discovered_date:
                r.discovered_date = now_discovered()

        existing = store.load_all_opportunities()
        gated = apply_quality_gates(records, existing_rows=existing, kill_days=10, enforce_path=True)
        result = store.upsert_opportunities(
            gated.kept, history_summary="ATS/careers deep crawl board_scrape"
        )
        store.record_source_run(
            "ats_deep",
            success=proc.returncode == 0 or bool(gated.kept),
            new_records=result.get("added", 0),
            duplicates=result.get("updated", 0),
            error="" if proc.returncode == 0 else (proc.stderr or "")[-500:],
        )
        out.update(
            {
                "fetched": len(jobs),
                "kept": len(gated.kept),
                "dropped": len(gated.dropped),
                "gate": gated.stats,
                **result,
            }
        )
        return out
    except Exception as exc:  # noqa: BLE001
        store.record_source_run("ats_deep", success=False, error=str(exc))
        return {"ok": False, "error": str(exc), **out}
