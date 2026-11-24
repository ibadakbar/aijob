#!/usr/bin/env python3
"""Resolve a company name/slug to live ATS boards (career-ops discover + ats-scrapers find_company).

Probes Greenhouse / Ashby / Lever / Workable / SmartRecruiters / Recruitee for a slug,
and looks up inventory CSVs by name/slug.

Examples:
  python tools/discover_company_ats.py openai
  python tools/discover_company_ats.py "Linear" --write
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from job_scraper.engine.pipeline import BOARDS_PATH, load_boards  # noqa: E402
from probe_boards import probe_one  # noqa: E402

INVENTORY = ROOT / "job_scraper" / "ats_inventories"
PROBE_ATS = ("greenhouse", "ashby", "lever", "workable", "smartrecruiters", "recruitee")


def _slugify(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "", s)
    return s


def inventory_hits(query: str) -> list[dict[str, str]]:
    q = query.strip().lower()
    slug_q = _slugify(query)
    hits: list[dict[str, str]] = []
    for csv_name in INVENTORY.glob("*.csv"):
        ats = csv_name.stem
        with csv_name.open(encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                name = (row.get("name") or "").strip()
                slug = (row.get("slug") or "").strip()
                url = (row.get("url") or "").strip()
                if not slug:
                    continue
                if slug.lower() == slug_q or slug.lower() == q or q in name.lower():
                    hits.append({"ats": ats, "token": slug, "company": name or slug, "url": url})
    return hits


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("company", help="Company name or ATS slug")
    parser.add_argument("--write", action="store_true", help="Append live hits into boards.json")
    parser.add_argument("--boards", type=Path, default=BOARDS_PATH)
    args = parser.parse_args()

    slug = _slugify(args.company)
    print(f"Query={args.company!r} slug={slug!r}")
    inv = inventory_hits(args.company)
    if inv:
        print(f"Inventory matches: {len(inv)}")
        for h in inv[:12]:
            print(f"  inv\t{h['ats']}\t{h['token']}\t{h['company']}\t{h['url']}")

    # Probe common slugs (query slug + inventory tokens)
    tokens = [slug]
    for h in inv:
        if h["ats"] in PROBE_ATS and h["token"] not in tokens:
            tokens.append(h["token"])

    live: list[dict[str, str]] = []
    for token in tokens[:8]:
        for ats in PROBE_ATS:
            result = probe_one(ats, token)
            jobs = result.get("jobs")
            if result.get("ok") and (jobs or 0) >= 1:
                print(f"LIVE\t{ats}\t{token}\tjobs={jobs}")
                live.append({"ats": ats, "token": token, "company": args.company, "jobs": str(jobs)})
            else:
                print(f"miss\t{ats}\t{token}\t{result.get('status')}\t{result.get('error') or ''}")

    if args.write and live:
        raw = json.loads(args.boards.read_text(encoding="utf-8"))
        boards = load_boards(args.boards)
        for row in live:
            ats = row["ats"]
            existing = {(r.get("token") or "") for r in boards.get(ats) or []}
            if row["token"] in existing:
                continue
            raw.setdefault(ats, []).append(
                {
                    "token": row["token"],
                    "company": row["company"],
                    "notes": f"discover jobs={row['jobs']}",
                }
            )
        args.boards.write_text(json.dumps(raw, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Wrote {args.boards}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
