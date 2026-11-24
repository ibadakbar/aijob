import json, re, pathlib

term = pathlib.Path(
    r"C:\Users\surface\.cursor\projects\d-jobboard-ai-job-search\terminals\4353.txt"
).read_text(encoding="utf-8", errors="replace")
# strip header
body = term.split("---\n", 2)[-1] if term.count("---") >= 2 else term
# find last complete JSON by scanning for { ... }
# Prefer object containing "jobs" or "results" or "eligible"
candidates = []
for m in re.finditer(r"\{", body):
    chunk = body[m.start() :]
    try:
        obj, _ = json.JSONDecoder().raw_decode(chunk)
    except Exception:
        continue
    if isinstance(obj, dict) and any(
        k in obj for k in ("jobs", "results", "eligible", "selected", "new", "kept", "pass", "fail")
    ):
        candidates.append(obj)

print("parsed objects", len(candidates))
if not candidates:
    # fallback: file tee
    t = pathlib.Path(".tmp/board_scrape_all.json").read_text(encoding="utf-8", errors="replace")
    for m in re.finditer(r"\{", t):
        chunk = t[m.start() :]
        try:
            obj, _ = json.JSONDecoder().raw_decode(chunk)
        except Exception:
            continue
        if isinstance(obj, dict) and len(obj) > 2:
            candidates.append(obj)
    print("file parsed", len(candidates))

obj = max(candidates, key=lambda o: len(json.dumps(o))) if candidates else {}
pathlib.Path(".tmp/board_scrape_clean.json").write_text(json.dumps(obj, indent=2)[:500000], encoding="utf-8")
print("keys", list(obj.keys())[:30])
for k, v in obj.items():
    if isinstance(v, list):
        print(f"  {k}: {len(v)}")
    elif isinstance(v, dict):
        print(f"  {k}: dict/{len(v)}")
    else:
        print(f"  {k}: {v!r}"[:100])

jobs = []
for key in ("jobs", "results", "eligible", "selected", "new", "kept", "pass", "candidates"):
    if isinstance(obj.get(key), list):
        jobs = obj[key]
        print("using", key)
        break
if not jobs and isinstance(obj.get("fail"), list):
    print("only fail list", len(obj["fail"]))

for j in jobs[:40]:
    if isinstance(j, dict):
        print(
            "-",
            j.get("company"),
            "|",
            j.get("title"),
            "|",
            (j.get("url") or "")[:100],
            "|",
            j.get("workplace") or j.get("location"),
            "|",
            j.get("path") or j.get("eligibility") or j.get("reason") or j.get("sponsorship"),
        )
