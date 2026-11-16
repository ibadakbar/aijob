import json
import re
from pathlib import Path

TARGET = (
    "united states", "usa", "canada", "uk", "united kingdom", "london", "edinburgh",
    "australia", "sydney", "melbourne", "new zealand", "auckland", "germany", "berlin",
    "munich", "europe", "remote", "worldwide", "eu",
)

SKIP_ONLY = ()  # user asked for Europe/Germany — keep EU hosts


def emails_of(lead):
    out = []
    for c in lead.get("contacts") or []:
        if c.get("channel_type") == "email" and c.get("value"):
            out.append(
                {
                    "value": c["value"],
                    "status": c.get("verification_status"),
                }
            )
    return out


def geo_ok(lead):
    blob = " ".join(
        [
            lead.get("location") or "",
            lead.get("country") or "",
            lead.get("title") or "",
            lead.get("url") or "",
        ]
    ).lower()
    return any(t in blob for t in TARGET) or "remotive.com" in blob or any(
        x in (lead.get("url") or "").lower()
        for x in (".co.uk", ".de/", ".com/", "arbeitnow")
    )


def load(path):
    text = Path(path).read_text(encoding="utf-8-sig", errors="replace")
    # CLI may print non-json lines; find first {
    i = text.find("{")
    if i < 0:
        return {"results": [], "meta": {"error": "no json", "raw": text[:500]}}
    return json.loads(text[i:])


jobs = load("_scratch_scorer/jobs_run.json")
agency = load("_scratch_scorer/agency_run.json")

print("JOBS META")
print(json.dumps({k: jobs.get("meta", {}).get(k) for k in ("returned", "qualified", "review_queue", "export", "errors", "run_id")}, indent=2))
print("AGENCY META")
print(json.dumps({k: agency.get("meta", {}).get(k) for k in ("returned", "qualified", "review_queue", "export", "errors", "run_id")}, indent=2))

rows = []
for src, payload in (("jobs", jobs), ("agency", agency)):
    for lead in payload.get("results") or []:
        if not geo_ok(lead):
            continue
        em = emails_of(lead)
        sc = lead.get("scores") or {}
        rows.append(
            {
                "src": src,
                "company": lead.get("company"),
                "title": lead.get("title"),
                "geo": lead.get("location") or lead.get("country") or "",
                "email": em[0]["value"] if em else "",
                "email_status": em[0]["status"] if em else "apply URL only",
                "status": lead.get("status"),
                "fit": sc.get("fit_score"),
                "overall": sc.get("overall"),
                "id": lead.get("id"),
                "url": lead.get("url"),
                "has_email": bool(em),
            }
        )

# Prefer email rows first, then overall score
rows.sort(key=lambda r: (not r["has_email"], -(r["overall"] or 0)))

print("\nTABLE")
for i, r in enumerate(rows[:12], 1):
    email_label = f"yes ({r['email']})" if r["has_email"] else "apply URL only"
    print(f"{i}. [{r['status']}] {r['company']} / {r['title']}")
    print(f"   geo={r['geo']} | Email? {email_label} | fit={r['fit']} all={r['overall']}")
    print(f"   id={r['id']}")
    print(f"   {r['url']}")

with_email = [r for r in rows if r["has_email"]]
print(f"\nWith published email: {len(with_email)} / {len(rows)} in-geo rows")
if jobs.get("meta", {}).get("export"):
    print("Jobs export:", jobs["meta"]["export"].get("dir"))
if agency.get("meta", {}).get("export"):
    print("Agency export:", agency["meta"]["export"].get("dir"))
