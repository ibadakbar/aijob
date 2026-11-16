# Lead search defaults (Ibad Akbar)

The `/leads` agent loads this file and applies these defaults unless the user overrides them in plain language.

## Operating mode: DEPTH INTELLIGENCE (default)

When the user says **find leads**, **today’s leads**, **worldwide**, **warm leads**, **deep**, **authentic**, or anything vague — run **Depth Intelligence**, not a Remotive/YC-WAAS dump.

Goal: **few, authentic, active** React / Next.js / TypeScript opportunities with a real buyer or hiring signal — not recycled aggregator noise.

### Depth Intelligence rules (non-negotiable)
1. **Quality ≫ quantity** — prefer **3–8** verified rows over 20 recycled names. Empty table + “dry” is better than fake warmth.
2. **Company-site first** — discover via WebSearch/WebFetch of `/careers` `/jobs` `/contact` `/about`, LinkedIn (low volume), then `visa_discover`. Treat Remotive / Arbeitnow / YC Work at a Startup **as seeds only** — never as the main table if ≥40% are recycle/blocklist.
3. **Authentic = natural listing** — role lives on the **employer domain** or ATS they own (Greenhouse/Ashby/Lever/Teamtailor on *their* board), posted **≤7 days** (prefer ≤3), still accepting applications.
4. **Active client / demand proven** — open role text, day-rate brief, or explicit “hiring / contracting for X” with a **published** mailbox or named founder LinkedIn. Funding/WAAS “[Hiring]” alone is **not** enough.
5. **Contact must be literal** — quote the source URL for every email/phone. Never invent.
6. If adapters only return recycle → **say boards saturated**, switch to Depth prompts in `leads/PROMPT_PACK.md` (Depth A–D), do not re-sell Lemon/Fluence/Strac/Quill/etc.

### Quality tiers (always rank this way)
| Tier | Meaning | Agent action |
|------|---------|--------------|
| **A** | Explicit demand + **published email** (on a public page) | Show first · draft outreach |
| **B** | Hiring / demand + **named founder LinkedIn** published | Show second · LinkedIn draft |
| **C** | Real job / contract but **apply URL only** | Secondary · route to `/apply` |
| **D** | No demand, marketplace noise, peer freelancers selling services | Hide or one-line “skipped” |

### What “cold / no reply” means here
Demote or skip:
- Apply-URL-only boards with no mailbox and no named founder
- Peer freelancers / white-label *vendors* (competitors, not buyers)
- `POTENTIAL_FIT` with `demand_proven=false` (funding/launch alone)
- Stale listings (>21 days) unless Tier A email still published
- India-only onsite with no remote/visa path (unless user asks India)

## Default markets (worldwide into these)
United States, Canada, United Kingdom, Australia, New Zealand, Germany, Netherlands, Ireland, Europe (EU/EEA), UAE, Saudi Arabia, Qatar, Switzerland, Sweden, Finland, Denmark, Pakistan  
**plus remote roles that hire into those markets**

## Default stack
React, Next.js, TypeScript, Node.js, full-stack / SaaS

## Prefer / boost (ranking)
- `verified_in_listing` visa sponsorship, explicit **Will sponsor**, relocation package, remote-international (hires from PK into target geos)
- Tier A published `careers@` / `jobs@` / `founders@` / `hiring@` on company domain
- YC / funded **only** when there is an **explicit open role** + (Will sponsor OR remote-international)

## Hard skips (unless user overrides)
- US-citizen-only / already-have-local-work-rights / “no visa sponsorship”
- German / Dutch / Arabic as **required** working language
- India-only onsite with no remote/visa path
- Peer freelancers and white-label **vendors selling** capacity (not buyers)
- **Recycle blocklist** (do not re-present as “new” if already shown/applied/rejected/closed): Fluence, Askable, Lemon.io, Strac, Quill, Velt, SalesPatriot, Karumi, Guac, Besimple, Capix, LegalOS, Reframe, GoodPeople, Reflection, Grafana, NavVis, Jack, Situ, trivago, PixelChain, Clera, BorderPass, CanadaVisa, Hospo AI, Air Apps, throxy, Vimub, ChatBotKit, Stat Sniper, Hardihood, VIBOA, Nord Harton, Shopitecture, eCommerce Smart, Underwaterpistol, Swanky, Charle, NICCOS, Prosper Digital, Refulfil, ClickHouse, Benetics, Contentful, TensorX, Almedia, Signifly, Momo Medical, Spiich, Canonical, Resquared, Health Harbor, Ciro, Doctolib, Templafy, Popl, Owen Thomas, Primus Connect, HartleyCo, Mitre Media, Sportsbet, DEPT, Presidio, Digital Melon, B2Dubai, Laine, Serko, CoreFlow, Objective Corporation, Fuse Energy, Blinq, Virtual Days, Ahoy, Supplios, Dream Broker, Entries, Taxxa, Rumli, FalschParker, Sajn, RoomStay, Matchspace Music, DiligenceSquared, Runway, Spark AI, Flick, HappyRobot, item, Clara, DreamCraft, Spellbrush, UntilNow, Manex AI, Anythink, Wypoon, Ziina, Buying Labs, Huup, Aurelo, Starnek, StableGroup, Corgi, The Arrival Technology, HUD, Interfere, Faction, Remanence, DualEntry, Orpex, VIQU, iO Associates, Xcede, Auro Recruitment, Few&Far Pierce Mitchell Outside-IR35 FE, Oliver Bernard bank FE contract — plus any company already in `job_search_tracker.csv` / prior outreach / rejected

## Anti-saturation (adapters are tired)
- Do **not** dump Remotive/WAAS top-20 as the main table when >40% are recycle/blocklist — go **Depth Intelligence** (company-site + LinkedIn + email proof) or say “boards saturated”
- Prefer LinkedIn (low volume) + `visa_discover` + company-site email enrichment over repeating the same Greenhouse/YC WAAS names
- Rotate **Depth A–D** in `leads/PROMPT_PACK.md` before classic Lanes 1–4 after a heavy apply/reject week
- Prefer roles **posted ≤3–7 days**; skip closed / “no longer accepting”
- After presenting a company once, add it to recycle — do not reshown as NEW

## Contact rules
- **Email / phone:** only if **literally published** on a public page — never invent `jobs@` / `name@company.com`
- Prefer company Contact / About / Careers pages over job-board wrappers
- Job board with Apply only → Tier C (`/apply`), not cold email
- YC: founder names + LinkedIn from public YC pages; email only from company site
- Master contact harvest (historical): `leads/exports/ALL_EMAILS_PHONES_SIMPLE.csv` — do not re-sell those as fresh discoveries without a **new** open role

## World Leads discovery split (agent must run)
| User says… | Agent runs… |
|------------|-------------|
| find leads / today’s leads / worldwide / warm / deep / authentic / (empty) | **Depth Intelligence** (see `leads.md` World path): company-site WebSearch first → LinkedIn low-vol → `visa_discover` → ATS seeds only → email proof. Max 3–8 authentic. Remotive/YC only if Depth dry |
| Depth A / B / C / D | Exact prompts in `leads/PROMPT_PACK.md` |
| jobs / hiring / Remotive | jobs path (still prefer Tier A/B; do not dump recycle) |
| email / phone / cold email / contact | Direct-contact enrichment (published only) |
| freelance / contract / relocation / visa | Depth filter to those signals |
| agency / white-label | agency mode |
| YC / co-founder | ycombinator **only with open role** + site email enrichment |
| apply / CV | `/apply <url>` |

## Output the user wants
After every discover, show **Tier A/B first** (max ~10), then a short Tier C appendix if useful:

1. Tier · Company / role  
2. Geo  
3. **Published email** (or none)  
4. **Published phone** (or none)  
5. Contact path (founder LinkedIn / apply)  
6. Source URL  
7. Next action  

One question: reply with a number to **outreach**, **apply**, or **skip**.
