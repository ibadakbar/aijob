"""Multi-strategy intelligent job discovery → Excel.

Approaches (rotated each cycle):
  1. freehire — fast API + rotating keyword packs
  2. visa_discover (ATS+Arbeitnow) — medium, Path A/B classified
  3. visa_discover --volume — JobSpy/RemoteOK/WWR (heavier, every Nth cycle)
  4. board_scrape — owned ATS deep crawl (optional light pass)

Never blocks the agent loop on a single 15-minute legacy scrape.
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

from agent.discovery.jobs.freehire_source import run_freehire_pack
from agent.discovery.jobs.query_packs import pick_packs_for_dry_streak
from agent.models.opportunity import (
    OpportunityRecord,
    make_opportunity_id,
    now_discovered,
)
from agent.quality.pipeline import apply_quality_gates
from agent.scoring.scores import score_job
from agent.storage.excel_store import ExcelStore

ROOT = Path(__file__).resolve().parents[3]
STATE_PATH = ROOT / "logs" / "agent_search_state.json"
log = logging.getLogger("opportunity_agent")


def _load_search_state() -> dict[str, Any]:
    if STATE_PATH.is_file():
        try:
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {
        "pack_cursor": 0,
        "cycle": 0,
        "pack_stats": {},
        "last_strategies": [],
    }


def _save_search_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
    tmp.replace(STATE_PATH)


def _run_cmd(
    cmd: list[str],
    *,
    out_path: Path,
    timeout: int,
) -> list[dict[str, Any]]:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"timeout after {timeout}s: {' '.join(cmd[:6])}…") from exc

    if out_path.is_file():
        try:
            data = json.loads(out_path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                return data.get("results") or data.get("jobs") or data.get("scrape_hits") or []
        except json.JSONDecodeError:
            pass
    raw = (proc.stdout or "").strip()
    if raw.startswith("{") or raw.startswith("["):
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                return data.get("results") or data.get("scrape_hits") or []
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or "")[-1500:] or f"exit {proc.returncode}")
    return []


def _visa_discover(
    *,
    limit: int,
    since: str,
    volume: bool,
    timeout: int,
    tag: str,
    sources: str | None = None,
) -> list[dict[str, Any]]:
    out_path = ROOT / "logs" / f"agent_visa_{tag}.json"
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
        "--max-jobs-per-source",
        "60" if volume else "80",
        "--arbeitnow-pages",
        "2" if volume else "3",
    ]
    if sources:
        cmd.extend(["--sources", sources])
    if volume:
        cmd.append("--volume")
    return _run_cmd(cmd, out_path=out_path, timeout=timeout)


def _board_scrape(*, limit: int, since: str, timeout: int) -> list[dict[str, Any]]:
    out_path = ROOT / "logs" / "agent_board_light.json"
    cmd = [
        sys.executable,
        str(ROOT / "tools" / "board_scrape.py"),
        "--limit",
        str(limit),
        "--since",
        since,
        "--format",
        "json",
        "--scrape-hits",
        str(out_path),
    ]
    return _run_cmd(cmd, out_path=out_path, timeout=timeout)


def _enrich_path_hints(job: dict[str, Any]) -> dict[str, Any]:
    """Infer Path A sponsorship hints from description before quality gates."""
    try:
        from job_scraper.engine.path_filter import remote_international, fake_remote
    except ImportError:
        return job
    blob = " ".join(
        str(job.get(k) or "")
        for k in ("title", "description", "location", "workplace")
    )
    if fake_remote(blob):
        return job
    if remote_international(blob):
        sp = job.get("sponsorship") if isinstance(job.get("sponsorship"), dict) else {}
        sp = dict(sp or {})
        if not sp.get("classification") or sp.get("classification") == "unknown":
            sp["classification"] = "possible"
            sp.setdefault("evidence", []).append(
                {"excerpt": "remote-international language in listing", "field": "description"}
            )
        job["sponsorship"] = sp
        job["path"] = job.get("path") or "A"
        job["workplace"] = job.get("workplace") or "remote"
    # Pakistan-local keep path
    country = str(job.get("country") or "").casefold()
    loc = str(job.get("location") or "").casefold()
    if country in ("pakistan", "pk") or "karachi" in loc or "pakistan" in loc:
        job["path"] = job.get("path") or "PK"
        job["country"] = job.get("country") or "Pakistan"
    return job


def job_dict_to_record(job: dict[str, Any]) -> OpportunityRecord:
    job = _enrich_path_hints(job)
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
    approach = str(job.get("approach") or job.get("query_pack") or "")
    if approach and not evidence:
        evidence = f"query_pack={approach}"
    skills_val = job.get("skills")
    if isinstance(skills_val, list):
        skills_s = ", ".join(str(s) for s in skills_val)
    else:
        skills_s = str(job.get("skills_str") or skills_val or "")
    rec = OpportunityRecord(
        id=make_opportunity_id("job", company, title, url),
        opportunity_type="job",
        company=company,
        role_or_title=title,
        description=str(job.get("description") or "")[:2000],
        required_skills=skills_s,
        country=str(job.get("country") or ""),
        location=str(job.get("location") or ""),
        remote_type=str(job.get("workplace") or "unknown"),
        international_eligibility=path,
        visa_sponsorship=visa,
        relocation_support=reloc_s,
        salary_or_budget=str(job.get("salary") or ""),
        posted_date=str(job.get("published_date") or "")[:10],
        # Found-at = this agent run (unique per record). Posted stays listing date.
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


def _dedupe_jobs(jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for j in jobs:
        url = str(j.get("url") or "").rstrip("/").casefold()
        key = url or f"{j.get('company','')}|{j.get('title','')}".casefold()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(j)
    return out


def _run_freehire_packs(
    store: ExcelStore,
    packs: list,
    *,
    timeout: int,
    strategies_run: list[str],
    strategy_results: dict[str, Any],
    all_jobs: list[dict[str, Any]],
) -> None:
    for pack in packs:
        strategies_run.append(f"freehire:{pack.id}")
        try:
            fr = run_freehire_pack(pack, timeout=timeout, with_description=True)
            strategy_results[pack.id] = {
                "ok": fr.get("ok"),
                "hits": fr.get("hits", 0),
                "total": fr.get("total_available", 0),
                "error": fr.get("error"),
                "approach": pack.approach,
            }
            if fr.get("ok"):
                all_jobs.extend(fr.get("jobs") or [])
                store.record_search_query(
                    query_id=pack.id,
                    engine="freehire",
                    query_text=pack.freehire_q,
                    hits=int(fr.get("hits") or 0),
                    new_hits=0,
                    notes=f"{pack.label} | {pack.approach}",
                )
                log.info(
                    "freehire pack %s → %s hits (pool %s)",
                    pack.id,
                    fr.get("hits"),
                    fr.get("total_available"),
                )
            else:
                log.warning("freehire pack %s failed: %s", pack.id, fr.get("error"))
                store.record_source_run(
                    f"freehire:{pack.id}", success=False, error=str(fr.get("error") or "")
                )
        except Exception as exc:  # noqa: BLE001
            log.exception("freehire pack %s crashed: %s", pack.id, exc)
            strategy_results[pack.id] = {"ok": False, "error": str(exc)}


def _gate_and_upsert(
    store: ExcelStore,
    all_jobs: list[dict[str, Any]],
    *,
    history_summary: str,
) -> tuple[list[dict[str, Any]], Any, dict[str, Any]]:
    jobs = _dedupe_jobs(all_jobs)
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
    result = store.upsert_opportunities(gated.kept, history_summary=history_summary)
    return jobs, gated, result


def run_job_discovery(
    store: ExcelStore | None = None,
    *,
    limit: int = 25,
    since: str = "2d",
    volume: bool = True,
    packs_per_cycle: int = 3,
    freehire_timeout: int = 90,
    visa_fast_timeout: int = 240,
    visa_volume_timeout: int = 420,
    board_timeout: int = 300,
    force_volume: bool | None = None,
) -> dict[str, Any]:
    """Intelligent multi-approach discovery with auto-improve when finds dry up."""
    store = store or ExcelStore()
    store.ensure_workbook()
    state = _load_search_state()
    cycle = int(state.get("cycle") or 0) + 1
    cursor = int(state.get("pack_cursor") or 0)
    dry_streak = int(state.get("dry_streak") or 0)

    packs, new_cursor, pack_mode = pick_packs_for_dry_streak(
        cursor,
        dry_streak=dry_streak,
        pack_stats=state.get("pack_stats") or {},
        base_n=packs_per_cycle,
    )

    # Widen freshness + force volume when dry
    effective_since = since
    if dry_streak >= 1:
        effective_since = "7d" if dry_streak == 1 else "14d"
    do_volume = (
        force_volume
        if force_volume is not None
        else (volume and (cycle % 3 == 0 or dry_streak >= 1))
    )

    strategies_run: list[str] = []
    strategy_results: dict[str, Any] = {}
    all_jobs: list[dict[str, Any]] = []
    improvements: list[str] = []

    if dry_streak > 0:
        improvements.append(
            f"dry_streak={dry_streak} → mode={pack_mode} packs={len(packs)} since={effective_since}"
        )
        log.info(
            "Auto-improve: dry_streak=%s mode=%s packs=%s since=%s volume=%s",
            dry_streak,
            pack_mode,
            [p.id for p in packs],
            effective_since,
            do_volume,
        )

    # --- Strategy 1: freehire packs ---
    _run_freehire_packs(
        store,
        packs,
        timeout=freehire_timeout,
        strategies_run=strategies_run,
        strategy_results=strategy_results,
        all_jobs=all_jobs,
    )

    # --- Strategy 2: visa_discover fast ---
    strategies_run.append("visa_fast")
    try:
        fast_jobs = _visa_discover(
            limit=limit + (10 if dry_streak else 0),
            since=effective_since,
            volume=False,
            timeout=visa_fast_timeout,
            tag="fast",
            sources="arbeitnow,landingjobs,remoteok",
        )
        for j in fast_jobs:
            j.setdefault("source", j.get("source") or "visa_fast")
            j["approach"] = "visa_ats"
        all_jobs.extend(fast_jobs)
        strategy_results["visa_fast"] = {"ok": True, "hits": len(fast_jobs)}
        store.record_search_query(
            query_id="visa_fast",
            engine="visa_discover",
            query_text=f"fast path-ab since={effective_since}",
            hits=len(fast_jobs),
            new_hits=0,
            notes="fast Path A/B",
        )
        log.info("visa_fast → %s jobs", len(fast_jobs))
    except Exception as exc:  # noqa: BLE001
        log.warning("visa_fast failed: %s", exc)
        strategy_results["visa_fast"] = {"ok": False, "error": str(exc)}
        store.record_source_run("visa_fast", success=False, error=str(exc))

    # --- Strategy 3: volume ---
    if do_volume:
        strategies_run.append("visa_volume")
        try:
            # When dry, prefer lighter boards (avoid JobSpy 420s hang)
            vol_sources = None
            vol_timeout = visa_volume_timeout
            use_full_volume = True
            if dry_streak >= 1:
                vol_sources = "arbeitnow,remoteok,weworkremotely,landingjobs"
                vol_timeout = min(visa_volume_timeout, 300)
                use_full_volume = False
            vol_jobs = _visa_discover(
                limit=max(limit, 30) + (dry_streak * 5),
                since=effective_since,
                volume=use_full_volume,
                timeout=vol_timeout,
                tag="volume",
                sources=vol_sources,
            )
            for j in vol_jobs:
                j.setdefault("source", j.get("source") or "visa_volume")
                j["approach"] = "visa_volume"
            all_jobs.extend(vol_jobs)
            strategy_results["visa_volume"] = {"ok": True, "hits": len(vol_jobs)}
            log.info("visa_volume → %s jobs", len(vol_jobs))
        except Exception as exc:  # noqa: BLE001
            log.warning("visa_volume failed: %s", exc)
            strategy_results["visa_volume"] = {"ok": False, "error": str(exc)}
            store.record_source_run("visa_volume", success=False, error=str(exc))

    # --- Strategy 4: board scrape if thin raw pool ---
    if len(_dedupe_jobs(all_jobs)) < 8 or dry_streak >= 2:
        strategies_run.append("board_light")
        try:
            board_jobs = _board_scrape(
                limit=min(30, limit + 10),
                since="14d" if dry_streak >= 2 else "7d",
                timeout=board_timeout,
            )
            for j in board_jobs:
                j.setdefault("source", j.get("source") or "board_scrape")
                j["approach"] = "board_light"
            all_jobs.extend(board_jobs)
            strategy_results["board_light"] = {"ok": True, "hits": len(board_jobs)}
            log.info("board_light → %s jobs", len(board_jobs))
        except Exception as exc:  # noqa: BLE001
            log.warning("board_light failed: %s", exc)
            strategy_results["board_light"] = {"ok": False, "error": str(exc)}

    jobs, gated, result = _gate_and_upsert(
        store,
        all_jobs,
        history_summary=(
            f"intelligent cycle={cycle} dry={dry_streak} mode={pack_mode} "
            f"packs={[p.id for p in packs]}"
        ),
    )
    added = int(result.get("added") or 0)

    # --- Self-heal: if still 0 NEW, escalate once more in this cycle ---
    if added == 0:
        improvements.append("same_cycle_escalation")
        log.info("Auto-improve: 0 new — same-cycle escalation")
        from agent.discovery.jobs.query_packs import pack_by_id

        extra_ids = [
            "emergency_visa_worldwide",
            "emergency_path_b_eu",
            "emergency_pk_local",
            "worldwide_remote",
            "visa_sponsor_react",
        ]
        extra_packs = [pack_by_id(i) for i in extra_ids]
        extra_packs = [p for p in extra_packs if p and p.id not in {x.id for x in packs}]
        if extra_packs:
            _run_freehire_packs(
                store,
                extra_packs[:3],
                timeout=freehire_timeout,
                strategies_run=strategies_run,
                strategy_results=strategy_results,
                all_jobs=all_jobs,
            )
        # Wider API sweep
        strategies_run.append("visa_fast_escalate")
        try:
            more = _visa_discover(
                limit=40,
                since="14d",
                volume=False,
                timeout=visa_fast_timeout,
                tag="fast_esc",
                sources="arbeitnow,landingjobs,remoteok,weworkremotely",
            )
            for j in more:
                j.setdefault("source", j.get("source") or "visa_fast_escalate")
                j["approach"] = "visa_escalate"
            all_jobs.extend(more)
            strategy_results["visa_fast_escalate"] = {"ok": True, "hits": len(more)}
            log.info("visa_fast_escalate → %s jobs", len(more))
        except Exception as exc:  # noqa: BLE001
            log.warning("visa_fast_escalate failed: %s", exc)
            strategy_results["visa_fast_escalate"] = {"ok": False, "error": str(exc)}

        jobs, gated, result = _gate_and_upsert(
            store,
            all_jobs,
            history_summary=f"intelligent cycle={cycle} ESCALATED dry={dry_streak}",
        )
        added = int(result.get("added") or 0)
        if added > 0:
            improvements.append(f"escalation_recovered_added={added}")
            log.info("Auto-improve recovered %s new listings", added)

    store.record_source_run(
        "intelligent_jobs",
        success=True,
        new_records=added,
        duplicates=int(result.get("updated") or 0),
    )

    # Pack stats + kept attribution
    pack_stats = state.setdefault("pack_stats", {})
    kept_by_pack: dict[str, int] = {}
    for rec in gated.kept:
        src = str(rec.source_name or "")
        if src.startswith("freehire:"):
            pid = src.split(":", 1)[1]
            kept_by_pack[pid] = kept_by_pack.get(pid, 0) + 1
    for pack in packs:
        st = pack_stats.setdefault(pack.id, {"runs": 0, "hits": 0, "kept": 0})
        st["runs"] = int(st.get("runs") or 0) + 1
        pack_hits = int((strategy_results.get(pack.id) or {}).get("hits") or 0)
        st["hits"] = int(st.get("hits") or 0) + pack_hits
        st["kept"] = int(st.get("kept") or 0) + int(kept_by_pack.get(pack.id) or 0)

    new_dry = 0 if added > 0 else dry_streak + 1
    state["pack_cursor"] = new_cursor
    state["cycle"] = cycle
    state["dry_streak"] = new_dry
    state["last_strategies"] = strategies_run
    state["last_improvements"] = improvements
    state["last_run"] = datetime.now().isoformat()
    state["last_fetched"] = len(jobs)
    state["last_kept"] = len(gated.kept)
    state["last_added"] = added
    state["pack_mode"] = pack_mode
    _save_search_state(state)

    return {
        "ok": True,
        "mode": "intelligent_multi_strategy",
        "cycle": cycle,
        "dry_streak": new_dry,
        "pack_mode": pack_mode,
        "auto_improve": improvements,
        "packs": [p.id for p in packs],
        "strategies": strategies_run,
        "strategy_results": strategy_results,
        "fetched": len(jobs),
        "kept": len(gated.kept),
        "dropped": len(gated.dropped),
        "gate": gated.stats,
        "volume_this_cycle": do_volume,
        "since": effective_since,
        **result,
    }
