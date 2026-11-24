"""Filter board_hits + LI seeds for Path A/B eligibility; write candidates JSON."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(r"D:\jobboard\ai-job-search")
hits = json.loads((ROOT / ".tmp" / "board_hits.json").read_text(encoding="utf-8"))

RECYCLE = {
    "fluence", "askable", "lemon.io", "lemon", "strac", "quill", "velt", "salespatriot",
    "karumi", "guac", "besimple", "capix", "legalos", "reframe", "goodpeople", "reflection",
    "grafana", "navvis", "jack", "situ", "trivago", "pixelchain", "clera", "borderpass",
    "canadavisa", "hospo ai", "air apps", "throxy", "vimub", "chatbotkit", "stat sniper",
    "hardihood", "viboa", "nord harton", "shopitecture", "ecommerce smart", "underwaterpistol",
    "swanky", "charle", "niccos", "prosper digital", "refulfil", "clickhouse", "benetics",
    "contentful", "tensorx", "almedia", "signifly", "momo medical", "spiich", "canonical",
    "resquared", "health harbor", "ciro", "doctolib", "templafy", "popl", "owen thomas",
    "primus connect", "hartleyco", "mitre media", "sportsbet", "dept", "presidio",
    "digital melon", "b2dubai", "laine", "serko", "coreflow", "objective corporation",
    "fuse energy", "blinq", "virtual days", "ahoy", "supplios", "dream broker", "entries",
    "taxxa", "rumli", "falschparker", "sajn", "roomstay", "matchspace music",
    "diligencesquared", "runway", "spark ai", "flick", "happyrobot", "item", "clara",
    "dreamcraft", "spellbrush", "untilnow", "manex ai", "anythink", "wypoon", "ziina",
    "buying labs", "huup", "aurelo", "starnek", "stablegroup", "corgi",
    "the arrival technology", "hud", "interfere", "faction", "remanence", "dualentry",
    "orpex", "viqu", "io associates", "xcede", "auro recruitment", "oliver bernard",
    "silence laboratories", "swiftguest", "botdigit", "bidpilotpro", "bairesdev", "kake",
    "squads", "ruby labs", "improbable", "wizdaa", "xceed", "lockedin ai", "siena",
    "silver.dev", "collabify", "tether keet", "search atlas", "kraken", "mixrank",
    "proofline", "benrey", "equitable earth", "peratera", "utorg", "syscov",
    "salmon group", "opinov8", "over99", "globalli", "eventfirst", "proxify", "proxify ab",
    "lazer", "brainverse", "dataspecc", "qualitesoft", "jeda.ai", "dojoit", "arounda",
    "lexin", "georion", "tailor", "remote people", "aicente", "toggl", "dispensed",
    "fueled", "praktika", "nextmatch", "wobbit", "virmondo", "sphere labs", "cyrolo",
    "propr", "genki", "staygenki", "bluepina", "wact", "flaredog", "quayutec", "omnea",
    "stratos", "stratos technologies", "borderless", "saasify labs", "getlaunchday",
    "nebius", "retell", "retell ai", "fidamy", "scope ai", "getscope", "seamflow",
    "casavi", "metaview", "conduct", "aiomic", "optimal", "re-leased", "cleargrid",
    "stream", "cloover", "profound", "brainial", "brightflag", "twenty", "outset", "nano",
}

NEG_VISA = re.compile(
    r"(do not (offer|provide)|doesn't offer|no visa|without sponsorship|"
    r"not (be )?able to sponsor|cannot sponsor|won't sponsor|will not sponsor|"
    r"no sponsorship|must .*authorized to work|already (have|has) .*work (authorization|permit|rights)|"
    r"US citizen|citizens? only|must reside in .{0,40}United States)",
    re.I,
)
POS_REMOTE_INT = re.compile(
    r"(worldwide|from anywhere|work from anywhere(?! in the (US|United States|UK|Canada|Australia))|"
    r"hire globally|hiring globally|international (applicants|candidates|hires)|"
    r"overseas|EOR|employer of record|remote[- ]international|anywhere in the world|"
    r"candidates from around the world)",
    re.I,
)
POS_VISA = re.compile(
    r"(we (do )?sponsor visas?|visa sponsorship|will sponsor|sponsorship available|"
    r"relocation (support|assistance|package)|visa assistance)",
    re.I,
)
STACK = re.compile(r"(react|next\.?js|typescript|full[- ]?stack|frontend|front-end)", re.I)
US_ONLY_REMOTE = re.compile(
    r"(work from anywhere in the US|remote[, ]+USA|US[- ]only|must .{0,30}United States|"
    r"authorized to work in the United States|reside in .{0,20}United States)",
    re.I,
)

li_seeds = [
    {"title": "Frontend Developer", "company": "Bump", "url": "https://ca.linkedin.com/jobs/view/frontend-developer-at-bump-4491587480", "date": "2026-11-17", "location": "Ottawa, Ontario, Canada", "portal": "linkedin-search", "source": "cli"},
    {"title": "Frontend Engineer", "company": "Evlo AI", "url": "https://www.linkedin.com/jobs/view/frontend-engineer-at-evlo-ai-4491413226", "date": "2026-11-17", "location": "Atlanta, GA", "portal": "linkedin-search", "source": "cli"},
    {"title": "Senior Front-End Engineer", "company": "Wiley", "url": "https://jo.linkedin.com/jobs/view/senior-front-end-engineer-at-wiley-4491806194", "date": "2026-11-18", "location": "Amman, Amman, Jordan", "portal": "linkedin-search", "source": "cli"},
    {"title": "Frontend Engineer - Agentic AI", "company": "Hawk", "url": "https://de.linkedin.com/jobs/view/frontend-engineer-agentic-ai-at-hawk-4479598989", "date": "2026-11-05", "location": "Berlin, Germany", "portal": "linkedin-search", "source": "cli"},
    {"title": "Senior Software Engineer (TypeScript, Next.js / Node.js) (m/f/x)", "company": "Atolls", "url": "https://de.linkedin.com/jobs/view/senior-software-engineer-typescript-next-js-node-js-m-f-x-at-atolls-4488164592", "date": "2026-11-06", "location": "Berlin, Germany", "portal": "linkedin-search", "source": "cli"},
    {"title": "Founding Product Engineer (m/w/d) – Agentic AI Platform", "company": "hyrUP GmbH", "url": "https://de.linkedin.com/jobs/view/founding-product-engineer-m-w-d-%E2%80%93-agentic-ai-platform-at-hyrup-gmbh-4488504463", "date": "2026-11-12", "location": "Berlin, Germany", "portal": "linkedin-search", "source": "cli"},
    {"title": "Senior Full Stack & AI Engineer (m/w/d)", "company": "Overfly", "url": "https://de.linkedin.com/jobs/view/senior-full-stack-ai-engineer-m-w-d-at-overfly-4485854340", "date": "2026-11-05", "location": "Berlin, Germany", "portal": "linkedin-search", "source": "cli"},
    {"title": "Senior Frontend Engineer", "company": "AMBOSS", "url": "https://de.linkedin.com/jobs/view/senior-frontend-engineer-at-amboss-4449566743", "date": "2026-11-11", "location": "Berlin, Germany", "portal": "linkedin-search", "source": "cli"},
    {"title": "Senior Product Engineer", "company": "Bolt", "url": "https://de.linkedin.com/jobs/view/senior-product-engineer-at-bolt-4489270443", "date": "2026-11-12", "location": "Berlin, Germany", "portal": "linkedin-search", "source": "cli"},
    {"title": "Senior Front-End Engineer (React) - Personalization", "company": "Picnic Technologies", "url": "https://nl.linkedin.com/jobs/view/senior-front-end-engineer-react-personalization-at-picnic-technologies-4484056416", "date": "2026-11-17", "location": "Amsterdam, North Holland, Netherlands", "portal": "linkedin-search", "source": "cli"},
    {"title": "Frontend Engineer — React & Next.js", "company": "voila.eu", "url": "https://nl.linkedin.com/jobs/view/frontend-engineer-%E2%80%94-react-next-js-at-voila-eu-4488849956", "date": "2026-11-09", "location": "Leusden, Utrecht, Netherlands", "portal": "linkedin-search", "source": "cli"},
    {"title": "Senior Full Stack Engineer, AI Platform & Agents", "company": "Wolters Kluwer", "url": "https://nl.linkedin.com/jobs/view/senior-full-stack-engineer-ai-platform-agents-at-wolters-kluwer-4354854127", "date": "2026-11-10", "location": "Alphen aan den Rijn, South Holland, Netherlands", "portal": "linkedin-search", "source": "cli"},
]

dropped = []
keepers_pre = []

for h in hits + li_seeds:
    company = (h.get("company") or "").strip()
    title = (h.get("title") or "").strip()
    url = (h.get("url") or "").strip()
    desc = h.get("description") or ""
    text = f"{title}\n{desc}\n{json.dumps(h.get('sponsorship') or {})}"
    ckey = company.lower().strip()
    # normalize lemon.io
    if ckey.startswith("lemon"):
        ckey = "lemon.io"
    if any(r == ckey or r in ckey for r in RECYCLE):
        dropped.append((company, title, "recycle"))
        continue
    if not STACK.search(f"{title} {desc[:800]}"):
        # allow if title has engineer and skill_score high from board
        if (h.get("skill_score") or 0) < 0.7 and "react" not in title.lower() and "typescript" not in title.lower() and "next" not in title.lower() and "full" not in title.lower() and "front" not in title.lower():
            dropped.append((company, title, "stack"))
            continue
    # Negate false-positive verified
    if NEG_VISA.search(text) and not re.search(r"we do sponsor visas", text, re.I):
        # exception: Anthropic style "we do sponsor" already handled
        if "we do sponsor" not in text.lower() and "we sponsor" not in text.lower():
            dropped.append((company, title, "neg_visa"))
            continue
    # US-only remote without international
    if US_ONLY_REMOTE.search(text) and not POS_REMOTE_INT.search(text):
        # Pearl-like: world candidates but US workplace
        if "work from anywhere in the us" in text.lower() or "authorized to work in the united states" in text.lower():
            dropped.append((company, title, "us_only"))
            continue
    # For board hits with sponsorship object, require verified OR (possible/unknown + strong remote-int)
    sp = h.get("sponsorship") or {}
    clas = sp.get("classification")
    path = h.get("path")
    evidence = " ".join(e.get("excerpt", "") for e in (sp.get("evidence") or []))
    if clas == "verified_in_listing" and NEG_VISA.search(evidence):
        dropped.append((company, title, "false_verified"))
        continue
    # Bosch Romania local relocation — not target geo Path B
    if "timi" in (h.get("location") or "").lower() or (company.lower() == "bosch" and "ron" in evidence.lower()):
        dropped.append((company, title, "local_reloc_non_target"))
        continue
    keepers_pre.append({
        "title": title,
        "company": company,
        "url": url,
        "date": h.get("date"),
        "location": h.get("location"),
        "portal": h.get("portal") or "visa-discover",
        "source": h.get("source") or "cli",
        "path": path,
        "sponsorship": sp,
        "description_snip": desc[:500],
        "rank_overall": h.get("rank_overall"),
        "skill_score": h.get("skill_score"),
        "sponsorship_score": h.get("sponsorship_score"),
    })

out = ROOT / ".tmp" / "lead_candidates.json"
out.write_text(json.dumps(keepers_pre, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"pre_keepers={len(keepers_pre)} dropped={len(dropped)}")
for d in dropped:
    print("DROP", "|".join(str(x) for x in d))
print("---KEEP---")
for k in keepers_pre:
    print(f"{k['company']}|{k['title'][:55]}|{k.get('path')}|{(k.get('sponsorship') or {}).get('classification')}|{k['url'][:80]}")
