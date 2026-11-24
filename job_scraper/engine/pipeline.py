"""Orchestrate fetch → classify → dedupe → rank for visa-aware discovery."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any, Optional

from .dedupe import dedupe_jobs
from .freshness import (
    filter_new_only,
    filter_since,
    load_blocked_companies,
    load_seen_identities,
    parse_since,
)
from .model import NormalizedJob
from .normalize import TARGET_COUNTRIES, country_in_targets
from .path_filter import filter_path_ab
from .rank import rank_jobs
from .sources import LIVE_SOURCES, STUB_SOURCES

ROOT = Path(__file__).resolve().parent.parent
BOARDS_PATH = ROOT / "boards.json"

BOARD_KEYS = (
    "greenhouse",
    "ashby",
    "lever",
    "workable",
    "personio",
    "teamtailor",
    "smartrecruiters",
    "recruitee",
)
DEFAULT_SOURCES = [
    "arbeitnow",
    "greenhouse",
    "ashby",
    "lever",
    "workable",
    "personio",
    "teamtailor",
    "smartrecruiters",
    "recruitee",
    "landingjobs",
]

# Board-volume pack (JobSpy / jobdrop / Hiring Cafe ideas) — opt-in via --volume
VOLUME_SOURCES = [
    "jobspy",
    "remoteok",
    "weworkremotely",
    "hiringcafe",
]


def load_boards(path: Path | None = None) -> dict[str, list[dict[str, str]]]:
    p = path or BOARDS_PATH
    data = json.loads(p.read_text(encoding="utf-8"))
    out: dict[str, list[dict[str, str]]] = {}
    for key in BOARD_KEYS:
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
    path_ab_only: bool = False,
    since: str | int | None = None,
    new_only: bool = False,
    arbeitnow_pages: int = 2,
    max_jobs_per_source: int = 150,
    include_stubs_in_meta: bool = True,
) -> dict[str, Any]:
    """Run live adapters and return ranked, deduped jobs + scrape-compatible hits."""
    wanted = set(sources or DEFAULT_SOURCES)
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

    if "landingjobs" in wanted:
        result = LIVE_SOURCES["landingjobs"]().fetch(max_jobs=max_jobs_per_source)
        collected.extend(result.jobs)
        errors.extend(result.errors)
        source_meta["landingjobs"] = {"count": len(result.jobs), **result.meta}

    if "remoteok" in wanted:
        result = LIVE_SOURCES["remoteok"]().fetch(max_jobs=min(60, max_jobs_per_source))
        collected.extend(result.jobs)
        errors.extend(result.errors)
        source_meta["remoteok"] = {"count": len(result.jobs), **result.meta}
        if result.meta.get("attribution"):
            source_meta["remoteok_attribution"] = result.meta["attribution"]

    if "weworkremotely" in wanted:
        result = LIVE_SOURCES["weworkremotely"]().fetch(max_jobs=min(40, max_jobs_per_source))
        collected.extend(result.jobs)
        errors.extend(result.errors)
        source_meta["weworkremotely"] = {"count": len(result.jobs), **result.meta}

    if "jobspy" in wanted:
        # Depth pack: multi-country Indeed + Pakistan any-mode; allow higher cap.
        result = LIVE_SOURCES["jobspy"]().fetch(
            max_jobs=max(180, max_jobs_per_source),
            results_wanted=25,
        )
        collected.extend(result.jobs)
        errors.extend(result.errors)
        source_meta["jobspy"] = {"count": len(result.jobs), **result.meta}

    if "hiringcafe" in wanted:
        result = LIVE_SOURCES["hiringcafe"]().fetch(max_jobs=min(40, max_jobs_per_source))
        collected.extend(result.jobs)
        errors.extend(result.errors)
        source_meta["hiringcafe"] = {"count": len(result.jobs), **result.meta}

    for key in (
        "greenhouse",
        "ashby",
        "lever",
        "workable",
        "personio",
        "teamtailor",
        "smartrecruiters",
        "recruitee",
    ):
        if key not in wanted:
            continue
        result = LIVE_SOURCES[key]().fetch(
            boards=boards.get(key),
            max_jobs=max_jobs_per_source,
        )
        collected.extend(result.jobs)
        errors.extend(result.errors)
        source_meta[key] = {"count": len(result.jobs), **result.meta}

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

    since_days = parse_since(since)
    pre_since = len(collected)
    collected = filter_since(collected, since_days)
    dropped_by_since = pre_since - len(collected)

    path_near: list[dict[str, str]] = []
    if path_ab_only:
        collected, path_near = filter_path_ab(collected)

    dropped_seen = 0
    if new_only:
        urls, pairs = load_seen_identities()
        blocked = load_blocked_companies()
        before = len(collected)
        collected = filter_new_only(
            collected,
            seen_urls=urls,
            seen_pairs=pairs,
            blocked_companies=blocked,
        )
        dropped_seen = before - len(collected)

    for job in collected:
        job.last_seen = today

    deduped = dedupe_jobs(collected)
    ranked = rank_jobs(deduped, preferred_countries=preferred)

    results = []
    scrape_hits = []
    for job, scores in ranked:
        item = job.to_dict()
        item["rank"] = asdict(scores)
        if job.raw.get("path"):
            item["path"] = job.raw["path"]
            item["path_reason"] = job.raw.get("path_reason")
        results.append(item)
        hit = job.to_scrape_hit()
        hit["rank_overall"] = scores.overall
        hit["sponsorship_score"] = scores.sponsorship_score
        hit["skill_score"] = scores.skill_score
        if job.raw.get("path"):
            hit["path"] = job.raw["path"]
        scrape_hits.append(hit)

    meta: dict[str, Any] = {
        "date": today,
        "raw_count": len(collected),
        "deduped_count": len(deduped),
        "sources": source_meta,
        "errors": errors,
        "path_ab_only": path_ab_only,
        "path_near_miss_count": len(path_near),
        "since_days": since_days,
        "dropped_by_since": dropped_by_since,
        "new_only": new_only,
        "dropped_as_seen": dropped_seen,
    }
    if "arbeitnow" in wanted:
        meta["arbeitnow_attribution"] = (
            "Job data from Arbeitnow.com (link back required by their API terms)."
        )
    out: dict[str, Any] = {
        "meta": meta,
        "results": results,
        "scrape_hits": scrape_hits,
    }
    if path_ab_only:
        out["path_near_misses"] = path_near[:40]
    return out
