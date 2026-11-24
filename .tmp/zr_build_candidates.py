import json
import os
import re
from pathlib import Path

out = Path(os.environ["TEMP"]) / "zr"
hd = """cognite,wispr,apiphany,sonder,bio,riplo,frontier health,thinking machines,flexport,sitefire,river,openart,formalize,solve intelligence,typesafe,carman,wn social,pancakeswap,adbite,astell,proxybase,utility profit,databento,netlify,railway,vitvio,peec,elevenlabs,bolt,swisscom,supabase,zalando,gray swan,amboss,elitebrain,talenthop,jobgether,seamflow,omnea,stratos,picnic,optiver,bairesdev,lemon,proxify,silver.dev,toggl,hud,reflection,fluence,clickhouse,cloover,doctolib,zoopla,trainline,mytos,rulemapping,fortus,teero,apata,redcare,discord,wheely,faction,profound,midnite,animore,impower,onelab,epidemic sound,n8n,ruya,pearl,hire hangar,naphora,clera,conduct,fuse energy,air apps,outset,personio,helsing,ubiquiti,scaleway,juxt,akeno,owen thomas,stackai,solvd,siena,fortaegis,staffbase,fueled,circleso,quayutec,flaredog,bluepina,bluedotprint,lynxiz,enzziro,vitraga,techlumas,borderless,fidamy,scope ai,manex,signals,insightiq,cyrolo,propr,dryft,pigment,vercel,ace & tate,skalar,comstruct,retell,embl,artie,flick,interfere,beacon,legora,coram,gametime,pango,brainial,brightflag,twenty,dualentry,teamviewer,trackunit,glean,buildops,verneek,bosch,sondera,troveo,true talent"""
hd_set = [h.strip() for h in hd.split(",")]
agency = (
    "recruit",
    "staffing",
    "agency",
    "consulting",
    "toptal",
    "andela",
    "talent solutions",
    "searchability",
    "oliver bernard",
    "computer futures",
    "e-frontiers",
)

prefs = Path(r"d:\jobboard\ai-job-search\leads\preferences.md").read_text(encoding="utf-8").lower()

seeds = []
for f in sorted(out.glob("*.json")):
    if f.name.startswith("cand") or f.name.startswith("store") or "visa" in f.name:
        continue
    raw = f.read_bytes()
    text = None
    for enc in ("utf-8-sig", "utf-16", "latin-1"):
        try:
            text = raw.decode(enc)
            break
        except Exception:
            continue
    text = (text or "").strip()
    if not text:
        print(f.name, "empty")
        continue
    try:
        data = json.loads(text)
    except Exception:
        i, j = text.find("{"), text.rfind("}")
        try:
            data = json.loads(text[i : j + 1])
        except Exception as e:
            print(f.name, "parse fail", e)
            continue
    results = data if isinstance(data, list) else data.get("results", [])
    print(f.name, "n=", len(results))
    for r in results:
        co = (r.get("company") or "").strip()
        title = (r.get("title") or "").strip()
        url = r.get("url") or r.get("link") or ""
        if not co or not url or not title:
            continue
        low = co.lower()
        if any(h in low for h in hd_set):
            continue
        if any(a in low for a in agency):
            continue
        if low in prefs or any(tok and tok in prefs for tok in [low] if len(low) > 3):
            # loose recycle: company name substring in prefs
            if re.search(r"\b" + re.escape(low) + r"\b", prefs):
                continue
        seeds.append(
            {
                "title": title,
                "company": co,
                "url": url,
                "date": r.get("date"),
                "location": r.get("location"),
                "portal": "linkedin-search",
                "source": "cli",
            }
        )

# dedupe by url
seen_u = set()
uniq = []
for s in seeds:
    if s["url"] in seen_u:
        continue
    seen_u.add(s["url"])
    uniq.append(s)

# cap 30
uniq = uniq[:30]
p = out / "zr_candidates.json"
p.write_text(json.dumps(uniq, indent=2), encoding="utf-8")
print("wrote", len(uniq), p)
for s in uniq:
    print("-", s["company"], "|", s["title"][:55], "|", (s.get("location") or "")[:35])
