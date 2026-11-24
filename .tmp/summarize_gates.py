import json

for name in ("gate_board.json", "gate_manual.json"):
    o = json.load(open(f".tmp/{name}", encoding="utf-8-sig"))
    print("====", name, "====")
    print(
        "selected",
        len(o.get("selected") or []),
        "seen",
        o.get("already_seen"),
        "applied",
        o.get("already_applied"),
    )
    for j in o.get("selected") or []:
        print(
            "-",
            j.get("company"),
            "|",
            j.get("title"),
            "|",
            (j.get("url") or "")[:110],
            "|",
            j.get("path") or (j.get("raw") or {}).get("path"),
        )
