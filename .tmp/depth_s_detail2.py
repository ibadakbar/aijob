import json
import re
import urllib.request

hdr = {"User-Agent": "Mozilla/5.0"}


def get(url: str) -> str:
    req = urllib.request.Request(url, headers=hdr)
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")


def scan(url: str, label: str) -> None:
    print("\n===", label)
    try:
        html = get(url)
    except Exception as e:
        print("ERR", e)
        return
    print(url, "len", len(html))
    low = html.lower()
    for pat in ("visa", "sponsor", "reloc", "work permit", "from anywhere", "worldwide", "react", "typescript", "next.js"):
        if pat in low:
            print(" HIT", pat, low.count(pat))
            i = low.find(pat)
            print(" ", re.sub(r"\s+", " ", html[max(0, i - 60) : i + 140])[:180])


scan(
    "https://career.formalize.com/jobs/8332332-staff-software-engineer-marketplace",
    "Formalize Staff SE",
)

# Greenhouse API style boards
for board, name in [
    ("gleanwork", "Glean"),
    ("buildops", "BuildOps"),
    ("planday", "Planday"),
]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs"
    try:
        data = json.loads(get(url))
        jobs = data.get("jobs", [])
        print(f"\n=== GH API {name} n={len(jobs)}")
        for j in jobs:
            t = j.get("title") or ""
            if any(k in t.lower() for k in ("front", "full stack", "fullstack", "react", "product engineer", "staff software", "senior software")):
                loc = ",".join(x.get("name", "") for x in (j.get("offices") or [])) or j.get("location", {}).get("name")
                print("-", t, "|", loc, "|", j.get("absolute_url"))
    except Exception as e:
        print("GH API", name, e)

# Ashby API buildops
try:
    raw = get("https://api.ashbyhq.com/posting-api/job-board/buildops")
    data = json.loads(raw)
    jobs = data.get("jobs", data if isinstance(data, list) else [])
    print("\n=== Ashby BuildOps", type(jobs), len(jobs) if hasattr(jobs, "__len__") else data.keys())
    for j in jobs[:50] if isinstance(jobs, list) else []:
        t = j.get("title") or ""
        print("-", t, "|", j.get("location"), "|", j.get("jobUrl") or j.get("id"))
except Exception as e:
    print("Ashby buildops", e)

# Cognite contact: LinkedIn company about via search already failed — Tier C OK
# OpenArt founders confirmed
print("\nOpenArt founders: linkedin.com/in/kechunmao , linkedin.com/in/johnqiao0618")
