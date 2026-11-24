import json
import re
import urllib.request

hdr = {"User-Agent": "Mozilla/5.0"}


def get(url: str) -> str:
    req = urllib.request.Request(url, headers=hdr)
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")


# Discover ATS for promising companies
queries = [
    "https://api.ashbyhq.com/posting-api/job-board/avelios",
    "https://api.ashbyhq.com/posting-api/job-board/anyfin",
    "https://api.ashbyhq.com/posting-api/job-board/truesec",
    "https://boards-api.greenhouse.io/v1/boards/audienceproject/jobs",
    "https://boards-api.greenhouse.io/v1/boards/planday/jobs",
    "https://boards-api.greenhouse.io/v1/boards/economic/jobs",
    "https://boards-api.greenhouse.io/v1/boards/vismaeconomic/jobs",
    "https://boards-api.greenhouse.io/v1/boards/formalize/jobs",
]

for url in queries:
    try:
        raw = get(url)
        data = json.loads(raw)
        jobs = data.get("jobs", data if isinstance(data, list) else [])
        print(url.split("/")[-2] if "boards-api" in url else url.split("/")[-1], "n=", len(jobs) if isinstance(jobs, list) else data)
        if isinstance(jobs, list):
            for j in jobs[:30]:
                t = j.get("title") or ""
                if any(k in t.lower() for k in ("front", "full", "react", "software", "engineer", "product")):
                    print(" -", t, "|", j.get("location") or j.get("absolute_url", "")[:60])
    except Exception as e:
        print(url, "ERR", str(e)[:80])

# Teamtailor Formalize list dates
html = get("https://formalize.teamtailor.com/jobs")
print("formalize tt jobs page")
for href in re.findall(r'href="(https://career\.formalize\.com/jobs/[^"]+)"', html):
    print(" ", href)

# Planday careers
try:
    h = get("https://careers.planday.com")
    print("planday careers", len(h))
    for href, txt in re.findall(r'href="([^"]+)"[^>]*>([^<]{0,100})', h):
        if "engineer" in (txt + href).lower() or "front" in (txt + href).lower():
            print(" ", txt.strip()[:60], href[:100])
except Exception as e:
    print("planday", e)

# Avelios frontend munich - personio?
for url in [
    "https://avelios-medical.jobs.personio.de",
    "https://avelios.jobs.personio.de",
    "https://jobs.ashbyhq.com/avelios",
    "https://job-boards.greenhouse.io/aveliosmedical",
]:
    try:
        h = get(url)
        print(url, "OK", len(h), "visa" in h.lower(), "reloc" in h.lower())
    except Exception as e:
        print(url, str(e)[:60])
