#!/usr/bin/env python3
"""CLI for the visa / relocation discovery engine.

Examples:
  python tools/visa_discover.py --path-ab --since 14d --new-only --limit 30
  python tools/visa_discover.py --volume --path-ab --since 14d --new-only --limit 40

--volume adds JobSpy + RemoteOK + WeWorkRemotely + HiringCafe (Apify if token set).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))


def _load_repo_dotenv() -> None:
    """Load gitignored `.env` into os.environ (does not override existing vars)."""
    path = ROOT / ".env"
    if not path.is_file():
        return
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = val


_load_repo_dotenv()

from job_scraper.engine.pipeline import DEFAULT_SOURCES, VOLUME_SOURCES, discover  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--sources",
        default=None,
        help="Comma-separated live sources (default: ATS + Arbeitnow + Landing.jobs)",
    )
    parser.add_argument(
        "--volume",
        action="store_true",
        help="Also run JobSpy/RemoteOK/WWR/HiringCafe board-volume pack",
    )
    parser.add_argument("--limit", type=int, default=40, help="Max ranked rows to print/write")
    parser.add_argument(
        "--format",
        choices=("summary", "json", "scrape"),
        default="summary",
    )
    parser.add_argument("--out", type=Path, help="Write full JSON payload here")
    parser.add_argument(
        "--scrape-hits",
        type=Path,
        help="Write scrape_state-compatible hits JSON array here",
    )
    parser.add_argument("--arbeitnow-pages", type=int, default=2)
    parser.add_argument(
        "--max-jobs-per-source",
        type=int,
        default=150,
        help="Cap raw jobs kept per ATS adapter (default 150)",
    )
    parser.add_argument(
        "--require-country",
        action="store_true",
        help="Drop jobs whose country is set and outside the target list (keeps remote/unknown)",
    )
    parser.add_argument(
        "--path-ab",
        action="store_true",
        help="Keep only Path A (remote+intl/sponsor) or Path B (onsite/hybrid+verified sponsor/reloc)",
    )
    parser.add_argument(
        "--since",
        default=None,
        help="Freshness window: 7d, 2w, 30, or days int (keeps undated)",
    )
    parser.add_argument(
        "--new-only",
        action="store_true",
        help="Drop URLs/company+title already in seen_jobs.json or job_search_tracker.csv",
    )
    args = parser.parse_args()

    if args.sources:
        sources = [s.strip() for s in args.sources.split(",") if s.strip()]
    else:
        sources = list(DEFAULT_SOURCES)
    if args.volume:
        for s in VOLUME_SOURCES:
            if s not in sources:
                sources.append(s)

    try:
        payload = discover(
            sources=sources,
            arbeitnow_pages=args.arbeitnow_pages,
            require_country_match=args.require_country,
            path_ab_only=args.path_ab,
            since=args.since,
            new_only=args.new_only,
            max_jobs_per_source=args.max_jobs_per_source,
        )
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"error": str(exc), "code": "DISCOVER_FAILED"}), file=sys.stderr)
        return 1

    results = payload["results"][: args.limit]
    hits = payload["scrape_hits"][: args.limit]
    payload_out = {**payload, "results": results, "scrape_hits": hits}

    if args.out:
        args.out.write_text(json.dumps(payload_out, indent=2, ensure_ascii=False), encoding="utf-8")
    if args.scrape_hits:
        args.scrape_hits.write_text(json.dumps(hits, indent=2, ensure_ascii=False), encoding="utf-8")

    if args.format == "json":
        print(json.dumps(payload_out, ensure_ascii=False, indent=2))
    elif args.format == "scrape":
        print(json.dumps(hits, ensure_ascii=False, indent=2))
    else:
        meta = payload["meta"]
        print(
            f"Visa discovery {meta['date']}: {meta['deduped_count']} unique "
            f"(from {meta['raw_count']} raw). Showing top {len(results)}."
        )
        if args.volume:
            print(f"Volume pack on: {', '.join(VOLUME_SOURCES)}")
        if meta.get("path_ab_only"):
            print(
                f"Path A/B filter on — near-misses dropped: {meta.get('path_near_miss_count', 0)}"
            )
        if meta.get("since_days") is not None:
            print(
                f"Since {meta['since_days']}d — dropped {meta.get('dropped_by_since', 0)} older dated rows"
            )
        if meta.get("new_only"):
            print(f"New-only — dropped {meta.get('dropped_as_seen', 0)} already-seen rows")
        if meta.get("errors"):
            print(f"Source errors: {len(meta['errors'])} (see --format json meta.errors)")
        if meta.get("arbeitnow_attribution"):
            print(meta["arbeitnow_attribution"])
        rok = (meta.get("sources") or {}).get("remoteok_attribution") or (
            (meta.get("sources") or {}).get("remoteok") or {}
        ).get("attribution")
        if rok:
            print(rok)
        print()
        print(
            f"{'#':>3} {'Overall':>7} {'Spons':>5} {'Skill':>5}  "
            f"{'Path':<4} {'Classification':<22} Company / Title"
        )
        for i, row in enumerate(results, 1):
            rank = row.get("rank") or {}
            sp = (row.get("sponsorship") or {}).get("classification", "unknown")
            path = row.get("path") or "-"
            print(
                f"{i:3d} {rank.get('overall', 0):7.3f} {rank.get('sponsorship_score', 0):5.2f} "
                f"{rank.get('skill_score', 0):5.2f}  {path:<4} {sp:<22} "
                f"{row.get('company','')[:22]} — {row.get('title','')[:48]}"
            )
            print(f"     {row.get('url')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
