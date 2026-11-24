import json
from pathlib import Path

from job_scraper.engine.freshness import _norm, load_blocked_companies, load_seen_identities

urls, pairs = load_seen_identities()
blocked = load_blocked_companies()


def load(p: str):
    raw = Path(p).read_text(encoding="utf-8-sig")
    start = raw.find("{")
    if start < 0:
        start = raw.find("[")
    data = json.loads(raw[start:])
    if isinstance(data, dict):
        return data.get("results") or data.get("jobs") or []
    return data if isinstance(data, list) else []


cands = []
for src, p in [("remote", ".tmp/freehire_remote.json"), ("eu", ".tmp/freehire_eu.json")]:
    path = Path(p)
    if not path.exists():
        print(f"missing {p}")
        continue
    try:
        jobs = load(p)
    except Exception as exc:
        print(p, exc)
        continue
    for j in jobs:
        company = j.get("company") or j.get("company_name") or ""
        title = j.get("title") or ""
        url = j.get("url") or j.get("apply_url") or j.get("external_url") or ""
        if not url:
            continue
        c = _norm(company)
        if c in blocked:
            continue
        if url.rstrip("/") in urls:
            continue
        if (c, _norm(title)) in pairs:
            continue
        cands.append(
            {
                "source": src,
                "company": company,
                "title": title,
                "url": url,
                "location": j.get("location") or j.get("country"),
                "posted": j.get("posted_at") or j.get("published_at"),
            }
        )

seen = set()
out = []
for x in cands:
    u = x["url"].rstrip("/")
    if u in seen:
        continue
    seen.add(u)
    out.append(x)

print("new candidates", len(out))
for i, x in enumerate(out[:20], 1):
    print(f"{i}. {x['company']} — {x['title']}")
    print("   ", x["url"][:140])
    print("   ", x.get("location"), x.get("posted"))
