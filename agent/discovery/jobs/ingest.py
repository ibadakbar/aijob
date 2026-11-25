"""Ingest jobs from existing visa_discover / board_scrape into Excel."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

from agent.models.opportunity import OpportunityRecord, make_opportunity_id, now_discovered
from agent.quality.pipeline import apply_quality_gates
from agent.scoring.scores import score_job
from agent.storage.excel_store import ExcelStore

ROOT = Path(__file__).resolve().parents[3]


def _run_visa_discover(
    *,
    limit: int = 30,
    since: str = "2d",
    volume: bool = True,
) -> list[dict[str, Any]]:
    out_path = ROOT / "logs" / "agent_visa_hits.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(ROOT / "tools" / "visa_discover.py"),
        "--path-ab",
        "--new-only",
        "--since",
        since,
        "--limit",
        str(limit),
        "--format",
        "json",
        "--scrape-hits",
        str(out_path),
    ]
    if volume:
        cmd.append("--volume")
    proc = subprocess.run(
        cmd,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=900,
    )
    # Prefer scrape-hits file; fall back to stdout JSON
    if out_path.is_file():
        try:
            data = json.loads(out_path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                return data.get("results") or data.get("jobs") or []
        except json.JSONDecodeError:
            pass
    if proc.stdout.strip().startswith("{") or proc.stdout.strip().startswith("["):
        try:
            data = json.loads(proc.stdout)
            if isinstance(data, dict):
                return data.get("results") or []
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-2000:] or f"visa_discover exit {proc.returncode}")
    return []


def job_dict_to_record(job: dict[str, Any]) -> OpportunityRecord:
    title = str(job.get("title") or "")
    company = str(job.get("company") or "")
    url = str(job.get("url") or "")
    sponsorship = job.get("sponsorship") or {}
    if isinstance(sponsorship, dict):
        sclass = str(sponsorship.get("classification") or "")
        reloc = sponsorship.get("relocation_support")
    else:
        sclass = ""
        reloc = None
    rank = job.get("rank") or {}
    overall = 0.0
    skill = 0.0
    if isinstance(rank, dict):
        overall = float(rank.get("overall") or job.get("rank_overall") or 0) * 100
        skill = float(rank.get("skill_score") or job.get("skill_score") or 0) * 100
    path = str(job.get("path") or "")
    visa = "yes" if sclass == "verified_in_listing" or path in ("A", "B") and sclass else "unknown"
    if sclass == "not_available":
        visa = "no"
    reloc_s = "unknown"
    if reloc is True:
        reloc_s = "yes"
    elif reloc is False:
        reloc_s = "no"
    evidence = ""
    if isinstance(sponsorship, dict):
        ev = sponsorship.get("evidence") or []
        if ev and isinstance(ev, list) and isinstance(ev[0], dict):
            evidence = str(ev[0].get("excerpt") or "")[:500]
    rec = OpportunityRecord(
        id=make_opportunity_id("job", company, title, url),
        opportunity_type="job",
        company=company,
        role_or_title=title,
        description=str(job.get("description") or "")[:2000],
        required_skills=", ".join(job.get("skills") or []) if isinstance(job.get("skills"), list) else str(job.get("skills") or ""),
        country=str(job.get("country") or ""),
        location=str(job.get("location") or ""),
        remote_type=str(job.get("workplace") or "unknown"),
        international_eligibility=path,
        visa_sponsorship=visa,
        relocation_support=reloc_s,
        salary_or_budget=str(job.get("salary") or ""),
        posted_date=str(job.get("published_date") or "")[:10],
        discovered_date=now_discovered(),
        last_verified=date.today().isoformat(),
        source_name=str(job.get("source") or job.get("portal") or "visa_discover"),
        source_url=url,
        evidence=evidence,
        opportunity_score=overall or 0,
        path=path,
        sponsorship_class=sclass,
        skill_score=skill,
    )
    return score_job(rec)


def run_job_discovery(
    store: ExcelStore | None = None,
    *,
    limit: int = 25,
    since: str = "2d",
    volume: bool = True,
) -> dict[str, Any]:
    store = store or ExcelStore()
    store.ensure_workbook()
    try:
        jobs = _run_visa_discover(limit=limit, since=since, volume=volume)
        records = [
            job_dict_to_record(j)
            for j in jobs
            if j.get("url") and j.get("company") and j.get("title")
        ]
        existing = store.load_all_opportunities()
        gated = apply_quality_gates(
            records,
            existing_rows=existing,
            kill_days=14,
            enforce_path=True,
        )
        result = store.upsert_opportunities(
            gated.kept, history_summary="job discovery visa_discover (gated)"
        )
        store.record_source_run(
            "visa_discover",
            success=True,
            new_records=result.get("added", 0),
            duplicates=result.get("updated", 0),
        )
        return {
            "ok": True,
            "fetched": len(jobs),
            "kept": len(gated.kept),
            "dropped": len(gated.dropped),
            "gate": gated.stats,
            **result,
        }
    except Exception as exc:  # noqa: BLE001 — isolate source failure
        store.record_source_run("visa_discover", success=False, error=str(exc))
        return {"ok": False, "error": str(exc)}
