import urllib.request, json, re, html

jid = "e6924f60-c8cc-42b3-9d05-2442ec30e12d"
req = urllib.request.Request(
    "https://api.ashbyhq.com/posting-api/job-board/elevenlabs",
    headers={"User-Agent": "Mozilla/5.0"},
)
j = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())
job = next(x for x in j["jobs"] if x.get("id") == jid)
desc = job.get("descriptionPlain") or re.sub("<[^>]+>", " ", job.get("descriptionHtml") or "")
desc = html.unescape(desc)
# print last 1500 chars (usually location)
print(desc[-1800:])
print("--- React/TS ---")
for needle in ["React", "TypeScript", "Python", "frontend"]:
    print(needle, needle.lower() in desc.lower())
