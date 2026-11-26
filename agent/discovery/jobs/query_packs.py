"""Rotating intelligent search packs for Ibad's React/Next/TS SaaS profile.

Each pack is a named approach (title-focused, sponsorship language, domain,
seniority, market). The orchestrator rotates packs so every cycle hits a
different angle instead of one legacy scrape.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class QueryPack:
    id: str
    label: str
    approach: str  # title | sponsorship | domain | seniority | market | hybrid
    freehire_q: str
    freehire_extra: dict[str, Any] = field(default_factory=dict)
    jobspy_query: str = ""
    notes: str = ""


# Target ISO countries (no India). freehire --country OR group.
TARGET_COUNTRIES = (
    "DE,NL,GB,IE,US,CA,AU,NZ,SE,DK,FI,NO,BE,CH,CZ,AE,SA,QA,PK,SG"
)

# Shared facet defaults for freehire remote discovery.
_BASE_REMOTE = {
    "remote": "remote",
    "country": TARGET_COUNTRIES,
    "jobage": 14,
    "limit": 15,
}

_BASE_GLOBAL = {
    "remote": "remote",
    "region": "eu,uk,north_america,mena,global",
    "jobage": 10,
    "limit": 12,
}

QUERY_PACKS: list[QueryPack] = [
    # --- Sponsorship / mobility FIRST (Path A/B yield) ---
    QueryPack(
        id="visa_sponsor_react",
        label="Visa sponsorship + React stack",
        approach="sponsorship",
        freehire_q=(
            'React OR Next.js OR TypeScript OR "full stack"'
        ),
        freehire_extra={
            **_BASE_GLOBAL,
            "limit": 20,
            "jobage": 21,
        },
        jobspy_query=(
            'React OR Next.js (TypeScript OR Node) '
            '("visa sponsorship" OR "will sponsor" OR relocation OR "work from anywhere" '
            'OR worldwide OR "hire globally" OR EOR)'
        ),
        notes="Path A/B language first",
    ),
    QueryPack(
        id="worldwide_remote",
        label="Worldwide / from-anywhere remote",
        approach="sponsorship",
        freehire_q='worldwide OR "from anywhere" OR "hire globally" OR EOR OR "visa sponsorship"',
        freehire_extra={
            "remote": "remote",
            "region": "global,eu,uk,north_america,mena",
            "skill": "react,typescript,nextjs",
            "jobage": 21,
            "limit": 18,
        },
        jobspy_query=(
            '(React OR Next.js OR "full stack") '
            '("from anywhere" OR worldwide OR "hire globally" OR "remote international" OR EOR)'
        ),
        notes="Remote-international hire language",
    ),
    QueryPack(
        id="reloc_sponsor_eu",
        label="Relocation / sponsor EU-UK",
        approach="sponsorship",
        freehire_q='relocation OR sponsorship OR "visa sponsor" OR "work permit"',
        freehire_extra={
            "region": "eu,uk",
            "skill": "react,typescript",
            "jobage": 21,
            "limit": 15,
            "seniority": "middle,senior,lead",
        },
        jobspy_query=(
            '(React OR Next.js OR TypeScript) (relocation OR "visa sponsorship" OR "will sponsor") '
            '(Germany OR Netherlands OR Ireland OR "United Kingdom")'
        ),
        notes="Path B onsite/hybrid with sponsor language",
    ),
    # --- Title precision (ATS-friendly titles) ---
    QueryPack(
        id="title_react_next",
        label="Title: React / Next.js / Full-Stack",
        approach="title",
        freehire_q='title:React OR title:Next.js OR title:"Full Stack" OR title:TypeScript',
        freehire_extra={**_BASE_REMOTE, "seniority": "middle,senior,lead", "jobage": 10},
        jobspy_query='title:("React" OR "Next.js" OR "Full Stack") TypeScript remote',
        notes="Core stack titles in target geos",
    ),
    QueryPack(
        id="title_frontend_saas",
        label="Title: Frontend / SaaS Engineer",
        approach="title",
        freehire_q='title:Frontend OR title:"Front End" OR title:"Software Engineer" OR title:SaaS',
        freehire_extra={
            **_BASE_REMOTE,
            "skill": "react,typescript,nextjs",
            "seniority": "middle,senior",
        },
        jobspy_query='"Frontend Engineer" OR "SaaS" React (TypeScript OR Next.js) remote',
        notes="Product/SaaS framing",
    ),
    # --- Domain packs (Ibad strengths) ---
    QueryPack(
        id="domain_saas_dashboards",
        label="SaaS dashboards / analytics",
        approach="domain",
        freehire_q='SaaS OR dashboard OR analytics OR "B2B"',
        freehire_extra={
            **_BASE_REMOTE,
            "skill": "react,typescript",
            "category": "frontend,fullstack",
        },
        jobspy_query='(SaaS OR dashboard OR analytics) (React OR Next.js) TypeScript remote',
        notes="Plai-adjacent product work",
    ),
    QueryPack(
        id="domain_shopify_ecommerce",
        label="Shopify / e-commerce",
        approach="domain",
        freehire_q='Shopify OR Liquid OR ecommerce OR "e-commerce"',
        freehire_extra={
            **_BASE_REMOTE,
            "skill": "react,javascript",
            "limit": 12,
        },
        jobspy_query='(Shopify OR Liquid OR ecommerce) (React OR Next.js OR TypeScript) remote',
        notes="Secondary stack strength",
    ),
    QueryPack(
        id="domain_ai_llm",
        label="AI / LLM product features",
        approach="domain",
        freehire_q='OpenAI OR LLM OR "AI engineer" OR ChatGPT',
        freehire_extra={
            **_BASE_REMOTE,
            "skill": "react,typescript,nodejs",
            "category": "fullstack,ml_ai,frontend",
        },
        jobspy_query='(OpenAI OR LLM OR "AI-powered") (React OR Next.js OR TypeScript) remote',
        notes="AI product engineering angle",
    ),
    # --- Seniority / role variants ---
    QueryPack(
        id="senior_fullstack",
        label="Senior / Lead full-stack",
        approach="seniority",
        freehire_q='title:Senior OR title:Lead OR title:"Staff"',
        freehire_extra={
            **_BASE_REMOTE,
            "skill": "react,typescript,nodejs",
            "category": "fullstack,frontend",
            "seniority": "senior,lead,staff",
        },
        jobspy_query='("Senior" OR Lead) (React OR "Full Stack" OR Next.js) TypeScript remote',
        notes="5+ years framing",
    ),
    QueryPack(
        id="mern_node",
        label="MERN / Node API",
        approach="hybrid",
        freehire_q='Node.js OR Express OR MERN OR MongoDB',
        freehire_extra={
            **_BASE_REMOTE,
            "skill": "nodejs,react,typescript",
            "category": "fullstack,backend",
        },
        jobspy_query='(Node.js OR MERN OR Express) React TypeScript remote',
        notes="Full-stack Node depth",
    ),
    # --- Market-focused ---
    QueryPack(
        id="market_eu_uk",
        label="EU + UK remote React",
        approach="market",
        freehire_q='title:React OR title:Next.js OR title:TypeScript',
        freehire_extra={
            "remote": "remote",
            "region": "eu,uk",
            "jobage": 14,
            "limit": 15,
            "seniority": "middle,senior",
        },
        jobspy_query='React OR Next.js TypeScript remote (Germany OR Netherlands OR "United Kingdom" OR Ireland)',
        notes="Primary EU/UK markets",
    ),
    QueryPack(
        id="market_anz_mena",
        label="AU/NZ + MENA remote",
        approach="market",
        freehire_q='title:React OR title:Next.js OR title:"Full Stack"',
        freehire_extra={
            "remote": "remote",
            "country": "AU,NZ,AE,SA,QA,SG,PK",
            "jobage": 21,
            "limit": 12,
        },
        jobspy_query='React OR Next.js (Australia OR "New Zealand" OR UAE OR Dubai OR Pakistan) remote',
        notes="ANZ + Gulf + PK",
    ),
    QueryPack(
        id="market_na_remote_intl",
        label="US/CA remote-international",
        approach="market",
        freehire_q='title:React OR title:Next.js OR title:TypeScript',
        freehire_extra={
            "remote": "remote",
            "country": "US,CA",
            "jobage": 10,
            "limit": 15,
            "seniority": "middle,senior",
        },
        jobspy_query=(
            'React OR Next.js TypeScript '
            '("work from anywhere" OR worldwide OR "visa sponsorship" OR EOR OR "hire globally")'
        ),
        notes="NA only when overseas/visa language present",
    ),
    # --- Emergency packs (auto-used when dry streak) ---
    QueryPack(
        id="emergency_visa_worldwide",
        label="EMERGENCY: visa + worldwide React",
        approach="sponsorship",
        # freehire allows max 5 OR alternatives
        freehire_q='worldwide OR relocation OR EOR OR "visa sponsorship" OR "from anywhere"',
        freehire_extra={
            "remote": "remote",
            "skill": "react,typescript,nextjs,nodejs",
            "region": "global,eu,uk,north_america,mena,apac",
            "jobage": 30,
            "limit": 25,
        },
        jobspy_query=(
            '(React OR Next.js OR TypeScript) '
            '("visa sponsorship" OR worldwide OR relocation OR "from anywhere" OR EOR)'
        ),
        notes="Widen window when agent finds nothing new",
    ),
    QueryPack(
        id="emergency_path_b_eu",
        label="EMERGENCY: EU Path B sponsor/reloc",
        approach="sponsorship",
        freehire_q='"visa sponsorship" OR relocation OR "will sponsor" OR "work permit"',
        freehire_extra={
            "region": "eu,uk",
            "skill": "react,typescript",
            "jobage": 30,
            "limit": 20,
            "seniority": "middle,senior,lead",
        },
        jobspy_query=(
            '(React OR Next.js) ("visa sponsorship" OR relocation OR "will sponsor") '
            '(Berlin OR Amsterdam OR London OR Dublin OR remote)'
        ),
        notes="Path B push when Path A remote is dry",
    ),
    QueryPack(
        id="emergency_pk_local",
        label="EMERGENCY: Pakistan local React",
        approach="market",
        freehire_q='title:React OR title:Next.js OR title:"Full Stack" OR title:MERN',
        freehire_extra={
            "country": "PK",
            "jobage": 30,
            "limit": 20,
        },
        jobspy_query='React OR Next.js OR MERN (Karachi OR Lahore OR Islamabad OR Pakistan)',
        notes="PK path exception when international dry",
    ),
]


SPONSORSHIP_PACK_IDS = {
    p.id for p in QUERY_PACKS if p.approach == "sponsorship"
}
EMERGENCY_PACK_IDS = {
    "emergency_visa_worldwide",
    "emergency_path_b_eu",
    "emergency_pk_local",
}


def pack_by_id(pack_id: str) -> QueryPack | None:
    for p in QUERY_PACKS:
        if p.id == pack_id:
            return p
    return None


def rotate_packs(cursor: int, n: int = 3) -> tuple[list[QueryPack], int]:
    """Return next ``n`` packs and the new cursor."""
    if not QUERY_PACKS:
        return [], 0
    out: list[QueryPack] = []
    i = cursor % len(QUERY_PACKS)
    for _ in range(min(n, len(QUERY_PACKS))):
        out.append(QUERY_PACKS[i])
        i = (i + 1) % len(QUERY_PACKS)
    return out, i


def pick_packs_for_dry_streak(
    cursor: int,
    *,
    dry_streak: int,
    pack_stats: dict[str, Any] | None = None,
    base_n: int = 3,
) -> tuple[list[QueryPack], int, str]:
    """Auto-improve pack selection when new listings dry up.

    Returns (packs, new_cursor, mode_label).
    """
    stats = pack_stats or {}
    if dry_streak <= 0:
        packs, nxt = rotate_packs(cursor, n=base_n)
        return packs, nxt, "rotate"

    # Prefer sponsorship / emergency packs; also boost historically high-hit packs
    n = min(len(QUERY_PACKS), base_n + min(dry_streak, 3))
    preferred: list[QueryPack] = []
    seen: set[str] = set()

    # 1) Emergency packs first when streak >= 2
    if dry_streak >= 2:
        for pid in (
            "emergency_visa_worldwide",
            "emergency_path_b_eu",
            "emergency_pk_local",
            "worldwide_remote",
            "visa_sponsor_react",
            "reloc_sponsor_eu",
        ):
            p = pack_by_id(pid)
            if p and p.id not in seen:
                preferred.append(p)
                seen.add(p.id)

    # 2) Best hit-rate packs from history
    ranked = sorted(
        ((pid, st) for pid, st in stats.items() if isinstance(st, dict)),
        key=lambda x: (int(x[1].get("kept") or 0), int(x[1].get("hits") or 0)),
        reverse=True,
    )
    for pid, _st in ranked:
        p = pack_by_id(pid)
        if p and p.id not in seen:
            preferred.append(p)
            seen.add(p.id)
        if len(preferred) >= n:
            break

    # 3) Fill with normal rotation
    rotated, nxt = rotate_packs(cursor, n=n)
    for p in rotated:
        if p.id not in seen:
            preferred.append(p)
            seen.add(p.id)
        if len(preferred) >= n:
            break

    mode = f"dry_escalate_{dry_streak}"
    return preferred[:n], nxt, mode
