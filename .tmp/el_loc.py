import urllib.request, json, re, html

ids = {
    "e4e0450f-d139-4f8e-b210-2f326a680d90": "Payments",
    "ce3d5a59-fb8c-482b-bc3f-60e44576c5e0": "Platform",
    "0547cf3a-856f-4db2-8307-73db634c4096": "ElevenMusic",
    "e6924f60-c8cc-42b3-9d05-2442ec30e12d": "Studio FE",
}
req = urllib.request.Request(
    "https://api.ashbyhq.com/posting-api/job-board/elevenlabs",
    headers={"User-Agent": "Mozilla/5.0"},
)
j = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())
by_id = {job.get("id"): job for job in j["jobs"]}
for jid, label in ids.items():
    job = by_id.get(jid)
    if not job:
        print("MISSING", label, jid)
        continue
    desc = job.get("descriptionPlain") or ""
    if not desc:
        desc = re.sub("<[^>]+>", " ", job.get("descriptionHtml") or "")
    desc = html.unescape(desc)
    print("====", label, job.get("title"))
    print("URL", job.get("jobUrl"))
    # location section snippets
    for m in re.finditer(
        r".{0,40}(Location|remote|globally|anywhere|worldwide|Europe|US|timezone|visa).{0,120}",
        desc,
        re.I,
    ):
        print(" ", " ".join(m.group(0).split())[:200])
