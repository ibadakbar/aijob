import re
import urllib.request

hdr = {"User-Agent": "Mozilla/5.0"}


def get(url: str) -> str:
    req = urllib.request.Request(url, headers=hdr)
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")


html = get("https://careers.trackunit.com")
print("trackunit len", len(html))
low = html.lower()
for pat in ["frontend", "visa", "reloc", "sponsor", "react", "typescript"]:
    print(pat, low.count(pat))
for href, txt in re.findall(r'href="([^"]+)"[^>]*>([^<]{0,100})', html):
    blob = (txt + " " + href).lower()
    if any(k in blob for k in ("front", "react", "full-stack", "fullstack", "software engineer")):
        print("JOB", txt.strip()[:70], "->", href[:120])

html2 = get("https://job-boards.greenhouse.io/gleanwork")
print("glean len", len(html2))
for href, txt in re.findall(r'href="([^"]+)"[^>]*>([^<]{0,120})', html2):
    if any(k in (txt + href).lower() for k in ("front", "full stack", "fullstack", "react", "product engineer")):
        print("GLEAN", txt.strip()[:80], "->", href[:120])

# Formalize / Planday / AudienceProject via teamtailor or personio guesses
for url in [
    "https://formalize.teamtailor.com/jobs",
    "https://planday.teamtailor.com/jobs",
    "https://careers.planday.com",
    "https://jobs.ashbyhq.com/glean",
    "https://boards.greenhouse.io/buildops",
    "https://job-boards.greenhouse.io/buildops",
    "https://jobs.ashbyhq.com/buildops",
    "https://jobs.lever.co/buildops",
]:
    try:
        h = get(url)
        print(url, "OK", len(h))
        if "visa" in h.lower() or "reloc" in h.lower():
            print("  has visa/reloc keyword")
        for href, txt in re.findall(r'href="([^"]+)"[^>]*>([^<]{0,100})', h)[:200]:
            if any(k in (txt + href).lower() for k in ("front", "full stack", "fullstack", "react", "software engineer")):
                print(" ", txt.strip()[:60], "->", href[:100])
    except Exception as e:
        print(url, "ERR", e)
