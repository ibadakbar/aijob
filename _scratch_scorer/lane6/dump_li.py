import json
from pathlib import Path

for p in sorted(Path(".").glob("li_*.json")):
    raw = p.read_text(encoding="utf-8-sig").strip()
    if not raw:
        print(p.name, "EMPTY")
        continue
    d = json.loads(raw)
    rs = d.get("results") or []
    print("===", p.name, "n=", len(rs))
    for j in rs:
        title = (j.get("title") or "")[:95]
        print(f"{j.get('date','')} | {j.get('company','')} | {title}")
        print(" ", j.get("url", ""))
