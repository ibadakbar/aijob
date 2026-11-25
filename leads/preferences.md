# Lead search defaults (Ibad Akbar)

The `/leads` agent loads this file and applies these defaults unless the user overrides them in plain language.

## Operating mode: BEST LEADS (default) + DEPTH INTELLIGENCE

When the user says **find leads**, **today’s leads**, **best leads**, **worldwide**, **warm leads**, **deep**, **authentic**, or anything vague — run **Best Leads Mode** (below), not a Remotive/YC-WAAS dump and not a same-day O→S death spiral.

Goal: **3–8 authentic, hireable** React / Next.js / TypeScript rows — Tier A/B first, Tier C allowed when A/B thin — not recycled aggregator noise and not empty tables that hide apply-ready Path A/B roles.

### Best Leads Mode (ACTIVE — yield-smart, still honest)
Fixes empty “0 NEW” runs caused by stacking every hard filter at once.

1. **Run this order every vague `/leads` (do not skip to Depth S first):**
   1. **Volume-first:** `python tools/board_scrape.py --limit 30 --since 7d` (or `visa_discover --volume --path-ab --since 14d --new-only --limit 40`). Uses JobSpy + RemoteOK + WWR + **Hiring Cafe** when `APIFY_TOKEN` is in `.env`. Prefer this over LinkedIn-only.
   2. Light LinkedIn only if volume thin: Path A `-l Remote --remote remote --jobage-minutes 2880` (48h) **cap 8**; Path B 2–3 hubs `--jobage 14` + visa|reloc **cap 8**. Drop agencies.
   3. WebSearch owned ATS only (Ashby/GH/Lever/Teamtailor/Personio/Workable) — Path A/B eligibility terms
   4. Contact ladder on every elig-pass before marking fail
   5. **Weekly inventory:** `python tools/harvest_boards.py --ats greenhouse,ashby,lever,smartrecruiters --limit 40 --write` (new ATS slugs; do not re-scrape the same 12 boards forever)
2. **Fake-remote DROP (engine-enforced + agent):** auto-drop `within the U.S.`, `US only`, `Remote - United States`, `Fully Remote (US)`, `U.S. Based`, country-only remote (UK/AU/CA-only) even when the feed says “Worldwide”. Path A needs real worldwide / from anywhere / hire globally / EOR.
3. **Freshness (Best Leads, not Navigator-strict):** Path A ≤**10d**; Path B ≤**14d**; undated but **still accepting** on owned ATS → allow as Tier C with `Conf. med` (do **not** bury Anthropic-class roles in near-miss only).
4. **Tier C budget:** when Tier A+B < 3, allow up to **3** Tier C (elig ✓ + owned ATS + still open). Prefer `/apply` next action.
5. **Phone is optional** — never drop a Tier A email row for missing phone. Show phone only if literal.
6. **Salvage band (when NEW would be 0):** promote up to **2** near-misses that have (elig ✓ + published `jobs@`/`careers@`/`hello@`) **or** (elig ✓ + named founder LI) even if Path A 8–21d stale — mark `salvage: true` and quote the waiver reason. Do not invent contacts.
7. **Sponsor-Watch:** elig ✓ but posted 15–90d → max 5 rows, not NEW, offer waive → apply.
8. **Escalation:** only if Best Leads returns 0 NEW **and** salvage empty → Depth R once → Depth S once → Convert Day. Do **not** run O→P→Q→R→S in one day on a vague “find leads”. Cap **1 discovery turn/day** when boards are saturated; rest of day = convert + `/outcome`.
9. **Outcome / convert loop:** after presenting NEW, push `/apply` on keeps. Open convert backlog includes **Elile** (Senior Front-end) + **Supabase** (DevRel) when still open. After apply, remind once to `/outcome`. Demote no-reply / rejected in tracker for 14d.

### Depth Intelligence rules (non-negotiable)
1. **Quality ≫ quantity** — prefer **3–8** verified rows over 20 recycled names. Empty table + “dry” is better than **fake** warmth — but Best Leads salvage/Tier C rules above beat a useless empty table that hides real Path A/B.
2. **Company-site first** — discover via WebSearch/WebFetch of `/careers` `/jobs` `/contact` `/about`, LinkedIn (low volume), then `visa_discover`. Treat Remotive / Arbeitnow / YC Work at a Startup **as seeds only** — never as the main table if ≥40% are recycle/blocklist.
3. **Authentic = natural listing** — role lives on the **employer domain** or ATS they own (Greenhouse/Ashby/Lever/Teamtailor on *their* board), still accepting applications (freshness per Best Leads / Depth R/S caps).
4. **Active client / demand proven** — open role text, day-rate brief, or explicit “hiring / contracting for X” with a **published** mailbox or named founder LinkedIn. Funding/WAAS “[Hiring]” alone is **not** enough.
5. **Contact must be literal** — quote the source URL for every email/phone. Never invent.
6. If adapters only return recycle → **say boards saturated**, switch to Depth prompts in `leads/PROMPT_PACK.md` (Depth A–O), do not re-sell Lemon/Fluence/Strac/Quill/etc.
7. **Listings-saturated mode (only after Best Leads dry)** — stop re-scraping the same job boards. Switch to **Demand Graph** (Depth O) → **Sponsored Mobility** (Depth P) → **Sponsor Hub Cities** (Depth Q) → **Listing Navigator** (Depth R) → after R dry + contact-ladder / “more parameters / find more listings” → **Parametric Board Sweep (Depth S)**. Dual-proof for Tier A/B; Tier C per Best Leads budget. Near-miss log required on Navigator/S runs. Zero NEW OK only with an honest near-miss log **and** salvage attempt done.

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
- Onsite / hybrid **without** visa sponsorship or relocation
- **India / India-primary listings** (Bangalore, Mumbai, Hyderabad, India-only remote/onsite) — hard skip unless user explicitly asks India

## Default markets (worldwide into these)
United States, Canada, United Kingdom, Australia, New Zealand, Germany, Netherlands, Ireland, Europe (EU/EEA), Norway, Belgium, Czechia, Singapore, UAE, Saudi Arabia, Qatar, Switzerland, Sweden, Finland, Denmark, Pakistan  
**plus remote roles that hire into those markets**

## Default stack
React, Next.js, TypeScript, Node.js, full-stack / SaaS

## Workplace filter (ACTIVE — remote-first + sponsored mobility)
**Prefer fully remote.** Onsite / hybrid are allowed **only** when the employer listing literally offers **visa sponsorship** and/or **relocation** into a target geo. Without that quote → remote-only path.

### Path A — Remote (default)
Keep fully remote when at least one of:
1. **Visa sponsorship** — will sponsor / sponsorship available for a remote hire, OR
2. **Remote-international** — worldwide / from anywhere / international / overseas applicants / EOR / hire globally

Country-only remote (e.g. “remote Australia”, “remote UK only”, “within the U.S.”) = **DROP** (fake-remote). WWR/RemoteOK “Worldwide” labels do **not** override a US/UK-only body. Overseas hire or remote sponsorship must be explicit without a geo-lock.

### Path B — Onsite / hybrid (sponsored mobility only)
Keep onsite or hybrid **only if** the listing quotes **will sponsor / visa sponsorship / relocation support / relocation package** into US/CA/UK/IE/NL/DE/AU/NZ/UAE/EU/EEA (or similar target geo).  
Onsite/hybrid with **no** sponsorship and **no** relocation = **DROP**.

LinkedIn CLI: prefer `--remote remote` for Path A; for Path B run a **separate** low-volume search **without** remote filter + keywords `visa OR sponsor OR relocation`, then dual-check the listing text before keeping.

## Prefer / boost (ranking)
- Fully remote + `verified_in_listing` visa sponsorship / will sponsor
- Fully remote-international (worldwide / from anywhere / hire globally / EOR)
- Onsite/hybrid + verified sponsorship **and** relocation (strongest Path B)
- Tier A published `careers@` / `jobs@` / `founders@` / `hiring@` on company domain
- YC / funded **only** when there is an **explicit open role** + (Will sponsor OR remote-international OR relocate+sponsor)

## Hard skips (unless user overrides)
- **Onsite** / **hybrid** with **no** visa sponsorship and **no** relocation
- Country-only / **fake-remote** (`within the U.S.`, `US only`, `Remote - United States`, `Fully Remote (US)`, UK/AU/CA-only remote) even if the aggregator title says Worldwide
- US-citizen-only / already-have-local-work-rights / “no visa sponsorship” (when sponsorship is the only path and remote-international is absent)
- German / Dutch / Arabic as **required** working language
- **India / India-primary** roles (any workplace) — not a target market; drop unless user asks India
- Peer freelancers and white-label **vendors selling** capacity (not buyers)
- **Recycle blocklist** (do not re-present as “new” if already shown/applied/rejected/closed): Fluence, Askable, Lemon.io, Strac, Quill, Velt, SalesPatriot, Karumi, Guac, Besimple, Capix, LegalOS, Reframe, GoodPeople, Reflection, Grafana, NavVis, Jack, Situ, trivago, PixelChain, Clera, BorderPass, CanadaVisa, Hospo AI, Air Apps, throxy, Vimub, ChatBotKit, Stat Sniper, Hardihood, VIBOA, Nord Harton, Shopitecture, eCommerce Smart, Underwaterpistol, Swanky, Charle, NICCOS, Prosper Digital, Refulfil, ClickHouse, Benetics, Contentful, TensorX, Almedia, Signifly, Momo Medical, Spiich, Canonical, Resquared, Health Harbor, Ciro, Doctolib, Templafy, Popl, Owen Thomas, Primus Connect, HartleyCo, Mitre Media, Sportsbet, DEPT, Presidio, Digital Melon, B2Dubai, Laine, Serko, CoreFlow, Objective Corporation, Fuse Energy, Blinq, Virtual Days, Ahoy, Supplios, Dream Broker, Entries, Taxxa, Rumli, FalschParker, Sajn, RoomStay, Matchspace Music, DiligenceSquared, Runway, Spark AI, Flick, HappyRobot, item, Clara, DreamCraft, Spellbrush, UntilNow, Manex AI, Anythink, Wypoon, Ziina, Buying Labs, Huup, Aurelo, Starnek, StableGroup, Corgi, The Arrival Technology, HUD, Interfere, Faction, Remanence, DualEntry, Orpex, VIQU, iO Associates, Xcede, Auro Recruitment, Few&Far Pierce Mitchell Outside-IR35 FE, Oliver Bernard bank FE contract, Silence Laboratories, SwiftGuest, BotDigit, WebAccessibility.co, BidPilotPro, BairesDev, Kake, Squads, Ruby Labs, Improbable, Wizdaa, XCEED, LockedIn AI, Siena, Silver.dev, Collabify, Tether Keet, Search Atlas, Kraken, MixRank, Proofline, Benrey, Equitable Earth, Peratera, Utorg, Syscov, Salmon Group, Opinov8, Over99, Globalli, eventfirst, Proxify, Lazer, Brainverse, Dataspecc, Qualitesoft, Jeda.ai, Dojoit, Arounda, Lexin, Georion, Tailor, Remote People, aicente, Toggl, Dispensed, Fueled, Praktika, NextMatch, Wobbit, Virmondo, Sphere Labs, Cyrolo, Propr, Genki, Staygenki, bluepina, WAct, WAConversionTracking, Flaredog, Quayutec, Omnea, STRATOS, STRATOS Technologies, Borderless, SaaSify Labs, GetLaunchDay, Nebius, Retell, Retell AI, Fidamy, Scope AI, Getscope, Seamflow, Casavi, Metaview, Conduct, Aiomic, Optimal (NZ/AU-only remote), Re-Leased, ClearGrid, Stream (GetStream Staff Backend Amsterdam), Cloover, a16z-speedrun Stealth, Profound Frontend, Brainial, Brightflag, Twenty, Outset, nano, Catawiki, Inspira Financial, Samsara, Mistral.ai, Mistral, Wise, Pleo, Mammoth-AI, CoLab Software, League, Bosch, PRG Pakistan, Nubank, Axle Careers, Render, Dawn Technology, Yooli, WelcomeHome Software, Renaissance Learning, Secure Privacy, A.Team, Dropbox, 1KOMMA5, CloudPSO, EHB Technologies — plus **any company/URL already in** `job_search_tracker.csv` / prior outreach / rejected / `job_scraper/seen_jobs.json` / last Convert Day or Sponsor-Watch table
- **Worldwide WebSearch anti-repeat:** Never treat a Google/Bing hit as NEW if the employer or ATS slug was already presented. Same job on LinkedIn vs Ashby vs Arbeitnow = one listing. Prefer empty NEW + `dropped_as_repeat` count over re-showing Cyrolo/Omnea/Scope/Seamflow/etc.

## Anti-saturation (adapters are tired)
- Do **not** dump Remotive/WAAS top-20 as the main table when >40% are recycle/blocklist — go **Depth Intelligence** (company-site + LinkedIn + email proof) or say “boards saturated”
- Prefer **`--volume` / `board_scrape` + Hiring Cafe** + owned ATS + company-site email enrichment over LinkedIn guest spam; LI is a thin additive only
- Weekly `harvest_boards.py --write` so ATS discovery is not stuck on the same curated slugs
- After Depth E–N dry / “listings finished” → Depth O → Depth P → Depth Q → Depth R (Listing Navigator) → Depth S (Parametric Board Sweep). Do **not** re-run Dual-Proof / Manager-Post / Morning Minutes / Async/EOR / Demand Graph / Depth P Path A / Depth Q hub keyword sweeps / Depth R single-query Navigator the same day once S is chosen
- Rotate **Depth A–S** in `leads/PROMPT_PACK.md` before classic Lanes 1–4 after a heavy apply/reject week
- Prefer roles **posted ≤3–7 days**; Path B up to ≤14d (Navigator/S: Path B ≤14d / Path A ≤10d on S, ≤7d on R); skip closed / “no longer accepting”
- After presenting a company once, add it to recycle — do not reshown as NEW
- Cap discovery energy: if **two consecutive** Depth runs return 0 NEW **and** near-miss log is empty, stop discovering and force **convert backlog**. If near-misses exist → one contact-ladder pass on those before quitting. After contact-ladder + Depth S both dry → **Convert Day** only (`PROMPT_PACK.md` — `/apply`/`/outcome` backlog + optional Sponsor-Watch; **no Depth T** the same day)
- When user says listings empty / agent not finding jobs → run **Depth R Listing Navigator** (not another Depth Q paste). When they say **more parameters / find more listings / Depth S** after R → **Depth S Parametric Board Sweep**

## Contact rules
- **Email / phone:** only if **literally published** on a public page — never invent `jobs@` / `name@company.com`
- Prefer company Contact / About / Careers pages over job-board wrappers
- **Contact ladder (Navigator):** Imprint → Contact → Careers FAQ → Press/About Team → Ashby/GH “email us” on any board role → named founder/CTO LinkedIn from Press or company About — complete before marking contact-fail
- Allowed mailboxes for Tier A: `careers@` `jobs@` `hiring@` `hello@` `join@` `talent@` `people@` `founders@` (and literal Talent Lead name@ on ATS). `support@` / `info@` alone ≠ Tier A unless the page labels it for hiring
- Job board with Apply only → Tier C (`/apply`) if eligibility ✓ and ≤7d — not cold email
- YC: founder names + LinkedIn from public YC pages; email only from company site
- Master contact harvest (historical): `leads/exports/ALL_EMAILS_PHONES_SIMPLE.csv` — do not re-sell those as fresh discoveries without a **new** open role

## World Leads discovery split (agent must run)
| User says… | Agent runs… |
|------------|-------------|
| find leads / today’s leads / best leads / worldwide / warm / deep / authentic / (empty) | **Best Leads Mode** (this file): `visa_discover` → LI 48h/7d + 2–3 Path B hubs → owned ATS → contact ladder → Tier A/B then Tier C ≤3 → salvage ≤2 if dry. Remotive/YC only if Best Leads dry. Do **not** auto-run full O→S the same day |
| Depth A / B / C / D / E–O / Demand Graph / listings finished / more powerful | Exact prompts in `leads/PROMPT_PACK.md` (prefer **Depth O** when boards dry) |
| visa / relocate / onsite / hybrid / sponsored mobility | **Depth P** — remote-first; onsite/hybrid only with sponsor/relocation |
| sponsor hubs / Path B primary / hub cities / after Depth P | **Depth Q** — Path B–primary dual-proof in sponsor hub cities |
| navigator / listings empty / agent not finding / search better / after Depth Q dry | **Depth R** — Listing Navigator (company→ATS→contact ladder) |
| more parameters / find more listings / Depth S / parametric / multi-ATS / after Depth R dry | **Depth S** — Parametric Board Sweep (multi-query + multi-ATS matrix) |
| jobs / hiring / Remotive | jobs path (still prefer Tier A/B; do not dump recycle) |
| email / phone / cold email / contact | Direct-contact enrichment (published only) |
| freelance / contract / relocation / visa | Depth filter to those signals |
| agency / white-label | agency mode — only when buyer needs overflow capacity THIS WEEK |
| YC / co-founder | ycombinator **only with open role** + site email enrichment |
| apply / CV | `/apply <url>` |
| convert / backlog | **Convert Day** — `/apply`/`/outcome` backlog + optional Sponsor-Watch; no discovery |
| zero-repeat / no repeats / same listings again / worldwide keeps repeating | **Zero-Repeat Worldwide** (`PROMPT_PACK.md`) — scrape_state candidates gate; empty NEW OK |
| after zero-repeat dry / next strategy / fresh minutes | **Convert leftover** same day → next morning **Fresh Minutes Zero-Repeat** (`PROMPT_PACK.md`); no Depth T same day |

## Output the user wants
After every discover, show **Tier A/B first** (max ~10), then Tier C / salvage if useful:

1. Tier · Company / role · Path A/B  
2. Geo  
3. **Published email** (or none) — required column; never invent  
4. **Published phone** (or none) — optional  
5. Contact path (founder LinkedIn / apply)  
6. Source URL / proof quote  
7. Next action  

One question: reply with a number to **outreach**, **apply**, or **skip**.

## How the user should run this (correct daily use)
1. Morning: `/leads` or `/leads best leads` → Best Leads Mode (expect 3–8 or honest dry + salvage).
2. Pick numbers → `/apply <url>` or outreach draft (never auto-send).
3. After apply/reply: `/outcome` so recycle + ranking learn.
4. If Best Leads dry same morning → **one** Depth R **or** wait for afternoon Fresh Minutes — not O→S stack.
5. Depth S only when user says **more parameters / Depth S** after R.
6. After S dry → Convert Day only (backlog + Sponsor-Watch). No Depth T same day.
7. Next calendar day → Fresh Minutes Zero-Repeat or Best Leads again.
