import json
from datetime import date
from pathlib import Path
import subprocess
import sys

TMP = Path(__file__).resolve().parent
ROOT = TMP.parent

p = TMP / "dg_visa.json"
print("visa exists", p.exists(), "size", p.stat().st_size if p.exists() else 0)
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    jobs = d if isinstance(d, list) else d.get("results") or []
    print("n", len(jobs))
    for j in jobs:
        t = (j.get("title") or "").lower()
        if any(k in t for k in ["react", "next", "front", "full", "typescript", "node"]):
            print(
                j.get("path"),
                j.get("company"),
                j.get("title"),
                (j.get("sponsorship") or {}).get("classification"),
                (j.get("url") or "")[:70],
            )

today = date.today().isoformat()
rows = [
    {
        "title": "Full-Stack Developer",
        "company": "Carman",
        "url": "https://carman.world/en/careers/fullstack",
        "location": "Remote (Worldwide)",
        "posted_date": None,
        "deadline": None,
        "fit": "high",
        "status": "new",
        "portal": "employer-careers",
        "source": "websearch",
        "first_seen": today,
    },
    {
        "title": "Frontend engineer (Next.js)",
        "company": "WN Social",
        "url": "https://wnsocial.com/careers",
        "location": "Remote · Worldwide",
        "posted_date": None,
        "deadline": None,
        "fit": "high",
        "status": "new",
        "portal": "employer-careers",
        "source": "websearch",
        "first_seen": today,
    },
    {
        "title": "Senior Frontend Engineer",
        "company": "PancakeSwap",
        "url": "https://docs.pancakeswap.finance/welcome-to-pancakeswap/about-us/team/become-a-chef/frontend-engineer",
        "location": "Remote (any timezone)",
        "posted_date": None,
        "deadline": None,
        "fit": "medium",
        "status": "new",
        "portal": "employer-careers",
        "source": "websearch",
        "first_seen": today,
    },
]
store = TMP / "dg_store.json"
store.write_text(json.dumps(rows, indent=2), encoding="utf-8")
r = subprocess.run(
    [sys.executable, "tools/scrape_state.py", "store", "--results", str(store)],
    cwd=ROOT,
    capture_output=True,
    text=True,
)
print(r.stdout)
print(r.stderr, file=sys.stderr)
raise SystemExit(r.returncode)
