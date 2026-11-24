import urllib.request, json
from datetime import datetime, timezone, timedelta

req = urllib.request.Request(
    "https://api.ashbyhq.com/posting-api/job-board/elevenlabs",
    headers={"User-Agent": "Mozilla/5.0"},
)
j = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())
cut = datetime.now(timezone.utc) - timedelta(days=7)
cut14 = datetime.now(timezone.utc) - timedelta(days=14)
rows = []
for job in j["jobs"]:
    t = job.get("title", "")
    if not any(
        k in t.lower()
        for k in ["full-stack", "fullstack", "frontend", "front-end", "product engineer"]
    ):
        continue
    pub = job.get("publishedAt") or ""
    try:
        dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
    except Exception:
        dt = None
    rows.append((dt, t, job.get("location"), job.get("jobUrl"), pub[:19], job.get("id")))
rows.sort(key=lambda x: x[0] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
for dt, t, loc, url, pub, jid in rows[:30]:
    f7 = bool(dt and dt >= cut)
    f14 = bool(dt and dt >= cut14)
    print(f7, f14, pub, "|", t, "|", loc, "|", jid)
    print(" ", url)
