#!/usr/bin/env python3
"""CLI for the visa / relocation discovery engine.

Examples:
  python tools/visa_discover.py --format summary
  python tools/visa_discover.py --sources arbeitnow,greenhouse --limit 20 --out /tmp/hits.json
  python tools/visa_discover.py --scrape-hits /tmp/scrape_hits.json

Output shapes:
  summary  — compact table for humans
  json     — full ranked results (+ meta)
  scrape   — array compatible with tools/scrape_state.py candidates

Does not submit applications. Does not invent sponsorship claims.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# Allow `from job_scraper.engine...` and tools/ imports
sys.path.insert(0, str(ROOT / "tools"))

from job_scraper.engine.pipeline import discover  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--sources",
        default="arbeitnow,greenhouse,ashby,lever",
        help="Comma-separated live sources (default: all live)",
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
        "--require-country",
        action="store_true",
        help="Drop jobs whose country is set and outside the target list (keeps remote/unknown)",
    )
    args = parser.parse_args()
    sources = [s.strip() for s in args.sources.split(",") if s.strip()]

    try:
        payload = discover(
            sources=sources,
            arbeitnow_pages=args.arbeitnow_pages,
            require_country_match=args.require_country,
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
        if meta.get("errors"):
            print(f"Source errors: {len(meta['errors'])} (see --format json meta.errors)")
        if meta.get("arbeitnow_attribution"):
            print(meta["arbeitnow_attribution"])
        print()
        print(f"{'#':>3} {'Overall':>7} {'Spons':>5} {'Skill':>5}  Classification          Company / Title")
        for i, row in enumerate(results, 1):
            rank = row.get("rank") or {}
            sp = (row.get("sponsorship") or {}).get("classification", "unknown")
            print(
                f"{i:3d} {rank.get('overall', 0):7.3f} {rank.get('sponsorship_score', 0):5.2f} "
                f"{rank.get('skill_score', 0):5.2f}  {sp:<22} {row.get('company','')[:22]} — {row.get('title','')[:48]}"
            )
            print(f"     {row.get('url')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
