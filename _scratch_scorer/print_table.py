import json
from pathlib import Path

data = json.loads(Path("leads/exports/20261027-182714/leads.json").read_text(encoding="utf-8"))
rows = []
for lead in data["leads"]:
    emails = [
        c
        for c in (lead.get("contacts") or [])
        if c.get("channel_type") == "email" and c.get("value")
    ]
    sc = lead.get("scores") or {}
    rows.append((bool(emails), float(sc.get("overall") or 0), lead, emails))
rows.sort(key=lambda x: (not x[0], -x[1]))

out = Path("_scratch_scorer/table_out.txt")
lines = [
    f"count={len(rows)} with_email={sum(1 for r in rows if r[0])}",
    f"export=leads/exports/20261027-182714",
    "",
]
for i, (has, _ov, lead, emails) in enumerate(rows[:12], 1):
    sc = lead.get("scores") or {}
    elabel = f"yes ({emails[0]['value']}; {emails[0].get('verification_status')})" if emails else "apply URL only"
    lines.append(
        f"{i}\t{lead.get('status')}\t{lead.get('company')}\t{lead.get('title')}\t"
        f"{lead.get('location') or lead.get('country') or ''}\t{elabel}\t"
        f"fit={sc.get('fit_score')}\tall={sc.get('overall')}\t{lead.get('id')}\t{lead.get('url')}"
    )
out.write_text("\n".join(lines), encoding="utf-8")
print(out.read_text(encoding="utf-8"))
