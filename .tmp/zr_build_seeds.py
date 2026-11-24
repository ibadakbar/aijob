"""Build ≤30 Zero-Repeat seeds from LI JSON + owned ATS; write candidates JSON."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TMP = ROOT / ".tmp"

HARD = {
    x.lower()
    for x in """
Railway VitVio Peec ElevenLabs Bolt Swisscom Supabase Zalando EY Gray Swan AMBOSS ELITEBRAIN
Dex TalentHop Jobgether Seamflow Omnea STRATOS Picnic Optiver BairesDev Lemon Proxify Silver
Tailor Toggl HUD Reflection Fluence ClickHouse Cloover Doctolib Swap Zoopla Trainline Mytos
Rulemapping Fortus Teero Apata SOUS Redcare Discord Wheely Faction Stream Profound Midnite
Animore Impower OneLab Epidemic n8n Ruya Pearl Hire Hangar Naphora Clera Conduct Fuse Air Apps
Outset Personio Hawk Emma Helsing Ubiquiti Scaleway JUXT Akeno Owen Thomas Kindred Maze Wayflyer
""".split()
}

AGENCY = (
    "recruit",
    "talent",
    "searchability",
    "client server",
    "hunter bond",
    "computer futures",
    "cpl",
    "fruition",
    "oliver",
    "adamantine",
    "wave talent",
    "hyrup",
    "mlabs",
    "presidio",
    "realtime",
    "infinity",
    "talentmate",
    "tenth revolution",
    "harvey nash",
    "huxley",
    "sr2",
    "trust in soda",
)

# Owned ATS / employer careers only (real Apply URLs)
ATS = [
    {
        "title": "Full Stack Software Engineer — AI & Automation",
        "company": "Utility Profit",
        "url": "https://job-boards.greenhouse.io/utilityprofit/jobs/4412541009",
        "location": "Remote — Worldwide",
        "date": None,
        "portal": "greenhouse",
        "source": "websearch",
    },
    {
        "title": "Software Engineer (TypeScript/JavaScript)",
        "company": "Databento",
        "url": "https://job-boards.greenhouse.io/databento/jobs/8076835",
        "location": "Remote / Boston / SLC / SF / NY",
        "date": None,
        "portal": "greenhouse",
        "source": "websearch",
    },
    {
        "title": "Senior Frontend Engineer",
        "company": "StackAI",
        "url": "https://jobs.ashbyhq.com/stack-ai/f15559d9-4c4f-4e95-bdf5-786376d93f04",
        "location": "Spain (Remote)",
        "date": None,
        "portal": "ashby",
        "source": "websearch",
    },
    {
        "title": "Senior / Lead Full Stack Engineer (TypeScript + React)",
        "company": "Solvd",
        "url": "https://jobs.ashbyhq.com/solvd/83e49175-52a2-4639-963a-f25f47f46514",
        "location": "Argentina / Poland / Brazil / Georgia / Colombia",
        "date": None,
        "portal": "ashby",
        "source": "websearch",
    },
    {
        "title": "Senior Fullstack Engineer",
        "company": "Siena AI",
        "url": "https://jobs.ashbyhq.com/siena/91e5e63a-7b02-4176-8b8f-0747042d756f",
        "location": "Remote - Europe (+ listed countries)",
        "date": None,
        "portal": "ashby",
        "source": "websearch",
    },
    {
        "title": "Full Stack Software Engineer",
        "company": "Fortaegis Technologies",
        "url": "https://fortaegis.teamtailor.com/jobs/8626786-full-stack-software-engineer",
        "location": "Amsterdam (Onsite)",
        "date": None,
        "portal": "teamtailor",
        "source": "websearch",
    },
    {
        "title": "Forward Deployed Engineer",
        "company": "Staffbase",
        "url": "https://job-boards.greenhouse.io/staffbase/jobs/8869895002",
        "location": "Berlin / Chemnitz / Dresden",
        "date": "2026-10-06",
        "portal": "greenhouse",
        "source": "websearch",
    },
    {
        "title": "Software Engineer (FE+ Full Stack)",
        "company": "Wiley",
        "url": "https://wiley.wd1.myworkdayjobs.com/en-US/wiley_careers/job/Software-Engineer--FE--Full-Stack-_R2601157",
        "location": "Amman, Jordan",
        "date": "2026-11-18",
        "portal": "workday",
        "source": "websearch",
    },
]


def hard_hit(company: str) -> bool:
    c = company.lower()
    return any(h in c for h in HARD)


def agency_hit(company: str) -> bool:
    c = company.lower()
    return any(a in c for a in AGENCY)


def load_li(path: Path) -> list[dict]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    jobs = data.get("results") or []
    out = []
    for j in jobs:
        if not isinstance(j, dict):
            continue
        co = (j.get("company") or "").strip()
        title = (j.get("title") or "").strip()
        url = (j.get("url") or "").strip()
        if not co or not title or not url:
            continue
        out.append(
            {
                "title": title,
                "company": co,
                "url": url,
                "location": j.get("location") or "",
                "date": j.get("date") or j.get("listedAt") or None,
                "portal": "linkedin-search",
                "source": "cli",
            }
        )
    return out


def main() -> None:
    files = [
        "zr_pa1.json",
        "zr_pa3.json",
        "zr_pa_pe.json",
        "zr_pb_lon.json",
        "zr_pb_ber.json",
        "zr_pb_ams.json",
    ]
    seeds: list[dict] = []
    seen_keys: set[tuple[str, str]] = set()
    dropped_hard = dropped_agency = dropped_dup = dropped_noise = 0

    # Prefer ATS first so they survive the ≤30 cap
    for row in ATS:
        key = (row["company"].lower(), row["title"].lower())
        if key in seen_keys or hard_hit(row["company"]):
            continue
        seen_keys.add(key)
        seeds.append(row)

    # LI seeds: keep React/TS/frontend/fullstack engineer titles only
    KEEP = (
        "react",
        "typescript",
        "frontend",
        "front-end",
        "front end",
        "full stack",
        "fullstack",
        "full-stack",
        "software engineer",
        "product engineer",
        "design engineer",
        "nodejs",
        "node.js",
        "next.js",
        "nextjs",
    )
    DROP_TITLE = (
        "product manager",
        "support",
        "accountant",
        "debt",
        "media buyer",
        "sales",
        "quality engineer",
        "associ",
    )

    for name in files:
        for row in load_li(TMP / name):
            key = (row["company"].lower(), row["title"].lower())
            if key in seen_keys:
                dropped_dup += 1
                continue
            if hard_hit(row["company"]):
                dropped_hard += 1
                continue
            if agency_hit(row["company"]):
                dropped_agency += 1
                continue
            t = row["title"].lower()
            if any(d in t for d in DROP_TITLE):
                dropped_noise += 1
                continue
            if not any(k in t for k in KEEP):
                dropped_noise += 1
                continue
            seen_keys.add(key)
            seeds.append(row)

    seeds = seeds[:30]
    out = TMP / "zr_seeds.json"
    out.write_text(json.dumps(seeds, indent=2), encoding="utf-8")
    meta = {
        "seed_count": len(seeds),
        "dropped_hard": dropped_hard,
        "dropped_agency": dropped_agency,
        "dropped_dup": dropped_dup,
        "dropped_noise": dropped_noise,
        "companies": [s["company"] for s in seeds],
    }
    (TMP / "zr_seeds_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
