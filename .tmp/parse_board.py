import json, re, pathlib

t = pathlib.Path(".tmp/board_scrape_all.json").read_text(encoding="utf-8", errors="replace")
# Drop PowerShell error stream lines
clean = []
for line in t.splitlines():
    if line.startswith("python :") or "CategoryInfo" in line or "FullyQualified" in line:
        continue
    if line.strip().startswith("At line:") or line.strip().startswith("+"):
        continue
    clean.append(line)
raw = "\n".join(clean)
i = raw.find("{")
raw = raw[i:]
obj = json.loads(raw)
pathlib.Path(".tmp/board_scrape_clean.json").write_text(json.dumps(obj, indent=2), encoding="utf-8")
print("top keys:", list(obj.keys()))
for k, v in obj.items():
    if isinstance(v, list):
        print(f"{k}: {len(v)}")
    elif isinstance(v, dict):
        print(f"{k}: dict {list(v.keys())[:12]}")
    else:
        print(f"{k}: {v!r}"[:120])

jobs = obj.get("jobs") or obj.get("results") or obj.get("selected") or []
if isinstance(obj.get("data"), list):
    jobs = obj["data"]
# nested
for key in ("pass", "fail", "new", "kept", "eligible", "candidates", "dropped"):
    if key in obj and isinstance(obj[key], list):
        print(f"list {key}: {len(obj[key])}")
        jobs = jobs or obj[key]

print("--- sample ---")
for j in (jobs or [])[:25]:
    if not isinstance(j, dict):
        print(j)
        continue
    print(
        "-",
        j.get("company"),
        "|",
        j.get("title"),
        "|",
        j.get("workplace") or j.get("location"),
        "|",
        (j.get("url") or "")[:90],
        "|",
        j.get("path") or j.get("eligibility") or j.get("sponsorship"),
    )
