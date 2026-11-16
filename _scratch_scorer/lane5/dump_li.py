import json
from pathlib import Path

for p in sorted(Path(".").glob("li_*.json")):
    d = json.loads(p.read_text(encoding="utf-8-sig"))
    rs = d.get("results") or []
    print("===", p.name, "n=", len(rs), "meta", d.get("meta"))
    for j in rs:
        title = (j.get("title") or "")[:100]
        print(f"{j.get('date','')} | {j.get('company','')} | {title}")
        print(" ", j.get("url", ""))
