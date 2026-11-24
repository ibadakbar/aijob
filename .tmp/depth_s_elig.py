import json
import re
import urllib.request

hdr = {"User-Agent": "Mozilla/5.0"}


def get(url: str) -> str:
    req = urllib.request.Request(url, headers=hdr)
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")


def scan(url: str, label: str) -> None:
    print("\n===", label)
    html = get(url)
    print(url, "len", len(html))
    low = html.lower()
    for pat in (
        "visa",
        "sponsor",
        "reloc",
        "work permit",
        "from anywhere",
        "worldwide",
        "react",
        "typescript",
        "next.js",
        "danish",
        "german",
        "posted",
        "published",
    ):
        if pat in low:
            print(" HIT", pat, low.count(pat))
    for pat in ("visa", "reloc", "sponsor", "react", "typescript"):
        i = low.find(pat)
        if i >= 0:
            print(" SNIP", pat, ":", re.sub(r"\s+", " ", html[max(0, i - 100) : i + 160])[:220])


scan(
    "https://career.formalize.com/jobs/8332332-staff-software-engineer-marketplace",
    "Formalize",
)
scan(
    "https://job-boards.greenhouse.io/gleanwork/jobs/4006733005",
    "Glean FE",
)
scan(
    "https://jobs.ashbyhq.com/buildops/c0230e3b-d9fb-4dd2-a76c-5bb249e38f9f",
    "BuildOps Staff Toronto Ashby",
)
scan(
    "https://job-boards.greenhouse.io/gleanwork/jobs/4006734005",
    "Glean Fullstack",
)

# Formalize contact
for url in [
    "https://formalize.com/contact",
    "https://www.formalize.com/contact",
    "https://career.formalize.com",
    "https://formalize.com",
]:
    try:
        h = get(url)
        emails = sorted(set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", h)))
        emails = [e for e in emails if not e.endswith(("png", "jpg", "svg", "webp"))]
        print(url, "emails", emails[:15])
    except Exception as e:
        print(url, e)

# Greenhouse job detail API for dates
for jid, name in [("4006733005", "Glean FE"), ("4006734005", "Glean FS")]:
    try:
        data = json.loads(get(f"https://boards-api.greenhouse.io/v1/boards/gleanwork/jobs/{jid}"))
        print(name, "updated", data.get("updated_at"), "loc", data.get("location"))
        content = (data.get("content") or "")[:500]
        print(" content has visa", "visa" in content.lower(), "reloc", "reloc" in content.lower())
    except Exception as e:
        print(name, e)
