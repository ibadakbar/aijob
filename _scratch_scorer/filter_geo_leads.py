import json
from pathlib import Path

p = Path("leads/exports/20261027-181806/leads.json")
data = json.loads(p.read_text(encoding="utf-8"))

TARGET_HINTS = (
    "united states",
    "usa",
    "canada",
    "toronto",
    "vancouver",
    "united kingdom",
    "london",
    "edinburgh",
    "manchester",
    "australia",
    "sydney",
    "melbourne",
    "new zealand",
    "auckland",
    "wellington",
    "worldwide",
    "remote",
)
SKIP_URL = (".nl/", ".ch/", ".fr/", "/munich", "/zurich", "/utrecht", "/breda", "/paris", "/berlin")


def is_target(lead: dict) -> bool:
    url = (lead.get("url") or "").lower()
    blob = " ".join(
        [
            lead.get("location") or "",
            lead.get("country") or "",
            lead.get("title") or "",
            url,
        ]
    ).lower()
    if "remotive.com" in url or ".co.uk" in url:
        return True
    if any(s in url for s in SKIP_URL) and "remotive" not in url and ".co.uk" not in url:
        return False
    return any(h in blob for h in TARGET_HINTS)


print("TARGET MATCHES\n")
for lead in data["leads"]:
    if not is_target(lead):
        continue
    sc = lead.get("scores") or {}
    print(
        f"{lead.get('status'):12} fit={sc.get('fit_score', 0):.2f} "
        f"all={sc.get('overall', 0):.2f} | {lead.get('company')} / {lead.get('title')}"
    )
    print(f"  loc={lead.get('location')} country={lead.get('country')}")
    print(f"  id={lead.get('id')}")
    print(f"  {lead.get('url')}\n")

print("SKIPPED (outside US/CA/UK/AU/NZ focus)\n")
for lead in data["leads"]:
    if is_target(lead):
        continue
    print(f"- {lead.get('company')} | {lead.get('location')} | {(lead.get('url') or '')[:70]}")
