#!/usr/bin/env python3
"""Probe public ATS board tokens and report which return live jobs.

Examples:
  python tools/probe_boards.py
  python tools/probe_boards.py --ats greenhouse,workable --only-ok
  python tools/probe_boards.py --candidates-file /tmp/extra_tokens.json --ats ashby

Does not write boards.json; print OK rows and optionally --write-ok for a merge hint JSON.
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from job_scraper.engine.http import UA  # noqa: E402
from job_scraper.engine.pipeline import BOARD_KEYS, BOARDS_PATH, load_boards  # noqa: E402

ENDPOINTS = {
    "greenhouse": "https://boards-api.greenhouse.io/v1/boards/{token}/jobs",
    "ashby": "https://api.ashbyhq.com/posting-api/job-board/{token}",
    "lever": "https://api.lever.co/v0/postings/{token}?mode=json&limit=100",
    "workable": "https://apply.workable.com/api/v1/widget/accounts/{token}?details=true",
    "personio": "https://{token}/xml?language=en",
    "teamtailor": "https://{token}/jobs.json",
    "smartrecruiters": "https://api.smartrecruiters.com/v1/companies/{token}/postings?limit=10&offset=0",
    "recruitee": "https://{token}.recruitee.com/api/offers",
}


def _fetch(url: str, timeout: float = 20.0) -> tuple[int | None, bytes | None, str | None]:
    try:
        req = Request(url, headers={"User-Agent": UA, "Accept": "application/json,application/xml,*/*"})
        with urlopen(req, timeout=timeout) as resp:  # noqa: S310
            return resp.status, resp.read(), None
    except HTTPError as exc:
        return exc.code, None, str(exc.reason)
    except (URLError, TimeoutError, OSError) as exc:
        return None, None, type(exc).__name__ + ":" + str(exc)


def _personio_host(token: str) -> str:
    return token if "." in token else f"{token}.jobs.personio.com"


def _teamtailor_host(token: str) -> str:
    return token if "." in token else f"{token}.teamtailor.com"


def _count_jobs(ats: str, raw: bytes) -> int:
    if ats == "personio":
        root = ET.fromstring(raw)
        return len(root.findall("position"))
    data = json.loads(raw)
    if ats == "lever":
        return len(data) if isinstance(data, list) else -1
    if ats == "teamtailor":
        return len((data or {}).get("items") or [])
    if ats in ("greenhouse", "ashby", "workable"):
        return len((data or {}).get("jobs") or [])
    if ats == "smartrecruiters":
        if isinstance(data, dict):
            if "totalFound" in data:
                return int(data.get("totalFound") or 0)
            return len(data.get("content") or [])
        return -1
    if ats == "recruitee":
        return len((data or {}).get("offers") or []) if isinstance(data, dict) else -1
    return -1


def probe_one(ats: str, token: str) -> dict[str, Any]:
    t = token.strip()
    if ats == "personio":
        url = ENDPOINTS[ats].format(token=_personio_host(t))
    elif ats == "teamtailor":
        url = ENDPOINTS[ats].format(token=_teamtailor_host(t))
    elif ats == "recruitee":
        if t.startswith("http://") or t.startswith("https://"):
            from urllib.parse import urlsplit

            host = urlsplit(t).netloc
            url = f"https://{host}/api/offers"
        elif "." in t:
            url = f"https://{t}/api/offers"
        else:
            url = ENDPOINTS[ats].format(token=t)
    else:
        url = ENDPOINTS[ats].format(token=t)
    code, raw, err = _fetch(url)
    if code == 200 and raw is not None:
        try:
            n = _count_jobs(ats, raw)
        except Exception as exc:  # noqa: BLE001
            return {"ats": ats, "token": t, "ok": False, "status": code, "jobs": None, "error": str(exc), "url": url}
        return {"ats": ats, "token": t, "ok": True, "status": code, "jobs": n, "error": None, "url": url}
    return {"ats": ats, "token": t, "ok": False, "status": code, "jobs": None, "error": err, "url": url}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--boards", type=Path, default=BOARDS_PATH)
    parser.add_argument(
        "--ats",
        default=",".join(BOARD_KEYS),
        help="Comma-separated ATS keys to probe",
    )
    parser.add_argument("--only-ok", action="store_true", help="Print only HTTP 200 boards")
    parser.add_argument("--min-jobs", type=int, default=0, help="Require at least N jobs when --only-ok")
    parser.add_argument(
        "--candidates-file",
        type=Path,
        help='Optional JSON {"greenhouse":[{"token":"...","company":"..."}], ...} to probe instead of boards.json',
    )
    parser.add_argument(
        "--write-ok",
        type=Path,
        help="Write OK rows (status 200) as boards-shaped JSON for manual merge",
    )
    args = parser.parse_args()

    if args.candidates_file:
        data = json.loads(args.candidates_file.read_text(encoding="utf-8"))
        boards = {k: [r for r in (data.get(k) or []) if (r.get("token") or "").strip()] for k in BOARD_KEYS}
    else:
        boards = load_boards(args.boards)

    wanted = [s.strip() for s in args.ats.split(",") if s.strip()]
    rows: list[dict[str, Any]] = []
    for ats in wanted:
        if ats not in ENDPOINTS:
            print(f"skip unknown ats={ats}", file=sys.stderr)
            continue
        for row in boards.get(ats) or []:
            token = (row.get("token") or "").strip()
            if not token:
                continue
            result = probe_one(ats, token)
            result["company"] = row.get("company") or token
            rows.append(result)
            show = result["ok"] and (result.get("jobs") or 0) >= args.min_jobs
            if args.only_ok and not show:
                continue
            flag = "OK" if result["ok"] else "FAIL"
            jobs = result.get("jobs")
            err = result.get("error") or ""
            print(f"{flag}\t{ats}\t{token}\tjobs={jobs}\t{err}")

    if args.write_ok:
        out: dict[str, list[dict[str, str]]] = {k: [] for k in BOARD_KEYS}
        for r in rows:
            if not r.get("ok"):
                continue
            if args.min_jobs and (r.get("jobs") or 0) < args.min_jobs:
                continue
            out[r["ats"]].append({"token": r["token"], "company": r.get("company") or r["token"]})
        args.write_ok.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Wrote OK boards → {args.write_ok}", file=sys.stderr)

    ok = sum(1 for r in rows if r.get("ok"))
    print(f"Probed {len(rows)} boards; {ok} OK", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
