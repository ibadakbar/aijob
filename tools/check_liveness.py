#!/usr/bin/env python3
"""Check whether job posting URLs are still live (career-ops liveness pattern).

Examples:
  python tools/check_liveness.py https://jobs.ashbyhq.com/openai/...
  python tools/check_liveness.py --file urls.txt
  python tools/check_liveness.py --json hits.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from job_scraper.engine.http import fetch_status  # noqa: E402

_CLOSED_HINTS = re.compile(
    r"(no longer available|job not found|position (has been )?filled|"
    r"this job is closed|posting (has )?expired|404|page not found|"
    r"no longer accepting|requisition not found)",
    re.I,
)


def classify(url: str) -> dict:
    code, body_or_note = fetch_status(url)
    if code is None:
        return {"url": url, "status": "unknown", "http": None, "note": body_or_note}
    if code in (404, 410, 451):
        return {"url": url, "status": "closed", "http": code, "note": body_or_note}
    if code >= 400:
        return {"url": url, "status": "error", "http": code, "note": body_or_note}
    if isinstance(body_or_note, str) and _CLOSED_HINTS.search(body_or_note):
        return {"url": url, "status": "likely_closed", "http": code, "note": "closed language in body"}
    return {"url": url, "status": "open", "http": code, "note": ""}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("urls", nargs="*", help="Posting URLs")
    parser.add_argument("--file", type=Path, help="Text file, one URL per line")
    parser.add_argument("--json", type=Path, help="JSON array of hits with url field")
    args = parser.parse_args()

    urls: list[str] = list(args.urls)
    if args.file:
        urls.extend(
            line.strip()
            for line in args.file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        )
    if args.json:
        data = json.loads(args.json.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data = data.get("scrape_hits") or data.get("results") or data.get("selected") or []
        for row in data or []:
            if isinstance(row, dict) and isinstance(row.get("url"), str):
                urls.append(row["url"])

    if not urls:
        print("No URLs provided", file=sys.stderr)
        return 2

    results = [classify(u) for u in urls]
    open_n = sum(1 for r in results if r["status"] == "open")
    closed_n = sum(1 for r in results if r["status"] in ("closed", "likely_closed"))
    for r in results:
        print(f"{r['status']:<14} HTTP={r['http']!s:<4} {r['url']}")
        if r["note"] and r["status"] != "open":
            print(f"               {r['note'][:120]}")
    print(f"Summary: {open_n} open / {closed_n} closed-or-likely / {len(results)} total", file=sys.stderr)
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
