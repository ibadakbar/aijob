import urllib.request, re

urls = [
    "https://bolt.eu/en/careers/locations/berlin/",
    "https://bolt.eu/en/careers/positions/afa5be27-7c54-4f88-bfc1-efebdf465920/",
]
for u in urls:
    req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
    try:
        html = urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "replace")
    except Exception as e:
        print("ERR", u, e)
        continue
    text = re.sub(r"<script[\s\S]*?</script>", " ", html)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    print("===", u, "len", len(text))
    for needle in ["visa", "reloc", "immigration", "residence", "React", "TypeScript", "Node"]:
        print(needle, needle.lower() in text.lower())
    for m in re.finditer(
        r".{0,50}(visa|residence permit|relocation|React|TypeScript).{0,90}",
        text,
        re.I,
    ):
        print("Q:", m.group(0)[:200])
