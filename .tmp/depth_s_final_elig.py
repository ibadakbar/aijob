import json
import re
import urllib.request

hdr = {"User-Agent": "Mozilla/5.0"}


def get(url: str) -> str:
    req = urllib.request.Request(url, headers=hdr)
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")


# BuildOps Toronto Staff via GH API job id 5754105004
for jid, name in [("5754105004", "BuildOps Staff TOR"), ("6147598004", "BuildOps Sr TOR")]:
    try:
        data = json.loads(get(f"https://boards-api.greenhouse.io/v1/boards/buildops/jobs/{jid}"))
        content = data.get("content") or ""
        print(name, "updated", data.get("updated_at"))
        low = content.lower()
        print(" visa", "visa" in low, "reloc", "reloc" in low, "sponsor", "sponsor" in low, "react", "react" in low)
        for m in re.finditer(r".{0,50}(visa|sponsor|reloc).{0,80}", content, re.I):
            print(" ", re.sub("<[^>]+>", " ", m.group(0))[:160])
    except Exception as e:
        print(name, e)

# River greenhouse job date
try:
    data = json.loads(get("https://boards-api.greenhouse.io/v1/boards/riverai/jobs/4250000009"))
    print("River updated", data.get("updated_at"), "title", data.get("title"))
    c = (data.get("content") or "").lower()
    print(" visa", "visa" in c, "reloc", "reloc" in c)
except Exception as e:
    print("River", e)

# OpenArt ashby - check published if in HTML
html = get("https://jobs.ashbyhq.com/openart/0fc06a39-65de-41ed-ac7f-e21f311989ad")
for pat in ("published", "datePosted", "2026-"):
    print("openart", pat, html.lower().count(pat.lower()))
m = re.search(r'"publishedAt"\s*:\s*"([^"]+)"', html)
print("publishedAt", m.group(1) if m else None)
m = re.search(r'"publicationDate"\s*:\s*"([^"]+)"', html)
print("publicationDate", m.group(1) if m else None)

# Cognite GH API
try:
    # eu board?
    for board in ("cognite", "cognitedata"):
        try:
            data = json.loads(get(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs/5037088101"))
            print("Cognite board", board, data.get("updated_at"), "title", data.get("title"))
            break
        except Exception as e:
            print("board", board, e)
except Exception as e:
    print(e)
