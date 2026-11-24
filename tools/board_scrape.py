#!/usr/bin/env python3
"""Board-volume scrape (JobSpy + RemoteOK + WWR + optional Hiring Cafe).

Thin wrapper around visa_discover --volume with Path A/B defaults for leads.

Examples:
  python tools/board_scrape.py
  python tools/board_scrape.py --limit 25 --scrape-hits %TEMP%\\board_hits.json
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VISA = ROOT / "tools" / "visa_discover.py"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--since", default="14d")
    parser.add_argument("--scrape-hits", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--format", default="summary", choices=("summary", "json", "scrape"))
    parser.add_argument("--no-path-ab", action="store_true", help="Disable Path A/B filter")
    parser.add_argument("--no-new-only", action="store_true")
    args = parser.parse_args()

    cmd = [
        sys.executable,
        str(VISA),
        "--volume",
        "--since",
        args.since,
        "--limit",
        str(args.limit),
        "--format",
        args.format,
        "--max-jobs-per-source",
        "180",
    ]
    if not args.no_path_ab:
        cmd.append("--path-ab")
    if not args.no_new_only:
        cmd.append("--new-only")
    if args.scrape_hits:
        cmd.extend(["--scrape-hits", str(args.scrape_hits)])
    if args.out:
        cmd.extend(["--out", str(args.out)])

    print("Running:", " ".join(cmd), file=sys.stderr)
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
