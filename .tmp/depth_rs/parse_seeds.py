import json
import re
from pathlib import Path

from job_scraper.engine.freshness import _norm, load_blocked_companies, load_seen_identities

urls, pairs = load_seen_identities()
blocked = load_blocked_companies()

# extra hard excludes from Depth R text
extra = """
hud clera dualentry profound toggl doctolib manex wypoon retell omnea stratos
borderless nebius faction stream cloover brightflag twenty outset nano
""".split()
blocked |= {_norm(x) for x in extra}

AGENCY = re.compile(
    r"recruit|staffing|agency|talent|consulting|solutions ltd|jobgether|proxify|toptal|lemon",
    re.I,
)


def load_json(path: Path):
    raw = path.read_text(encoding="utf-8-sig")
    i = raw.find("{")
    j = raw.find("[")
    start = min(x for x in (i, j) if x >= 0)
    data = json.loads(raw[start:])
    if isinstance(data, dict):
        return data.get("results") or data.get("jobs") or []
    return data


rows = []
for p in Path(".tmp/depth_rs").glob("li_*.json"):
    try:
        jobs = load_json(p)
    except Exception as e:
        print("fail", p, e)
        continue
    for job in jobs:
        company = (job.get("company") or job.get("companyName") or "").strip()
        title = (job.get("title") or "").strip()
        url = (job.get("url") or job.get("link") or "").strip()
        loc = job.get("location") or ""
        posted = job.get("posted_date") or job.get("postedAt") or job.get("date") or ""
        if not company or not title:
            continue
        c = _norm(company)
        if c in blocked or AGENCY.search(company):
            reason = "blocked/agency"
        elif url.rstrip("/") in urls or (c, _norm(title)) in pairs:
            reason = "seen"
        else:
            reason = "KEEP"
        rows.append(
            {
                "file": p.name,
                "company": company,
                "title": title,
                "url": url,
                "location": loc,
                "posted": posted,
                "reason": reason,
            }
        )

keep = [r for r in rows if r["reason"] == "KEEP"]
print("total", len(rows), "keep", len(keep), "drop", len(rows) - len(keep))
for r in keep:
    print(f"- {r['company']} | {r['title'][:70]}")
    print(f"  {r['location']} | {r['posted']}")
    print(f"  {r['url'][:120]}")

Path(".tmp/depth_rs/seeds_keep.json").write_text(
    json.dumps(keep, indent=2), encoding="utf-8"
)
