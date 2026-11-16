"""Orchestrate fetch → classify → dedupe → rank for visa-aware discovery."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any, Optional

from .dedupe import dedupe_jobs
from .model import NormalizedJob
from .normalize import TARGET_COUNTRIES, country_in_targets
from .rank import RankScores, rank_jobs
from .sources import LIVE_SOURCES, STUB_SOURCES

ROOT = Path(__file__).resolve().parent.parent
BOARDS_PATH = ROOT / "boards.json"


def load_boards(path: Path | None = None) -> dict[str, list[dict[str, str]]]:
    p = path or BOARDS_PATH
    data = json.loads(p.read_text(encoding="utf-8"))
    out: dict[str, list[dict[str, str]]] = {}
    for key in ("greenhouse", "ashby", "lever"):
        rows = []
        for row in data.get(key) or []:
            token = (row.get("token") or "").strip()
            if not token or token.startswith("//") or (row.get("company") or "").upper() == "SKIP":
                continue
            rows.append(row)
        out[key] = rows
    return out


def discover(
    *,
    sources: Optional[list[str]] = None,
    boards_path: Path | None = None,
    target_countries: Optional[set[str]] = None,
    require_country_match: bool = False,
    arbeitnow_pages: int = 2,
    max_jobs_per_source: int = 60,
    include_stubs_in_meta: bool = True,
) -> dict[str, Any]:
    """Run live adapters and return ranked, deduped jobs + scrape-compatible hits."""
    wanted = set(sources or ["arbeitnow", "greenhouse", "ashby", "lever"])
    boards = load_boards(boards_path)
    today = date.today().isoformat()
    collected: list[NormalizedJob] = []
    errors: list[str] = []
    source_meta: dict[str, Any] = {}

    if "arbeitnow" in wanted:
        result = LIVE_SOURCES["arbeitnow"]().fetch(
            pages=arbeitnow_pages,
            visa_sponsorship=True,
            max_jobs=max_jobs_per_source,
        )
        collected.extend(result.jobs)
        errors.extend(result.errors)
        source_meta["arbeitnow"] = {"count": len(result.jobs), **result.meta}

    if "greenhouse" in wanted:
        result = LIVE_SOURCES["greenhouse"]().fetch(
            boards=boards.get("greenhouse"),
            max_jobs=max_jobs_per_source,
        )
        collected.extend(result.jobs)
        errors.extend(result.errors)
        source_meta["greenhouse"] = {"count": len(result.jobs), **result.meta}

    if "ashby" in wanted:
        result = LIVE_SOURCES["ashby"]().fetch(
            boards=boards.get("ashby"),
            max_jobs=max_jobs_per_source,
        )
        collected.extend(result.jobs)
        errors.extend(result.errors)
        source_meta["ashby"] = {"count": len(result.jobs), **result.meta}

    if "lever" in wanted:
        result = LIVE_SOURCES["lever"]().fetch(
            boards=boards.get("lever"),
            max_jobs=max_jobs_per_source,
        )
        collected.extend(result.jobs)
        errors.extend(result.errors)
        source_meta["lever"] = {"count": len(result.jobs), **result.meta}

    if include_stubs_in_meta:
        for name, stub in STUB_SOURCES.items():
            source_meta[name] = stub.fetch().meta

    preferred = target_countries or set(TARGET_COUNTRIES)
    if require_country_match:
        collected = [
            j
            for j in collected
            if j.country is None or country_in_targets(j.country, preferred) or j.workplace == "remote"
        ]

    for job in collected:
        job.last_seen = today

    deduped = dedupe_jobs(collected)
    ranked = rank_jobs(deduped, preferred_countries=preferred)

    results = []
    scrape_hits = []
    for job, scores in ranked:
        item = job.to_dict()
        item["rank"] = asdict(scores)
        results.append(item)
        hit = job.to_scrape_hit()
        hit["rank_overall"] = scores.overall
        hit["sponsorship_score"] = scores.sponsorship_score
        hit["skill_score"] = scores.skill_score
        scrape_hits.append(hit)

    meta: dict[str, Any] = {
        "date": today,
        "raw_count": len(collected),
        "deduped_count": len(deduped),
        "sources": source_meta,
        "errors": errors,
    }
    if "arbeitnow" in wanted:
        meta["arbeitnow_attribution"] = (
            "Job data from Arbeitnow.com (link back required by their API terms)."
        )
    return {
        "meta": meta,
        "results": results,
        "scrape_hits": scrape_hits,
    }
