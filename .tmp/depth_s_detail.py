import re
import urllib.request

hdr = {"User-Agent": "Mozilla/5.0"}


def get(url: str) -> str:
    req = urllib.request.Request(url, headers=hdr)
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")


def scan(url: str, label: str) -> None:
    print("\n===", label, url)
    try:
        html = get(url)
    except Exception as e:
        print("ERR", e)
        return
    print("len", len(html))
    low = html.lower()
    for pat in [
        "visa",
        "sponsor",
        "reloc",
        "work permit",
        "from anywhere",
        "worldwide",
        "eor",
        "react",
        "typescript",
        "next.js",
        "german",
        "danish",
        "norwegian",
        "dutch",
    ]:
        if pat in low:
            print(" HIT", pat, "count", low.count(pat))
    # show snippets around visa/reloc
    for pat in ("visa", "reloc", "sponsor", "work permit", "from anywhere"):
        i = low.find(pat)
        if i >= 0:
            print(" SNIP", pat, ":", re.sub(r"\s+", " ", html[max(0, i - 80) : i + 120])[:200])


scan(
    "https://careers.trackunit.com/jobs/8614980-frontend-software-engineer",
    "Trackunit FE",
)

# Formalize jobs list
html = get("https://formalize.teamtailor.com/jobs")
print("\n=== Formalize jobs")
for href, txt in re.findall(r'href="([^"]+)"[^>]*>([^<]{0,120})', html):
    if any(k in (txt + href).lower() for k in ("software", "front", "full", "engineer", "stack")):
        print(txt.strip()[:70], "->", href[:120])

# BuildOps list FE/FS
html = get("https://job-boards.greenhouse.io/buildops")
print("\n=== BuildOps GH")
for href, txt in re.findall(r'href="([^"]+)"[^>]*>([^<]{0,120})', html):
    t = txt.strip()
    if t and any(k in t.lower() for k in ("front", "full", "react", "staff software", "software engineer")):
        print(t[:80], "->", href[:120])

# Glean FE
html = get("https://job-boards.greenhouse.io/gleanwork")
print("\n=== Glean")
for href, txt in re.findall(r'href="([^"]+)"[^>]*>([^<]{0,120})', html):
    t = txt.strip()
    if t and any(k in t.lower() for k in ("front", "full stack", "fullstack", "product engineer")):
        print(t[:80], "->", href[:120])

# Ashby buildops jobs
html = get("https://jobs.ashbyhq.com/buildops")
print("\n=== BuildOps Ashby len", len(html))
for m in re.findall(r'"title"\s*:\s*"([^"]+)"', html)[:40]:
    if any(k in m.lower() for k in ("front", "full", "react", "software", "product")):
        print(" ", m)
