"""Worldwide client hunter — buyers needing React/Next/TS matching the profile.

Sources (published only, never invent contacts):
- leads_store.json client / freelance / demand rows
- leads_cli discover (radar + client-intent prompt → Google/web adapters inside leads engine)
- Profile skill gate (React / Next / TypeScript / full-stack SaaS)
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

from agent.models.opportunity import OpportunityRecord, make_opportunity_id, now_discovered
from agent.quality.contact_ladder import apply_contact_ladder_to_record, extract_published_phone
from agent.quality.pipeline import apply_quality_gates
from agent.scoring.scores import score_client
from agent.storage.excel_store import ExcelStore

ROOT = Path(__file__).resolve().parents[3]
LEADS_STORE = ROOT / "leads" / "store" / "leads_store.json"
CONFIG = ROOT / "agent" / "config" / "default.yaml"

DEFAULT_PROMPT = (
    "Find clients and businesses in DE/NL/UK/IE/AU/NZ/CA/US/EU/UAE/PK "
    "(and remote-international into those; include New Zealand) that need a React OR "
    "Next.js OR TypeScript OR full-stack SaaS developer (freelance, contract, or project). "
    "Prefer posts/pages with published email or phone. "
    "Exclude India / India-only / Bangalore / Mumbai / Hyderabad roles. "
    "Skip pure full-time job boards."
)

_STACK = (
    "react",
    "next.js",
    "nextjs",
    "typescript",
    "javascript",
    "full stack",
    "fullstack",
    "node.js",
    "nodejs",
    "saas",
    "frontend",
    "front-end",
    "mern",
)

_DEMAND = (
    "need",
    "looking for",
    "hiring",
    "seeking",
    "wanted",
    "require",
    "budget",
    "project",
    "freelance",
    "contract",
    "developer",
    "engineer",
    "build",
    "mvp",
)


def _profile_skills() -> list[str]:
    if not CONFIG.is_file():
        return list(_STACK)
    try:
        import yaml

        data = yaml.safe_load(CONFIG.read_text(encoding="utf-8")) or {}
        skills = (data.get("profile") or {}).get("skills") or []
        return [str(s).casefold() for s in skills] or list(_STACK)
    except Exception:  # noqa: BLE001
        return list(_STACK)


def matches_profile(text: str, skills: list[str] | None = None) -> bool:
    blob = (text or "").casefold()
    skills = skills or _profile_skills()
    # Normalize Next.js variants
    compact = blob.replace(".", "").replace(" ", "")
    hits = 0
    for s in skills:
        key = s.casefold().replace(".", "").replace(" ", "")
        if key and key in compact:
            hits += 1
        elif s.casefold() in blob:
            hits += 1
    for s in _STACK:
        if s.replace(".", "") in compact or s in blob:
            hits += 1
            break
    return hits >= 1


def _is_clientish(lead: dict[str, Any]) -> bool:
    lt = str(lead.get("lead_type") or lead.get("type") or "").lower()
    if lt in ("client", "freelance"):
        return True
    if lt in ("full_time", "job"):
        return False
    blob = " ".join(
        [
            str(lead.get("title") or ""),
            str(lead.get("intent_explanation") or ""),
            str(lead.get("description") or ""),
            str(lead.get("intent") or ""),
        ]
    ).casefold()
    return any(d in blob for d in _DEMAND) and matches_profile(blob)


def _lead_to_client_record(lead: dict[str, Any]) -> OpportunityRecord | None:
    company = str(lead.get("company") or lead.get("company_name") or "").strip()
    title = str(lead.get("title") or lead.get("role") or lead.get("opportunity_title") or "").strip()
    url = str(lead.get("url") or lead.get("source_url") or "").strip()
    if not company or not title:
        return None
    blob = " ".join(
        [
            title,
            str(lead.get("description") or ""),
            str(lead.get("intent_explanation") or ""),
            ", ".join(lead.get("technical_requirements") or [])
            if isinstance(lead.get("technical_requirements"), list)
            else "",
        ]
    )
    if not matches_profile(blob):
        return None

    contacts = lead.get("contacts") if isinstance(lead.get("contacts"), list) else []
    raw = lead.get("raw") if isinstance(lead.get("raw"), dict) else {}
    founders = raw.get("founders") if isinstance(raw.get("founders"), list) else []
    intent = str(lead.get("intent") or "")
    if not intent and any(d in blob.casefold() for d in ("looking for", "need", "hiring", "seeking")):
        intent = "EXPLICIT_DEMAND"

    skills = lead.get("technical_requirements") or lead.get("technologies") or []
    if isinstance(skills, list):
        skills_s = ", ".join(str(s) for s in skills)
    else:
        skills_s = str(skills or "")

    rec = OpportunityRecord(
        id=str(lead.get("id") or make_opportunity_id("client", company, title, url)),
        opportunity_type="client",
        company=company,
        role_or_title=title[:240],
        description=str(lead.get("description") or lead.get("intent_explanation") or "")[:2000],
        required_skills=skills_s,
        country=str(lead.get("country") or ""),
        location=str(lead.get("location") or ""),
        remote_type=str(lead.get("workplace") or "unknown"),
        salary_or_budget=str(lead.get("budget_or_salary") or lead.get("budget") or ""),
        posted_date=str(lead.get("published_date") or lead.get("posted_date") or "")[:10],
        discovered_date=now_discovered(),
        last_verified=date.today().isoformat(),
        source_name=str(lead.get("source") or "client_hunter"),
        source_url=url,
        company_website=str(raw.get("website") or ""),
        intent_classification=intent or "STRONG_SIGNAL",
        evidence=str(lead.get("evidence_summary") or "")[:800],
        status=str(lead.get("status") or "new"),
        next_action="client_outreach_review",
    )
    apply_contact_ladder_to_record(rec, contacts=contacts, founders=founders)
    if not rec.contact_phone:
        rec.contact_phone = extract_published_phone(rec.description, rec.evidence, url)
    return score_client(rec)


def harvest_clients_from_store(*, limit: int = 80) -> list[OpportunityRecord]:
    if not LEADS_STORE.is_file():
        return []
    data = json.loads(LEADS_STORE.read_text(encoding="utf-8"))
    leads = list((data.get("leads") or {}).values())
    out: list[OpportunityRecord] = []
    for lead in leads:
        if not isinstance(lead, dict) or not _is_clientish(lead):
            continue
        rec = _lead_to_client_record(lead)
        if rec:
            out.append(rec)
        if len(out) >= limit:
            break
    return out


def run_leads_cli_client_discover(prompt: str = DEFAULT_PROMPT) -> dict[str, Any]:
    """Trigger leads engine client/radar discovery (web adapters inside leads_cli)."""
    try:
        proc = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools" / "leads_cli.py"),
                "discover",
                "--prompt",
                prompt,
                "--mode",
                "radar",
                "--yes",
                "--format",
                "json",
            ],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=600,
        )
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stderr_tail": (proc.stderr or "")[-800:],
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}


def run_client_discovery(
    store: ExcelStore | None = None,
    *,
    limit: int = 50,
    discover: bool = True,
    prompt: str = "",
) -> dict[str, Any]:
    store = store or ExcelStore()
    store.ensure_workbook()
    prompt = (prompt or "").strip() or DEFAULT_PROMPT
    disc: dict[str, Any] = {}
    if discover:
        disc = run_leads_cli_client_discover(prompt)

    records = harvest_clients_from_store(limit=limit * 3)
    # Prefer rows with any contact path
    records.sort(
        key=lambda r: (
            0 if r.contact_email else 1,
            0 if r.contact_phone else 1,
            0 if r.linkedin_url else 1,
            -float(r.opportunity_score or 0),
        )
    )
    existing = store.load_all_opportunities()
    # Clients: soft path (enforce_path still drops fake-remote / unsponsored onsite)
    gated = apply_quality_gates(
        records,
        existing_rows=existing,
        kill_days=21,
        enforce_path=True,
    )
    # Keep client type only
    kept = [r for r in gated.kept if r.opportunity_type == "client"][:limit]
    result = store.upsert_opportunities(kept, history_summary="client hunter worldwide")
    store.record_source_run(
        "clients",
        success=True,
        new_records=result.get("added", 0),
        duplicates=result.get("updated", 0),
    )
    return {
        "ok": True,
        "discover": disc,
        "fetched": len(records),
        "kept": len(kept),
        "dropped": len(gated.dropped),
        "gate": gated.stats,
        "with_email": sum(1 for r in kept if r.contact_email),
        "with_phone": sum(1 for r in kept if r.contact_phone),
        **result,
    }
