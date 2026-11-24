import json
import os
from pathlib import Path

out = Path(os.environ["TEMP"]) / "depth_s"
hd = """thinking machines,solve intelligence,typesafe,flexport,riplo,frontier health,sitefire,carman,wn social,pancakeswap,adbite,astell,proxybase,utility profit,databento,netlify,railway,vitvio,peec,elevenlabs,bolt,swisscom,supabase,zalando,gray swan,amboss,elitebrain,talenthop,jobgether,seamflow,omnea,stratos,picnic,optiver,bairesdev,lemon,proxify,silver.dev,toggl,hud,reflection,fluence,clickhouse,cloover,doctolib,zoopla,trainline,mytos,rulemapping,fortus,teero,apata,redcare,discord,wheely,faction,profound,midnite,animore,impower,onelab,epidemic sound,n8n,ruya,pearl,hire hangar,naphora,clera,conduct,fuse energy,air apps,outset,personio,helsing,ubiquiti,scaleway,juxt,akeno,owen thomas,stackai,solvd,siena,fortaegis,staffbase,fueled,circleso,quayutec,flaredog,bluepina,bluedotprint,lynxiz,enzziro,vitraga,techlumas,borderless,fidamy,scope ai,manex,signals,insightiq,cyrolo,propr,dryft,pigment,vercel,ace & tate,skalar,comstruct,retell,embl,wispr,apiphany,sonder,bio,artie,flick,interfere,beacon,legora,coram,gametime,pango,brainial,brightflag,twenty,dualentry,stream"""
hd_set = [h.strip() for h in hd.split(",")]
# careful: avoid matching short tokens like "open","ey","dex","swap","tailor","gigs","hawk","emma","pearl" as substrings of unrelated names — use word-ish check
agency = ("recruit", "staffing", " talent", "agency", "consulting", "toptal", "andela")

seeds = []
for f in sorted(out.glob("*.json")):
    if "visa" in f.name:
        continue
    raw = f.read_bytes()
    text = None
    for enc in ("utf-8-sig", "utf-16", "utf-16-le", "latin-1"):
        try:
            text = raw.decode(enc)
            if text.strip().startswith("{") or text.strip().startswith("["):
                break
        except Exception:
            continue
    if not text:
        print(f.name, "NO TEXT")
        continue
    text = text.strip()
    try:
        data = json.loads(text)
    except Exception:
        i, j = text.find("{"), text.rfind("}")
        if i >= 0 and j > i:
            try:
                data = json.loads(text[i : j + 1])
            except Exception as e:
                print(f.name, "PARSE FAIL", e)
                continue
        else:
            print(f.name, "PARSE FAIL")
            continue
    results = data.get("results", data if isinstance(data, list) else [])
    print(f.name, "n=", len(results))
    for r in results:
        co = (r.get("company") or "").strip()
        title = (r.get("title") or "").strip()
        url = r.get("url") or r.get("link") or ""
        loc = r.get("location") or ""
        date = r.get("date") or r.get("postedAt") or r.get("listedAt")
        low = co.lower()
        if any(h in low for h in hd_set):
            continue
        if any(a in low for a in agency):
            continue
        seeds.append(
            {
                "company": co,
                "title": title,
                "url": url,
                "location": loc,
                "date": date,
                "file": f.name,
            }
        )

seen = set()
uniq = []
for s in seeds:
    k = s["company"].lower()
    if not k or k in seen:
        continue
    seen.add(k)
    uniq.append(s)

print("--- UNIQUE", len(uniq))
for s in uniq[:45]:
    print(
        s["company"],
        "|",
        (s["title"] or "")[:55],
        "|",
        (s["location"] or "")[:35],
        "|",
        s["file"],
    )

Path(out / "seeds_unique.json").write_text(json.dumps(uniq, indent=2), encoding="utf-8")
print("wrote", out / "seeds_unique.json")
