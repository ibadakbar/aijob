#!/usr/bin/env python3
"""Harvest live ATS board tokens from inventory CSVs into boards.json.

Inspired by mherzog4/job-boards discovery + kalil0321/ats-scrapers inventories.
Probes each candidate (live 200 + jobs>=min) before merge — never dumps dead slugs.

Examples:
  python tools/harvest_boards.py --ats greenhouse,ashby --limit 40 --min-jobs 1 --write
  python tools/harvest_boards.py --ats smartrecruiters,recruitee --limit 20 --dry-run
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

from job_scraper.engine.pipeline import BOARD_KEYS, BOARDS_PATH, load_boards  # noqa: E402

sys.path.insert(0, str(ROOT / "tools"))
from probe_boards import probe_one  # noqa: E402

INVENTORY = ROOT / "job_scraper" / "ats_inventories"

# Map boards.json key → inventory CSV
INV_MAP = {
    "greenhouse": "greenhouse.csv",
    "ashby": "ashby.csv",
    "lever": "lever.csv",
    "workable": "workable.csv",
    "personio": "personio.csv",
    "teamtailor": "teamtailor.csv",
    "smartrecruiters": "smartrecruiters.csv",
    "recruitee": "recruitee.csv",
}


def _personio_token(slug: str, url: str) -> str:
    # Prefer host from URL when present
    if "jobs.personio." in (url or ""):
        try:
            from urllib.parse import urlsplit

            return urlsplit(url).netloc
        except Exception:  # noqa: BLE001
            pass
    return f"{slug}.jobs.personio.com"


def _teamtailor_token(slug: str, url: str) -> str:
    if "teamtailor.com" in (url or ""):
        try:
            from urllib.parse import urlsplit

            return urlsplit(url).netloc
        except Exception:  # noqa: BLE001
            pass
    return f"{slug}.teamtailor.com"


_TECHISH = re.compile(
    r"\b(tech|software|digital|data|cloud|cyber|ai|labs?|systems?|"
    r"solutions?|platform|saas|fintech|healthtech|media|games?|studio)\b",
    re.I,
)


def load_inventory(
    ats: str,
    *,
    limit: int,
    offset: int = 0,
    prefer_tech: bool = True,
) -> list[dict[str, str]]:
    path = INVENTORY / INV_MAP[ats]
    if not path.exists():
        raise FileNotFoundError(f"missing inventory {path}")
    preferred: list[dict[str, str]] = []
    other: list[dict[str, str]] = []
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for i, row in enumerate(reader):
            if i < offset:
                continue
            slug = (row.get("slug") or "").strip()
            name = (row.get("name") or slug).strip()
            url = (row.get("url") or "").strip()
            if not slug:
                continue
            if ats == "personio":
                token = _personio_token(slug, url)
            elif ats == "teamtailor":
                token = _teamtailor_token(slug, url)
            else:
                token = slug
            item = {"token": token, "company": name}
            if prefer_tech and _TECHISH.search(name):
                preferred.append(item)
            else:
                other.append(item)
            if len(preferred) + len(other) >= max(limit * 8, 200):
                # enough pool to fill after tech preference
                break
    ordered = preferred + other if prefer_tech else other + preferred
    return ordered[:limit]



def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--ats",
        default="greenhouse,ashby",
        help="Comma-separated ATS keys with inventories",
    )
    parser.add_argument("--limit", type=int, default=30, help="Candidates to probe per ATS")
    parser.add_argument("--offset", type=int, default=0, help="Skip first N inventory rows per ATS")
    parser.add_argument("--min-jobs", type=int, default=1)
    parser.add_argument("--boards", type=Path, default=BOARDS_PATH)
    parser.add_argument("--write", action="store_true", help="Merge live hits into boards.json")
    parser.add_argument("--dry-run", action="store_true", help="Probe only; never write")
    args = parser.parse_args()

    wanted = [s.strip() for s in args.ats.split(",") if s.strip()]
    current = load_boards(args.boards)
    # Also keep raw for write-back of unknown keys
    raw = json.loads(args.boards.read_text(encoding="utf-8"))

    added: dict[str, list[dict[str, str]]] = {k: [] for k in BOARD_KEYS}
    for ats in wanted:
        if ats not in INV_MAP:
            print(f"skip unknown ats={ats}", file=sys.stderr)
            continue
        existing = {(r.get("token") or "").strip() for r in current.get(ats) or []}
        candidates = load_inventory(ats, limit=args.limit, offset=args.offset)
        print(f"=== {ats}: probing {len(candidates)} candidates (skip {len(existing)} known) ===")
        for row in candidates:
            token = row["token"]
            if token in existing:
                continue
            result = probe_one(ats, token)
            jobs = result.get("jobs") or 0
            ok = bool(result.get("ok")) and jobs >= args.min_jobs
            flag = "OK" if ok else "FAIL"
            print(f"{flag}\t{ats}\t{token}\tjobs={jobs}\t{result.get('error') or ''}")
            if ok:
                added[ats].append({"token": token, "company": row["company"], "notes": f"harvest jobs={jobs}"})
                existing.add(token)

    total_new = sum(len(v) for v in added.values())
    print(f"Live new boards: {total_new}", file=sys.stderr)
    if args.write and not args.dry_run and total_new:
        for ats, rows in added.items():
            if not rows:
                continue
            raw.setdefault(ats, [])
            raw[ats].extend(rows)
        args.boards.write_text(json.dumps(raw, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Wrote {args.boards}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
