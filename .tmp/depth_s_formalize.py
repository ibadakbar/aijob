import re
import urllib.request

hdr = {"User-Agent": "Mozilla/5.0"}
url = "https://career.formalize.com/jobs/8332332-staff-software-engineer-marketplace"
html = urllib.request.urlopen(urllib.request.Request(url, headers=hdr), timeout=30).read().decode(
    "utf-8", "replace"
)
# unescape a bit
text = (
    html.replace("\\u003c", "<")
    .replace("\\u003e", ">")
    .replace("\\u0026", "&")
    .replace("\\/", "/")
)
text = re.sub(r"<[^>]+>", " ", text)
text = re.sub(r"\s+", " ", text)
low = text.lower()
for kw in (
    "react",
    "typescript",
    "next",
    "frontend",
    "full-stack",
    "fullstack",
    "node",
    "python",
    "java",
    "kotlin",
    "visa",
    "copenhagen",
    "office",
):
    print(kw, low.count(kw))

# date patterns
for m in re.findall(r"(20\d{2}-\d{2}-\d{2}|posted[^.]{0,40}|published[^.]{0,40})", low)[:20]:
    print("DATEISH", m)

# print window around responsibilities
i = low.find("staff software")
print(text[i : i + 2500] if i >= 0 else text[2000:4500])

# founder search pages
for u in [
    "https://formalize.com/about",
    "https://www.formalize.com/about",
    "https://career.formalize.com",
]:
    try:
        h = urllib.request.urlopen(urllib.request.Request(u, headers=hdr), timeout=20).read().decode(
            "utf-8", "replace"
        )
        print("\nPAGE", u, len(h))
        for m in re.findall(r"linkedin.com/in/[A-Za-z0-9_-]+", h):
            print(" LI", m)
        for m in re.findall(r"(careers|jobs|hiring|hello|join|talent)@[A-Za-z0-9.-]+", h, re.I):
            print(" EM", m)
    except Exception as e:
        print(u, e)
