"""Fast freehire.me search adapter for the opportunity agent."""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Any

from agent.discovery.jobs.query_packs import QueryPack

ROOT = Path(__file__).resolve().parents[3]
CLI = ROOT / ".agents" / "skills" / "freehire-search" / "cli" / "src" / "cli.ts"
log = logging.getLogger("opportunity_agent")

# ISO → display (for Excel country column)
_ISO_NAME = {
    "de": "Germany",
    "nl": "Netherlands",
    "gb": "United Kingdom",
    "ie": "Ireland",
    "us": "United States",
    "ca": "Canada",
    "au": "Australia",
    "nz": "New Zealand",
    "se": "Sweden",
    "dk": "Denmark",
    "fi": "Finland",
    "no": "Norway",
    "be": "Belgium",
    "ch": "Switzerland",
    "cz": "Czechia",
    "ae": "UAE",
    "sa": "Saudi Arabia",
    "qa": "Qatar",
    "pk": "Pakistan",
    "sg": "Singapore",
    "in": "India",
}


def _bun() -> str:
    found = shutil.which("bun")
    if found:
        return found
    # Common Windows installs
    for candidate in (
        Path.home() / ".bun" / "bin" / "bun.exe",
        Path(r"C:\Users") / Path.home().name / ".bun" / "bin" / "bun.exe",
    ):
        if candidate.is_file():
            return str(candidate)
    return "bun"


def run_freehire_pack(
    pack: QueryPack,
    *,
    timeout: int = 90,
    with_description: bool = True,
) -> dict[str, Any]:
    """Run one freehire search pack. Returns {ok, jobs, hits, error, query}."""
    if not CLI.is_file():
        return {"ok": False, "jobs": [], "hits": 0, "error": "freehire CLI missing", "query": pack.freehire_q}

    cmd = [
        _bun(),
        "run",
        str(CLI),
        "search",
        "-q",
        pack.freehire_q,
        "--format",
        "json",
    ]
    extra = dict(pack.freehire_extra or {})
    if "limit" in extra:
        cmd.extend(["--limit", str(extra.pop("limit"))])
    if "jobage" in extra:
        cmd.extend(["--jobage", str(extra.pop("jobage"))])
    if "remote" in extra:
        cmd.extend(["--remote", str(extra.pop("remote"))])
    if "country" in extra:
        cmd.extend(["--country", str(extra.pop("country"))])
    if "region" in extra:
        cmd.extend(["--region", str(extra.pop("region"))])
    if "seniority" in extra:
        cmd.extend(["--seniority", str(extra.pop("seniority"))])
    if "category" in extra:
        cmd.extend(["--category", str(extra.pop("category"))])
    if "skill" in extra:
        cmd.extend(["--skill", str(extra.pop("skill"))])
    if not with_description:
        cmd.append("--no-description")

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
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "jobs": [],
            "hits": 0,
            "error": f"freehire timeout {timeout}s",
            "query": pack.freehire_q,
            "pack_id": pack.id,
        }
    except OSError as exc:
        return {
            "ok": False,
            "jobs": [],
            "hits": 0,
            "error": str(exc),
            "query": pack.freehire_q,
            "pack_id": pack.id,
        }

    raw = (proc.stdout or "").strip()
    if not raw:
        err = (proc.stderr or "")[-800:]
        return {
            "ok": False,
            "jobs": [],
            "hits": 0,
            "error": err or f"empty stdout exit={proc.returncode}",
            "query": pack.freehire_q,
            "pack_id": pack.id,
        }

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {
            "ok": False,
            "jobs": [],
            "hits": 0,
            "error": "invalid JSON from freehire",
            "query": pack.freehire_q,
            "pack_id": pack.id,
        }

    results = data.get("results") if isinstance(data, dict) else data
    if not isinstance(results, list):
        results = []
    jobs = [_normalize_hit(r, pack) for r in results if isinstance(r, dict)]
    jobs = [j for j in jobs if j.get("url") and j.get("company") and j.get("title")]
    total = 0
    if isinstance(data, dict):
        total = int((data.get("meta") or {}).get("total") or len(results))
    return {
        "ok": True,
        "jobs": jobs,
        "hits": len(jobs),
        "total_available": total,
        "query": pack.freehire_q,
        "pack_id": pack.id,
        "label": pack.label,
        "approach": pack.approach,
    }


def _normalize_hit(hit: dict[str, Any], pack: QueryPack) -> dict[str, Any]:
    slug = str(hit.get("id") or "").strip()
    url = str(hit.get("url") or "").strip()
    if not url and slug:
        url = f"https://freehire.me/jobs/{slug}"
    countries = hit.get("countries") or []
    country = ""
    if isinstance(countries, list) and countries:
        code = str(countries[0]).lower()
        country = _ISO_NAME.get(code, code.upper())
        # Prefer a non-India code when multi-listed
        for c in countries:
            cl = str(c).lower()
            if cl != "in":
                country = _ISO_NAME.get(cl, cl.upper())
                break
    skills = hit.get("skills") or []
    if isinstance(skills, list):
        skills_s = ", ".join(str(s) for s in skills[:20])
    else:
        skills_s = str(skills)
    desc = str(hit.get("description") or "")
    work = str(hit.get("work_mode") or "remote").lower()
    return {
        "title": str(hit.get("title") or ""),
        "company": str(hit.get("company") or ""),
        "url": url,
        "location": str(hit.get("location") or ""),
        "country": country,
        "workplace": work if work in ("remote", "hybrid", "onsite") else "remote",
        "description": desc[:4000],
        "skills": skills if isinstance(skills, list) else [],
        "skills_str": skills_s,
        "published_date": str(hit.get("date") or "")[:10],
        "source": f"freehire:{pack.id}",
        "portal": "freehire",
        "path": "",
        "sponsorship": {"classification": "unknown", "evidence": []},
        "rank": {"overall": 0.55, "skill_score": 0.6},
        "query_pack": pack.id,
        "approach": pack.approach,
    }
