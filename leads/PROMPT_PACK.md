# Prompt pack (Ibad) — Best Leads first, then Depth Intelligence

Paste under `/leads`. Prefer **fewer authentic hits** over adapter volume. Rotate so Remotive/YC-WAAS never dominate.

**Default for vague `/leads` / today’s / best:** **Daily Best Leads** (below) — not O→S in one sitting.

**Default mindset:** company careers / owned ATS + Path A/B eligibility + still open. Email if published; phone optional. Adapters = seed only.

**When Best Leads dry (0 NEW + salvage empty):** Depth R once → (user asks more parameters) Depth S → Convert Day.  
**When listings feel finished (Depth E–N dry):** Depth O → P → Q → R → S as in preferences — still one Depth per turn unless user stacks.

---

## Daily Best Leads (DEFAULT — use for `/leads` / best leads / today’s)

```text
/leads
DAILY BEST LEADS — yield-smart. Max 8 NEW (+ up to 2 salvage if NEW empty). Near-miss REQUIRED if dry.
Stack: React OR Next.js OR TypeScript. English-OK. No Remotive/YC as main table. Never invent email/phone.

PIPELINE (run in order — do not skip to Depth S):
1) VOLUME-FIRST: python tools/board_scrape.py --limit 30 --since 7d  (or visa_discover --volume --path-ab --since 14d --new-only --limit 40). Hiring Cafe uses APIFY_TOKEN from .env when set.
2) LinkedIn only if volume thin: Path A -l Remote --remote remote --jobage-minutes 2880 (cap 8). Path B hubs London+Berlin+Amsterdam --jobage 14 + visa|reloc (cap 8). Drop agencies.
3) ATS WebSearch: ashby/greenhouse/lever/teamtailor/personio/workable — Path A worldwide/from anywhere/EOR OR Path B visa|relocation. Open owned board only.
4) Fake-remote DROP: "within the U.S." / "US only" / "Remote - United States" / "Fully Remote (US)" / country-only remote — even if feed says Worldwide.
5) Contact ladder on every elig-pass. Phone optional.
6) Weekly (not every turn): python tools/harvest_boards.py --ats greenhouse,ashby,lever,smartrecruiters --limit 40 --write
CONVERT when dry: /apply Elile + Supabase if still open; then /outcome — max 1 discovery turn/day when saturated.

FRESHNESS: Path A ≤10d; Path B ≤14d; undated + still accepting on owned ATS → Tier C OK (Conf. med).
TIERS: A = published hiring email + elig; B = named human LI + elig; C = apply-only elig (max 3 when A+B < 3).
SALVAGE (only if NEW would be 0): up to 2 rows with elig + (jobs@|careers@|hello@ OR founder LI) even if Path A 8–21d — mark salvage:true.
SPONSOR-WATCH: elig ✓ posted 15–90d — max 5, not NEW.
DROP: preferences recycle + tracker + seen_jobs + agencies without end-employer ATS + required DE/NL/AR.

OUTPUT: NEW Tier A→B→C | Salvage (if any) | Near-miss | Sponsor-Watch | End counts
One question: # → outreach / apply / skip. If 0 NEW+salvage → suggest Depth R OR Convert Day — not full O–S same turn.
```

---

**Always append (ZERO-REPEAT — paste on every worldwide / Depth run):**

```text
Only NEW. Max 8. Quality over quantity. Never invent email/phone.
ZERO-REPEAT (hard): A row is DROP if ANY of these match — never put it in NEW, never “rediscover” via WebSearch/LinkedIn/ATS:
  (a) same URL or same ATS job UUID already in job_scraper/seen_jobs.json
  (b) same company+title already in seen_jobs OR job_search_tracker.csv
  (c) company on preferences.md recycle blocklist OR already shown in Depth E–S / Convert Day / Sponsor-Watch this week
  (d) aggregator mirror of a URL you already stored (Arbeitnow/Remotive/freehire/LinkedIn → same Ashby/GH/Lever slug)
Before the NEW table: run scrape_state.py candidates on every keep; already_seen / already_applied → silent DROP. Count dropped_as_repeat in End counts.
Do NOT refill the table with worldwide search hits that are the same Omnea/STRATOS/Cyrolo/Propr/Signals/InsightIQ/Scope/Seamflow/Faction/… names again.
Workplace: Prefer FULLY REMOTE. Onsite/hybrid ONLY if listing quotes visa sponsorship AND/OR relocation — otherwise remote only.
Remote keep: visa sponsorship OR remote-international / overseas hire. Country-only remote = skip.
Skip peer freelancers / capacity sellers. Skip US-citizen-only, local-rights-already, German/Dutch/Arabic-required.
Stack: React OR Next.js OR TypeScript full-stack / SaaS.
Prove authenticity: quote company-domain careers OR contact URL for every row.
If adapters/WebSearch return mostly recycle — say saturated + list dropped_as_repeat; leave NEW empty rather than re-paste.
```

---

## TODAY (2026-11-12) — Depth A (default)

Boards are saturated with recycle. Use **Depth A** (not classic Lane 1–8 dumps).

```text
/leads DEPTH — authentic only. Do NOT lead with Remotive/Arbeitnow/YC Work-at-a-Startup dumps.
Find React OR Next.js OR TypeScript full-stack SaaS roles posted last 5 days on COMPANY careers pages (or their own Greenhouse/Ashby/Lever/Teamtailor).
Geos: UK IE NL DE SE DK FI CH AU NZ UAE CA + remote-international into those.
Require: still open + (published careers@/jobs@/founders@/hiring@ OR named founder LinkedIn) OR verified Will-sponsor/relocation in the listing text.
Max 6. Only NEW. Quote source URL for every contact. Skip full recycle list.
```

---

## Depth B — Active buyers (clients, not job boards)

```text
/leads DEPTH buyers — product companies or studios actively hiring OR contracting React/Next/TS overflow THIS WEEK.
Discover via WebSearch company /careers /contact (not Remotive top-20).
Require literal published email on company domain. Quote URL. Max 6. Only NEW.
Geos: UK AU NL DE IE CA US remote-international. Skip vendors selling freelancers and recycle list.
```

---

## Depth C — Fresh visa / relocate (listing text only)

```text
/leads DEPTH visa — FULLY REMOTE only. React Next TypeScript full-stack where the EMPLOYER listing literally says Will sponsor OR visa sponsorship OR remote-international / overseas hire (verified_in_listing).
Skip onsite and hybrid. Posted last 7 days. English-OK. Geos: DE NL UK IE CA AU UAE US remote-int.
Enrich only those with published careers@/jobs@/founders@ OR clear ATS apply. Max 6. Only NEW. Skip recycle + local-rights-already.
```

---

## Depth D — Contract day-rate with named human

```text
/leads DEPTH contract — React OR Next OR TypeScript day-rate / freelance Outside-IR35 OR EU B2B — last 5 days.
Require published recruiter/company email OR named hiring manager LinkedIn post (quote URL).
UK IE NL DE AU SE DK CH. Skip ZZP-only local rights, German-required, SC-clearance-only, recycle. Max 6. Only NEW.
```

---

## Depth E — Intel Ops (scrape + verify; anti-SEO)

Use after a standard remote+visa pass when boards look thin or careers pages look fake. Forces triangulation and reject gates.

```text
/leads /lead-engine /linkedin-search /job-scraper
INTEL OPS — scrape hard, verify harder. Max 8. Zero OK. Quality ≫ volume.

MISSION: Find still-open React / Next.js / TypeScript / full-stack SaaS roles (or employer-paid recruiters hiring those) that are fully remote-international (or Path B with visa/reloc) — no relocation required.

CANDIDATE: Senior/full-stack React–Next–TypeScript–Node, SaaS, remote collab, 5+ yrs.
GEOS: US CA UK IE NL DE AU NZ UAE EU/EEA + remote-international into those.

WORKPLACE (hard — fail closed):
• FULLY REMOTE only — drop onsite/hybrid even with relocate packs.
• Keep ONLY if remote AND (A visa/will-sponsor for remote hire OR B worldwide / from anywhere / overseas / international applicants accepted).
• Country-only remote (AU/UK/CA-only etc.) = DROP unless overseas hire is explicit in listing text.
• LinkedIn: --remote remote only; jobage ≤7 (prefer ≤3).

SCRAPE PIPELINE (run in order; do not skip):
1) COMPANY-DOMAIN FIRST — WebSearch/WebFetch employer /careers /jobs /contact. Prefer Greenhouse/Ashby/Lever/Teamtailor on *their* board. Quote the employer URL, not a job-aggregator mirror.
2) LINKEDIN CLI — low volume; detail-fetch every keep candidate; quote the exact remote/visa/worldwide sentence + LinkedIn URL. Named recruiter OK if employer-paid (no candidate-fee mills).
3) visa_discover — keep verified_in_listing only, then drop non-remote / hybrid / relocate-onsite.
4) ATS seeds only (greenhouse,ashby,lever,arbeitnow) — adapters never fill the main table if ≥40% recycle.
NO Remotive / YC dump / SEEK.

INTELLIGENCE GATES (reject before the table):
• Authenticity: thin SEO “careers” pages with placeholder phones/addresses, unpaid intern spam, or no company footprint → needs_review or drop — never Tier A.
• Triangulate: prefer role that appears on company domain OR ATS they own; LinkedIn-only OK only with clear eligibility quote.
• Freshness: posted ≤7d (≤3 ideal); isActive/still open; expired = count not present.
• Contact: email/phone ONLY if literal on a public page — quote source URL. Prefer careers@ jobs@ hiring@ founders@. Never invent.
• Dedup: skip preferences.md recycle + already presented this week (Silence Laboratories, SwiftGuest, BotDigit, WebAccessibility.co, BidPilotPro, BairesDev, Kake) + tracker/applied/rejected.
• Language/rights: skip German/Dutch/Arabic-required; US-citizen / already-have-work-rights / PR-only; peer freelancers selling capacity.

OUTPUT — Tier A→B→C only (hide D):
| # | Tier | Company / Recruiter | Role | Geo / Mode | Posted | Eligibility quote + URL | Email (source URL) | Job link | Confidence (high/med/low + why) | Next |

Tier A = published email + clear remote + visa/international.
Tier B = named recruiter/founder LinkedIn + clear eligibility.
Tier C = clear eligibility + apply URL only.

End counts: discovered / detail-checked / qualified / with email / rejected(onsite-hybrid) / rejected(country-only or local-rights) / rejected(thin-SEO) / expired / recycle-skipped.
One question: number → outreach / apply / skip. If dry → say saturated + rotate Depth A–D.
```

---

## Depth F — Contact Deep Dive (email / recruiter / client first)

Use when Intel Ops returned apply-URL-only Tier C. Goal: **Tier A/B contacts**, not more orphan ATS links.

```text
/leads /lead-engine /linkedin-search /job-scraper
CONTACT DEEP DIVE — emails, named recruiters, real clients first; jobs only if they unlock a contact path. Max 8. Zero OK.

MISSION: Find people/companies I can actually reach for React / Next.js / TypeScript / full-stack SaaS work (fully remote + visa OR remote-international). Prefer published mailbox or named recruiter over bare Apply.

CANDIDATE: Senior/full-stack React–Next–TypeScript–Node, SaaS, remote collab, 5+ yrs.
GEOS: US CA UK IE NL DE AU NZ UAE EU/EEA + remote-international into those.

WORKPLACE (hard — fail closed):
• FULLY REMOTE only — skip onsite/hybrid.
• Keep only if remote AND (visa/will-sponsor for remote hire OR worldwide / from anywhere / overseas / international applicants).
• Country-only remote = DROP. LinkedIn: --remote remote; jobage ≤7 (prefer ≤3).

CONTACT PIPELINE (run in order; spend most effort here):
1) EMAIL HUNT on company domain — WebFetch /contact /about /careers /team /press. Keep only literal careers@ jobs@ hiring@ talent@ people@ founders@ or named person@company. Quote URL. Never invent / guess patterns.
2) NAMED RECRUITER / TA — employer-paid agency or in-house recruiter posting remote React/Next/TS with sponsorship or worldwide remote. Detail-fetch LI; quote eligibility + recruiter name + LI job URL. Email only if published on their site/post.
3) CLIENT / PRODUCT BUYER — product companies or studios with an open role OR explicit “hiring / contracting React overflow” THIS WEEK on their own site. Skip peer freelancers / white-label vendors selling capacity.
4) JOB BACKFILL — only after 1–3: company Greenhouse/Ashby/Lever + LinkedIn remote + visa_discover verified_in_listing (then drop non-remote). Enrich every keep with step 1 before tabling.
NO Remotive / YC dump / SEEK. Adapters = seeds only.

DEPTH RULES:
• Prefer 3–5 Tier A/B over 8 Tier C. If zero emails after enrichment → say so; do not invent.
• Triangulate: job URL + contact URL both quoted when both exist.
• Thin SEO / placeholder phones / jane@acme.com → drop (never Tier A).
• Dedup: preferences.md recycle + this week (Silence Laboratories, SwiftGuest, BotDigit, WebAccessibility.co, BidPilotPro, BairesDev, Kake, Squads, Ruby Labs, Improbable) + tracker/applied/rejected.
• Skip German/Dutch/Arabic-required; citizen/PR/local-rights-only; candidate-fee mills.

OUTPUT — Tier A→B→C:
| # | Tier | Company / Recruiter / Client | Role or ask | Geo / Mode | Posted | Eligibility quote + URL | Email (source URL) | Recruiter / founder (LI or page) | Job / brief link | Confidence | Next |

Tier A = published email + clear remote + visa/international.
Tier B = named recruiter/founder LinkedIn + clear eligibility (no email yet).
Tier C = clear eligibility + apply URL only (minimize).

End counts: discovered / contact-pages-checked / qualified / with email / named-recruiter / rejected(onsite-hybrid) / rejected(country-only or local-rights) / rejected(thin-SEO or no-contact) / expired / recycle-skipped.
One question: number → outreach / apply / skip. If dry on email → offer Depth B buyers or `/apply` on best Tier C.
```

---

## Depth G — Founder / Eng-Manager signal (Tier B first)

Use after Contact Deep Dive when Tier A emails are dry (US-auth / UK IR35 / AU-PR noise). Goal: **named humans + open demand**, then enrich email — not another ATS dump.

**Parallel (same day):** `/apply` or outreach on open Tier C backlog (Squads, Ruby Labs, Improbable, XCEED) so the search isn’t the only motion.

```text
/leads /lead-engine /linkedin-search /job-scraper
FOUNDER SIGNAL — Tier B first. Named founder / eng manager / in-house TA with a LIVE React-Next-TS ask. Max 6. Zero OK. Prefer humans over Apply buttons.

MISSION: Find people I can message for fully remote React / Next.js / TypeScript / full-stack SaaS work (visa OR remote-international). Emails are a bonus after the human is proven.

CANDIDATE: Senior/full-stack React–Next–TypeScript–Node, SaaS, remote collab, 5+ yrs.
GEOS: US CA UK IE NL DE AU NZ UAE EU/EEA + remote-international into those.

WORKPLACE (hard — fail closed):
• FULLY REMOTE only — skip onsite/hybrid.
• Keep only if remote AND (visa/will-sponsor for remote hire OR worldwide / from anywhere / overseas / international applicants).
• Country-only remote = DROP. LinkedIn: --remote remote; jobage ≤7 (prefer ≤3).

SIGNAL PIPELINE (order matters):
1) FOUNDER / ENG MANAGER POSTS — WebSearch + LinkedIn low-vol for “hiring” / “looking for” Senior React OR Next OR TypeScript OR full-stack (last 7d). Keep only when a *named person* is visible on a public post or company About/Team page (quote URL). Skip anonymous agency spam and peer freelancers selling capacity.
2) IN-HOUSE TA only — employer Talent/People posts for the company’s own React/Next role with eligibility quote. Skip US-auth-only, H-1B-transfer-only, UK Outside-IR35-without-overseas, AU PR/citizenship.
3) PRODUCT BUYER / STUDIO overflow — company /careers or blog “we’re hiring / contracting React” THIS WEEK on their domain. Enrich /contact for careers@ jobs@ hiring@ founders@ (literal only).
4) LIGHT JOB BACKFILL — Ashby/Greenhouse/Lever seeds only to unlock a named hiring manager or careers@ — never fill the table with apply-only rows if Tier B exists.
NO Remotive / YC dump / SEEK.

RULES:
• Prefer 3–6 Tier B (named human) over Tier C. Tier A if email appears on a quoted page.
• Never invent names or emails. If the poster is unnamed → drop or Tier C only.
• Thin SEO / placeholder contacts → drop.
• Dedup: preferences.md recycle + this week (Silence Laboratories, SwiftGuest, BotDigit, WebAccessibility.co, BidPilotPro, BairesDev, Kake, Squads, Ruby Labs, Improbable, Wizdaa, XCEED, LockedIn AI) + tracker/applied/rejected.
• Skip German/Dutch/Arabic-required; citizen/PR/local-rights-only; candidate-fee mills.

OUTPUT — Tier A→B→C:
| # | Tier | Company | Named human (role) | Ask / role | Geo / Mode | Posted | Eligibility quote + URL | Email (source URL) | Person / post URL | Job link | Confidence | Next |

End counts: discovered / humans-checked / qualified / with email / named-human / rejected(onsite-hybrid) / rejected(local-rights) / rejected(unnamed or thin-SEO) / expired / recycle-skipped.
One question: number → outreach / apply / skip. If dry → say saturated; clear Tier C backlog via `/apply` or rotate Depth D contract.
```

---

## Depth H — Fresh Pulse (≤72h listings + contract fork)

Use **after Founder Signal dry / 0–1 Tier A**. Goal: **new inventory only** — roles that appeared in the last **1–3 days** (hard cap 72h preferred; 7d only if ≤72h yields <3). Split brain: (A) permanent/full-time remote-int, (B) paid contract day-rate with named buyer. Do **not** re-hunt the same founder posts or this week’s companies.

**Parallel same day:** `/apply` LockedIn AI + Tier C backlog (Squads, Ruby Labs, Improbable, XCEED) so discovery isn’t the only motion.

```text
/leads /lead-engine /linkedin-search /job-scraper
FRESH PULSE — ≤72h first. Max 6. Zero OK. New inventory only — not last week’s humans/emails.

MISSION: Surface FULLY REMOTE React / Next.js / TypeScript / full-stack SaaS asks that appeared in the last 1–3 days and are remote-international / worldwide (visa OR from-anywhere / EOR). Prefer fresh listing text over recycled founder threads.

CANDIDATE: Senior/full-stack React–Next–TypeScript–Node, SaaS, remote collab, 5+ yrs.
GEOS: US CA UK IE NL DE AU NZ UAE EU/EEA + remote-international into those. Boost Nordics/CH/IE/NZ if ≤3d.

WORKPLACE (hard — fail closed):
• FULLY REMOTE only — skip onsite/hybrid.
• Keep only if remote AND (visa/will-sponsor for remote hire OR worldwide / from anywhere / overseas / international applicants).
• Country-only remote = DROP. LinkedIn: --remote remote; --jobage 1 then 3 (only widen to 7 if <3 keeps).

FRESHNESS PIPELINE (order matters — clock beats nostalgia):
1) LINKEDIN HYPER-FRESH — search Remote + React OR Next.js OR “full stack” TypeScript; jobage 1, then 3. Detail-fetch every keep. Quote exact eligibility sentence + posted date. Drop India-onsite mirrors, Kake/Blinq/BairesDev clones, hybrid “Remote” labels.
2) COMPANY DOMAIN ≤3d — WebSearch: “[Company] careers React OR Next.js hiring” + “posted” / “this week” on employer /careers /jobs (or their Greenhouse/Ashby/Lever). Prefer roles whose ATS/company page shows a publish date ≤3d. Quote employer URL (not aggregator mirrors). Enrich /contact for careers@ jobs@ hiring@ founders@ (literal only).
3) visa_discover — verified_in_listing only; keep fully remote; drop if first_seen/posted older than 7d when a date exists; prefer ≤3d.
4) CONTRACT FORK (fill 1–3 seats if FT dry) — UK/IE/NL/DE/AU/SE/DK/CH day-rate / Outside-IR35 / B2B React-Next-TS posted ≤5d with named recruiter OR published mailbox. Skip ZZP-local-only, German-required, SC-clearance, candidate-fee mills.
5) LIGHT ATS SEED — Ashby/Greenhouse/Lever only to unlock a ≤3d worldwide row or careers@ — never pad the table with stale apply-only recycle.
NO Remotive / YC dump / SEEK / re-present of this week’s shortlist.

INTELLIGENCE GATES:
• Freshness proof: every row needs a posted/first-seen date ≤3d (≤7d only if pulse dry) OR explicit “posted today/yesterday/this week” on company domain — else drop.
• Authenticity: thin SEO careers / placeholder contacts / unpaid equity-only → drop.
• Dedup: preferences.md recycle + this week (Silence Laboratories, SwiftGuest, BotDigit, WebAccessibility.co, BidPilotPro, BairesDev, Kake, Squads, Ruby Labs, Improbable, Wizdaa, XCEED, LockedIn AI, People Profilers / Tokyo Next.js client, Siena via Silver.dev) + tracker/applied/rejected + any company already messaged.
• Never invent names/emails. Unnamed apply-only → Tier C max 2, only if ≤72h + clear eligibility quote.

OUTPUT — Tier A→B→C (FT and Contract tagged in Ask column):
| # | Tier | Company | Named human (role) | Ask / role (FT or Contract) | Geo / Mode | Posted (age) | Eligibility quote + URL | Email (source URL) | Person / post URL | Job link | Confidence | Next |

End counts: discovered / detail-checked / qualified / ≤72h / ≤3d / with email / named-human / contract-rows / rejected(onsite-hybrid) / rejected(local-rights) / rejected(stale>7d) / rejected(unnamed or thin-SEO) / expired / recycle-skipped.
One question: number → outreach / apply / skip. If dry → say pulse empty; run `/apply` on LockedIn + backlog OR widen once to jobage 7 and stop.
```

---

## Depth I — Async Contract Markets (anti-IR35) + convert queue

Use **after Fresh Pulse dry (0–1 keeps)**. Stop re-running ≤72h FT LinkedIn — it is recycling India/hybrid/Kake. Switch inventory to **paid contractor / B2B / 1099 / async** markets that hire **overseas**, plus **Gulf + AU/NZ** remote-int. Mandate a **convert queue** in the same turn so discovery isn’t the only motion.

**Same-day convert (do first or in parallel):** `/apply` or outreach on open backlog — LockedIn AI, People Profilers (Lâm), Squads, Ruby Labs, Improbable, XCEED — before hunting more names.

```text
/leads /lead-engine /linkedin-search /job-scraper
ASYNC CONTRACT — overseas contractors first. Max 6. Zero OK. Skip UK Outside-IR35 “UK-based only” noise.

MISSION: Find FULLY REMOTE React / Next.js / TypeScript / full-stack paid contract or contractor seats that are remote-international / overseas contractors / worldwide B2B / 1099-from-anywhere. Prefer cash contracts over unpaid founding equity.

CANDIDATE: Senior/full-stack React–Next–TypeScript–Node, SaaS, remote collab, 5+ yrs. Overlap US ET/PT or AU/Gulf hours OK.
GEOS: US (contractor/1099/worldwide) · CA · AU · NZ · UAE · SA · QA · IE · NL · DE · Nordics/CH — only with overseas hire language. UK only if overseas/B2B-from-abroad is EXPLICIT (not “UK-based candidates only”).

WORKPLACE (hard — fail closed):
• FULLY REMOTE only — skip onsite/hybrid.
• Keep only if remote AND (visa for remote hire OR worldwide / from anywhere / overseas / international contractors OR “hire globally” / “async worldwide”).
• Country-only remote = DROP. LinkedIn: --remote remote; jobage ≤7 (prefer ≤5).

SIGNAL PIPELINE (order matters):
1) CONVERT QUEUE (list status, do not rediscover) — LockedIn AI · People Profilers/Tokyo Next.js · Squads · Ruby Labs · Improbable · XCEED. Mark each: apply / outreach / skip. Do not pad the new table with these.
2) US / GLOBAL CONTRACTOR — WebSearch + LinkedIn for “React OR Next.js OR TypeScript” + (contractor OR 1099 OR “independent contractor” OR “contract remote” OR “freelance contract”) + (worldwide OR “from anywhere” OR “international contractors” OR overseas). Detail-fetch; quote eligibility. Skip W2-US-auth-only and H-1B-transfer-only.
3) GULF + AU/NZ REMOTE-INT — company /careers or LinkedIn ≤7d for React/Next/TS fully remote with visa-sponsor OR overseas/international hire into AE/SA/QA/AU/NZ. Enrich careers@ jobs@ hiring@.
4) EU B2B OVERSEAS (not local-rights) — NL/DE/IE/Nordics/CH day-rate or B2B only when listing accepts non-local / overseas entity. Skip ZZP-NL-only, German-required, SC-clearance, UK Outside-IR35 without overseas.
5) STUDIO BUYERS (overflow) — product studios / digital agencies *hiring* React contractors into client delivery THIS WEEK (buyers of capacity, not Lemon-style vendor spam). Named human OR published mailbox required.
NO Remotive / YC dump / SEEK / Fresh Pulse re-run / Founder Signal re-run.

RULES:
• Prefer Tier A email + Tier B named recruiter/founder. Tier C apply-only max 2 and only with clear overseas quote ≤7d.
• Never invent contacts. Thin SEO / placeholder phones → drop.
• Dedup: preferences.md recycle + this week (Silence Laboratories, SwiftGuest, BotDigit, WebAccessibility.co, BidPilotPro, BairesDev, Kake, Squads, Ruby Labs, Improbable, Wizdaa, XCEED, LockedIn AI, People Profilers / Tokyo Next.js client, Siena via Silver.dev, AP US Tax Advisory, Collabify, Deel EMEA, Tether Keet, Search Atlas, Kraken) + tracker/applied/rejected.
• Skip peer freelancers selling capacity; candidate-fee mills; unpaid-until-raise.

OUTPUT — two blocks:
A) CONVERT QUEUE status table (backlog only).
B) NEW leads Tier A→B→C:
| # | Tier | Company | Named human (role) | Ask / role (Contract/FT) | Geo / Mode | Posted | Eligibility quote + URL | Email (source URL) | Person / post URL | Job link | Confidence | Next |

End counts: convert-queued / discovered / detail-checked / qualified / contract-rows / with email / named-human / rejected(onsite-hybrid) / rejected(UK-local-IR35 or local-rights) / rejected(unnamed or thin-SEO) / expired / recycle-skipped.
One question: number → outreach / apply / skip. If dry on NEW → finish convert queue only; stop discovering until tomorrow.
```

---

## Depth J — Unseen Boards Only (hard exclude applied/presented)

Use **after Async Contract** when the user says they already applied / don’t want repeats. Goal: **zero re-presentation**. Hunt inventory on surfaces Depth E–I barely touched: Teamtailor / Workable / Recruitee / Personio / BambooHR company boards, Shopify+React product roles, and UTC+3…+8 timezone buyers. Do **not** re-open LinkedIn jobage-1 dumps, HN Who’s Hiring November comments already scraped, or the convert queue.

**Before discover:** if any backlog item was applied, record `/outcome` — discovery is secondary tonight.

```text
/leads /lead-engine /linkedin-search /job-scraper
UNSEEN BOARDS — zero repeats. Max 6. Zero OK. If it appeared in Depth E–I or convert queue → DROP immediately.

HARD EXCLUDE (never table, never “near miss” as a keep):
Silence Laboratories, SwiftGuest, BotDigit, WebAccessibility.co, BidPilotPro, BairesDev, Kake, Squads, Ruby Labs, Improbable, Wizdaa, XCEED, LockedIn AI, People Profilers / Tokyo Next.js / Lâm Trịnh, Siena / Silver.dev, AP US Tax Advisory / Artur Polyak, Collabify / dejayy, Deel EMEA, Tether Keet, Search Atlas, Kraken, NOUS LATAM, MixRank, Proofline, Fluence, Lemon.io, Canonical, Blinq + full preferences.md recycle + tracker applied/rejected + any URL already in job_scraper/seen_jobs.json.

MISSION: Find NEW employers (not on the exclude list) hiring FULLY REMOTE React / Next.js / TypeScript / full-stack (or Shopify + React) via visa OR remote-international / worldwide / overseas / UTC+3–UTC+8 overlap hire.

CANDIDATE: Senior/full-stack React–Next–TypeScript–Node, SaaS, Shopify/Liquid bonus, remote collab, 5+ yrs.
GEOS: US CA UK IE NL DE AU NZ UAE EU/EEA + remote-international into those. Prefer buyers who name Asia / MENA / “any timezone” / UTC+5.

WORKPLACE (hard — fail closed): FULLY REMOTE only. Country-only remote = DROP. LinkedIn only as a seed, never the main table; if used: --remote remote, jobage ≤5, then reject any exclude-list company before detail.

SIGNAL PIPELINE (order matters — new surfaces first):
1) SECONDARY ATS SWEEP — WebSearch site:teamtailor.com OR site:jobs.workable.com OR site:*.recruitee.com OR site:*.personio.de OR site:bamboohr.com for React OR Next.js OR TypeScript OR “full stack” + (Remote OR Worldwide OR “from anywhere” OR “any country”). Prefer postings dated ≤7d. Quote employer board URL. Enrich /contact for careers@ jobs@ hiring@ founders@.
2) SHOPIFY + REACT PRODUCT BUYERS — company careers for Shopify Hydrogen / Liquid / Next storefront SaaS or e-comm product teams hiring remote-international THIS WEEK. Skip agency vendors selling Shopify freelancers.
3) TIMEZONE BUYERS — listings that literally say Asia / MENA / “UTC+3 to UTC+8” / “Pakistan” / “South Asia” / “hire globally async” for React-Next-TS. Company domain or their ATS only.
4) LIGHT visa_discover — verified_in_listing + fully remote only; DROP if company is on HARD EXCLUDE or URL already in seen_jobs.
5) NO: Remotive dump, YC WAAS dump, SEEK, Fresh Pulse re-run, Founder Signal re-run, Async Contract re-run, HN Who’s Hiring November re-scrape of posts already stored.

RULES:
• Company name + URL must be NEW vs HARD EXCLUDE and seen_jobs. When unsure → drop.
• Tier A email / Tier B named human preferred. Tier C apply-only max 2 only if ≤7d + clear overseas quote + not exclude.
• Never invent contacts. Thin SEO → drop.
• If discovery yields 0 NEW → say “unseen boards dry”; stop. Do not refill with old names. Suggest wait until tomorrow morning jobage-minutes pulse OR `/outcome` hygiene.

OUTPUT — Tier A→B→C NEW only:
| # | Tier | Company | Named human (role) | Ask / role | Geo / Mode | Posted | Eligibility quote + URL | Email (source URL) | Person / post URL | Job link | Confidence | Next |

End counts: discovered / exclude-hits-dropped / detail-checked / qualified / with email / named-human / rejected(onsite-hybrid) / rejected(local-rights) / rejected(repeat/seen) / rejected(thin-SEO) / expired.
One question: number → outreach / apply / skip. If 0 NEW → stop discovering; mark outcomes on applied backlog only.
```

---

## Depth K — Morning Minutes + AI-Native Product Teams

Use **after Unseen Boards (Depth J)** the next morning (or when user asks next strategy). Goal: catch **≤24h / jobage-minutes** inventory Depth J could not see, plus **AI-native / Claude Code / agentic** product teams hiring remote-international — a surface barely touched (Utorg was Russian-fail only). **Zero re-presentation** of Depth E–J keeps.

**Before discover:** record `/outcome` on anything applied from Benrey / Equitable Earth / Peratera / convert queue.

```text
/leads /lead-engine /linkedin-search /job-scraper
MORNING MINUTES + AI-NATIVE — zero repeats. Max 6. Zero OK. Depth E–J / convert / applied → DROP immediately.

HARD EXCLUDE (never table, never “near miss” as a keep):
Silence Laboratories, SwiftGuest, BotDigit, WebAccessibility.co, BidPilotPro, BairesDev, Kake, Squads, Ruby Labs, Improbable, Wizdaa, XCEED, LockedIn AI, People Profilers / Tokyo Next.js / Lâm Trịnh, Siena / Silver.dev, AP US Tax Advisory / Artur Polyak, Collabify / dejayy, Deel EMEA, Tether Keet, Search Atlas, Kraken, NOUS LATAM, MixRank, Proofline, Fluence, Lemon.io, Canonical, Blinq, Benrey, Equitable Earth, Peratera, Utorg, Syscov, Salmon Group, Opinov8, Over99, Globalli, eventfirst, Proxify, Lazer + full preferences.md recycle + tracker applied/rejected + any URL already in job_scraper/seen_jobs.json.

MISSION: Find NEW employers hiring FULLY REMOTE React / Next.js / TypeScript / full-stack via visa OR remote-international / worldwide / overseas / async / UTC+3–UTC+8. Prefer teams that ship with Claude Code / Cursor / Codex / agentic workflows (language must still be English — DROP required Russian/German/Arabic/Dutch).

CANDIDATE: Senior/full-stack React–Next–TypeScript–Node, SaaS, AI-augmented delivery (Claude Code by name when true), remote collab, 5+ yrs.
GEOS: US CA UK IE NL DE AU NZ UAE EU/EEA + remote-international into those.

WORKPLACE (hard — fail closed): FULLY REMOTE only. Country-only remote = DROP. LinkedIn = seed for freshness only, never pad the main table with US-auth or India-only noise.

SIGNAL PIPELINE (order matters — freshness + new angle first):
1) MORNING MINUTES — LinkedIn CLI: --remote remote, --jobage-minutes 180 (or --jobage 1 if minutes fail), queries: "React Next.js", "TypeScript full stack", "Next.js engineer". Cap ≤15. Detail-fetch only non-exclude + overseas quote. Drop hybrid/onsite/country-only before table.
2) AI-NATIVE PRODUCT CAREERS — WebSearch company /careers OR Greenhouse/Ashby/Lever/Teamtailor for (React OR Next.js OR TypeScript) + ("Claude Code" OR Cursor OR Codex OR "AI-native" OR agentic OR "AI coding agents") + (Remote OR Worldwide OR "from anywhere"). Prefer ≤7d. Quote eligibility. Enrich careers@ jobs@ hiring@ founders@.
3) GULF + AU/NZ PRODUCT (not agencies) — company careers THIS WEEK for React/Next/TS fully remote with visa-sponsor OR overseas/international hire into AE/SA/QA/AU/NZ. Skip staffing mills.
4) LIGHT visa_discover — verified_in_listing + fully remote only; DROP exclude-list / seen_jobs.
5) NO: Remotive/YC dump, SEEK, Teamtailor/Workable/Personio re-sweep of Depth J, Fresh Pulse / Founder Signal / Async Contract / Unseen Boards re-run, HN November re-scrape.

RULES:
• Company name + URL must be NEW vs HARD EXCLUDE and seen_jobs. When unsure → drop.
• Language Gate: required working language not in candidate Languages table → DROP (Utorg-class fail).
• Tier A email / Tier B named human preferred. Tier C apply-only max 2 only if ≤7d + clear overseas quote + not exclude.
• Never invent contacts. Thin SEO → drop.
• If 0 NEW → say “morning/AI-native dry”; stop. Do not refill with old names. Point to `/outcome` or wait for next Depth rotate.

OUTPUT — Tier A→B→C NEW only:
| # | Tier | Company | Named human (role) | Ask / role | Geo / Mode | Posted | Eligibility quote + URL | Email (source URL) | Person / post URL | Job link | Confidence | Next |

End counts: discovered / exclude-hits-dropped / detail-checked / qualified / with email / named-human / rejected(onsite-hybrid) / rejected(local-rights) / rejected(language) / rejected(repeat/seen) / rejected(thin-SEO) / expired.
One question: number → outreach / apply / skip. If 0 NEW → stop discovering; mark outcomes on applied backlog only.
```

---

## Depth L — Async / EOR Product Boards (no AI-native re-run)

Use **after Morning Minutes + AI-Native (Depth K)** when the user wants the next strategy with **zero repeats**. Goal: product SaaS / marketplace buyers that hire via **async**, **EOR**, **Deel/Remote.com**, or **contractor-from-anywhere** — not the Claude Code keyword sweep already done, not Teamtailor/Workable re-sweep, not LinkedIn minutes re-run.

**Before discover:** `/outcome` anything applied from Brainverse / Dataspecc / Qualitesoft / Jeda / Depth J keeps.

```text
/leads /lead-engine /linkedin-search /job-scraper
ASYNC / EOR PRODUCT BOARDS — zero repeats. Max 6. Zero OK. Depth E–K / convert / applied → DROP immediately.

HARD EXCLUDE (never table, never “near miss” as a keep):
Silence Laboratories, SwiftGuest, BotDigit, WebAccessibility.co, BidPilotPro, BairesDev, Kake, Squads, Ruby Labs, Improbable, Wizdaa, XCEED, LockedIn AI, People Profilers / Tokyo Next.js / Lâm Trịnh, Siena / Silver.dev, AP US Tax Advisory / Artur Polyak, Collabify / dejayy, Deel EMEA, Tether Keet, Search Atlas, Kraken, NOUS LATAM, MixRank, Proofline, Fluence, Lemon.io, Canonical, Blinq, Benrey, Equitable Earth, Peratera, Utorg, Syscov, Salmon Group, Opinov8, Over99, Globalli, eventfirst, Proxify, Lazer, Brainverse, Dataspecc, Qualitesoft, Jeda.ai / Dojoit, Arounda, Lexin, ClickHouse, Laine + full preferences.md recycle + tracker applied/rejected + any URL already in job_scraper/seen_jobs.json.

MISSION: Find NEW product employers (SaaS / marketplace / analytics / e-comm product — not staffing mills) hiring FULLY REMOTE React / Next.js / TypeScript / full-stack via visa OR remote-international / worldwide / overseas / async / EOR / Deel / Remote.com / “contractor from anywhere”.

CANDIDATE: Senior/full-stack React–Next–TypeScript–Node, SaaS dashboards, remote async collab, 5+ yrs. Mentoring OK; do not invent Lead titles.
GEOS: US CA UK IE NL DE AU NZ UAE EU/EEA + remote-international into those.

WORKPLACE (hard — fail closed): FULLY REMOTE only. Country-only remote = DROP. English working language required; DROP required Russian/German/Arabic/Dutch/Ukrainian. LinkedIn seed only if needed for ≤3d freshness — never pad table with India/US-auth noise.

SIGNAL PIPELINE (order matters — new angle first):
1) ASYNC / EOR PRODUCT CAREERS — WebSearch company /careers OR Greenhouse/Ashby/Lever boards for (React OR Next.js OR TypeScript OR “full stack”) + (async OR “async-first” OR EOR OR Deel OR “Remote.com” OR “hire anywhere” OR “contractor worldwide” OR “from any country”) + Remote. Prefer ≤7d. Quote eligibility. Enrich careers@ jobs@ hiring@ founders@.
2) GREENHOUSE / ASHBY / LEVER PRODUCT ONLY — light `visa_discover` OR targeted board search; keep verified_in_listing OR clear worldwide/EOR quote; DROP exclude-list / seen_jobs / AI-native keyword re-hits already presented (Brainverse/Dataspecc-class).
3) AU/NZ/GULF PRODUCT (EOR or visa remote) — company careers THIS WEEK for React/Next/TS fully remote with sponsorship OR overseas/EOR into AE/SA/QA/AU/NZ. Skip relocate-to-onsite packs.
4) NO: Remotive/YC dump, SEEK, Teamtailor/Workable/Personio Depth J re-sweep, Morning Minutes re-run, AI-native “Claude Code” keyword re-sweep, Fresh Pulse / Founder Signal / Async Contract / Unseen Boards re-run, HN November re-scrape.

RULES:
• Company name + URL must be NEW vs HARD EXCLUDE and seen_jobs. When unsure → drop.
• Prefer product companies over agencies selling capacity. Agency buyer of capacity only if named role + published mailbox + overseas quote.
• Tier A email / Tier B named human preferred. Tier C apply-only max 2 only if ≤7d + clear overseas/EOR quote + not exclude.
• Never invent contacts. Thin SEO → drop.
• If 0 NEW → say “async/EOR boards dry”; stop. Do not refill with old names. Point to `/outcome` or next Depth rotate.

OUTPUT — Tier A→B→C NEW only:
| # | Tier | Company | Named human (role) | Ask / role | Geo / Mode | Posted | Eligibility quote + URL | Email (source URL) | Person / post URL | Job link | Confidence | Next |

End counts: discovered / exclude-hits-dropped / detail-checked / qualified / with email / named-human / rejected(onsite-hybrid) / rejected(local-rights) / rejected(language) / rejected(repeat/seen) / rejected(thin-SEO) / expired.
One question: number → outreach / apply / skip. If 0 NEW → stop discovering; mark outcomes on applied backlog only.
```

---

## Depth M — Dual-Proof Warm Path (ultra bar)

Use **after Async/EOR (Depth L)** when the user wants next strategy with **zero repeats** and a higher intelligence bar. Goal: every keep must pass **dual proof** — (1) live employer-domain or owned ATS role with an explicit remote-international / visa / worldwide / overseas / EOR quote, **and** (2) a **published** `careers@`/`jobs@`/`hiring@`/`founders@` **or** a named founder/eng-manager/recruiter on a public company page. Single-signal Tier C apply-only is capped at **1** and only if ≤3d + crystal-clear overseas quote.

**Do not** re-run AI-native keyword sweeps, Teamtailor dumps, LinkedIn minutes, or async/EOR keyword hunts already exhausted. Prefer **company `/careers` first**, then targeted Ashby/Greenhouse/Lever **product** boards, then light `visa_discover` as seed only.

**Before discover:** `/outcome` on anything applied from Georion / Tailor / Remote People / Depth K–J backlog.

```text
/leads /lead-engine /linkedin-search /job-scraper
DUAL-PROOF WARM PATH — ultra bar. Max 5. Zero OK. Depth E–L / convert / applied → DROP immediately.

HARD EXCLUDE (never table, never “near miss” as a keep):
Silence Laboratories, SwiftGuest, BotDigit, WebAccessibility.co, BidPilotPro, BairesDev, Kake, Squads, Ruby Labs, Improbable, Wizdaa, XCEED, LockedIn AI, People Profilers / Tokyo Next.js / Lâm Trịnh, Siena / Silver.dev, AP US Tax Advisory / Artur Polyak, Collabify / dejayy, Deel (any), Tether Keet, Search Atlas, Kraken, NOUS LATAM, MixRank, Proofline, Fluence, Lemon.io, Canonical, Blinq, Benrey, Equitable Earth, Peratera, Utorg, Syscov, Salmon Group, Opinov8, Over99, Globalli, eventfirst, Proxify, Lazer, Brainverse, Dataspecc, Qualitesoft, Jeda.ai / Dojoit, Arounda, Lexin, ClickHouse, Laine, Georion, Tailor, Remote People / RemotePeople, aicente, Toggl, Dispensed, Fueled, Praktika, NextMatch, Wobbit, Virmondo, Sphere Labs + full preferences.md recycle + tracker applied/rejected + any URL already in job_scraper/seen_jobs.json.

MISSION: Find NEW product SaaS / marketplace / analytics / e-comm employers hiring FULLY REMOTE React / Next.js / TypeScript / full-stack — only when DUAL PROOF passes (remote-int / worldwide / EOR or Path B visa/reloc).

DUAL PROOF (both required for Tier A/B; Tier C max 1 if (1) alone and ≤3d):
(1) ELIGIBILITY — quote on employer domain or owned ATS: visa sponsorship for remote OR worldwide / from anywhere / overseas / international / EOR / Deel / Remote.com / hire globally / any country. Country-only remote = FAIL.
(2) CONTACT — literal published email (careers@ jobs@ hiring@ founders@ hello@ join@) with source URL, OR named human (founder / eng manager / recruiter) on a public About/Team/Careers/Press page with person URL.

CANDIDATE: Senior/full-stack React–Next–TypeScript–Node, SaaS dashboards, remote collab, 5+ yrs. English working language only — DROP required RU/DE/AR/NL/UKR.
GEOS: US CA UK IE NL DE AU NZ UAE EU/EEA + remote-international into those.

WORKPLACE (hard — fail closed): FULLY REMOTE only. Onsite/hybrid = DROP. LinkedIn ≤3d remote seed only to discover NEW company names — never pad table with India/US-auth noise; detail-fetch then dual-proof or drop.

SIGNAL PIPELINE (order matters — company-site intelligence first):
1) COMPANY CAREERS SWEEP — WebSearch `"careers" OR "/jobs"` + (React OR Next.js OR TypeScript) + (SaaS OR marketplace OR dashboard) + (worldwide OR "from anywhere" OR "any country" OR EOR OR "will sponsor" OR overseas) for THIS WEEK. Prefer employer domain URLs. WebFetch /careers /contact /about /team. Quote eligibility + harvest email/named human.
2) OWNED ATS PRODUCT BOARDS — Ashby/Greenhouse/Lever company boards (not aggregators) for React/Next/TS fully remote with overseas/visa/EOR quote ≤7d. Enrich contact on company domain (not invent). DROP if company on HARD EXCLUDE or already in seen_jobs.
3) LIGHT visa_discover — keep only verified_in_listing + fully remote + dual-proof enrichment possible; else drop.
4) OPTIONAL LinkedIn seed — --remote remote --jobage 3, queries React/Next/TS, cap 10; use only as company-name seed for step 1–2.
5) NO: Remotive/YC dump, SEEK, Depth J ATS re-sweep, Morning Minutes re-run, Claude Code keyword re-sweep, Async/EOR keyword re-sweep, Fresh Pulse / Founder Signal / HN November re-scrape.

RULES:
• Company + URL must be NEW vs HARD EXCLUDE and seen_jobs. Unsure → drop.
• Prefer product companies. Agencies only if dual-proof + they are buying capacity into client delivery THIS WEEK (not selling freelance seats).
• Thin SEO / fake testimonials / 404 contact → drop.
• Conflicting sources (e.g. Ashby “worldwide” vs YC “US visa only”) → FLAG in Confidence; do not sell as High.
• If 0 NEW → say “dual-proof dry”; stop. Do not refill with old names. Suggest `/outcome` hygiene or wait for next morning pulse.

OUTPUT — Tier A→B→C NEW only (prove both columns):
| # | Tier | Company | Named human (role) | Ask / role | Geo / Mode | Posted | Eligibility quote + URL | Email (source URL) | Person / post URL | Job link | Dual-proof (✓/✗) | Confidence | Next |

End counts: discovered / exclude-hits-dropped / detail-checked / dual-proof-pass / dual-proof-fail / qualified / with email / named-human / rejected(onsite-hybrid) / rejected(local-rights) / rejected(language) / rejected(repeat/seen) / rejected(thin-SEO) / expired.
One question: number → outreach / apply / skip. If 0 NEW → stop discovering; mark outcomes on applied backlog only.
```

---

## Depth N — Manager-Post → Dual-Proof (named-human first)

Use **after Dual-Proof Warm Path (Depth M)** when company-careers + ATS sweeps are thin. Goal: flip the discovery vector — start from **named humans already posting “hiring”** (founder / eng manager / recruiter) in the last **7 days**, then dual-proof their **employer-domain or owned ATS** role. Contact proof is often free; eligibility still must be quoted. Keeps Depth M’s dual-proof bar; does **not** re-run careers keyword sweeps, AI-native, Teamtailor, async/EOR, or LinkedIn job-search padding.

**Before discover:** `/outcome` Cyrolo / Propr if applied; mark Genki (freshness-skip) / bluepina (contact-fail) as skip if not already.

```text
/leads /lead-engine /linkedin-search /job-scraper
MANAGER-POST → DUAL-PROOF — named-human first. Max 5. Zero OK. Depth E–M / convert / applied → DROP immediately.

HARD EXCLUDE (never table, never “near miss” as a keep):
Silence Laboratories, SwiftGuest, BotDigit, WebAccessibility.co, BidPilotPro, BairesDev, Kake, Squads, Ruby Labs, Improbable, Wizdaa, XCEED, LockedIn AI, People Profilers / Tokyo Next.js / Lâm Trịnh, Siena / Silver.dev, AP US Tax Advisory / Artur Polyak, Collabify / dejayy, Deel (any), Tether Keet, Search Atlas, Kraken, NOUS LATAM, MixRank, Proofline, Fluence, Lemon.io, Canonical, Blinq, Benrey, Equitable Earth, Peratera, Utorg, Syscov, Salmon Group, Opinov8, Over99, Globalli, eventfirst, Proxify, Lazer, Brainverse, Dataspecc, Qualitesoft, Jeda.ai / Dojoit, Arounda, Lexin, ClickHouse, Laine, Georion, Tailor, Remote People / RemotePeople, aicente, Toggl, Dispensed, Fueled, Praktika, NextMatch, Wobbit, Virmondo, Sphere Labs, Cyrolo, Propr, Genki / Staygenki, bluepina, WAct / WAConversionTracking + full preferences.md recycle + tracker applied/rejected + any URL already in job_scraper/seen_jobs.json.

MISSION: Find NEW product SaaS / marketplace / analytics / e-comm employers where a **named hiring human** posted ≤7d that they are hiring React / Next.js / TypeScript / full-stack — then prove the company hire remote-international (visa OR worldwide / from anywhere / EOR).

DUAL PROOF (both required for Tier A/B; Tier C max 1 if eligibility alone and post ≤3d):
(1) ELIGIBILITY — quote on employer domain or owned ATS: visa sponsorship for remote OR worldwide / from anywhere / overseas / international / EOR / Deel / Remote.com / hire globally / any country. Country-only remote = FAIL.
(2) CONTACT — the posting human counts IF their public post/About/Team URL is quoted (founder / eng manager / recruiter). Prefer also a published careers@/jobs@/hiring@/hello@/join@ when present.

CANDIDATE: Senior/full-stack React–Next–TypeScript–Node, SaaS dashboards, remote collab, 5+ yrs. English working language only — DROP required RU/DE/AR/NL/UKR.
GEOS: US CA UK IE NL DE AU NZ UAE EU/EEA + remote-international into those.

WORKPLACE (hard — fail closed): FULLY REMOTE only. Onsite/hybrid = DROP.

SIGNAL PIPELINE (order matters — human signal first):
1) MANAGER / FOUNDER POSTS ≤7d — WebSearch + XSearch for posts: ("hiring" OR "we're hiring" OR "open role") + (React OR "Next.js" OR TypeScript OR "full-stack" OR "fullstack") + (remote OR worldwide OR "from anywhere" OR EOR) + (founder OR "engineering manager" OR CTO OR "head of eng"). Keep only posts that name a **real company** + **named human**. Quote post URL. Cap 15 seeds.
2) COMPANY CONVERT — for each seed company: WebFetch /careers /jobs + owned Ashby/Greenhouse/Lever/Workable board. Require a still-open React/Next/TS/full-stack role. Quote eligibility. Harvest mailbox if published. DROP if HARD EXCLUDE / seen_jobs / thin SEO / no open role.
3) LIGHT visa_discover — only as company-name seed if post pipeline dry; keep verified_in_listing + fully remote + dual-proof enrichment; else drop.
4) NO LinkedIn job-search padding (Depth M already burned India/US-auth noise). LinkedIn **people/post** URLs from WebSearch are OK as person proof — do not scrape people-search result pages.
5) NO: Remotive/YC dump, SEEK, Depth J–L keyword re-sweeps, Dual-Proof careers re-sweep, Morning Minutes, Claude Code keyword re-sweep, HN November re-scrape, Cyrolo/Propr/Genki re-table.

RULES:
• Company + URL must be NEW vs HARD EXCLUDE and seen_jobs. Unsure → drop.
• Prefer product companies. Agencies only if dual-proof + buying capacity THIS WEEK (not selling seats).
• Post without a live matching role on company/ATS → drop (signal ≠ demand until role exists).
• Conflicting sources → FLAG Confidence; do not sell as High.
• If 0 NEW → say “manager-post dry”; stop. Do not refill with Depth M names. Suggest `/apply` Cyrolo/Propr or `/outcome` hygiene.

OUTPUT — Tier A→B→C NEW only:
| # | Tier | Company | Named human (role) | Ask / role | Geo / Mode | Posted | Eligibility quote + URL | Email (source URL) | Person / post URL | Job link | Dual-proof (✓/✗) | Confidence | Next |

End counts: discovered / exclude-hits-dropped / detail-checked / dual-proof-pass / dual-proof-fail / qualified / with email / named-human / rejected(onsite-hybrid) / rejected(local-rights) / rejected(language) / rejected(repeat/seen) / rejected(thin-SEO) / rejected(post-no-role) / expired.
One question: number → outreach / apply / skip. If 0 NEW → stop discovering; convert Cyrolo/Propr or mark outcomes only.
```

---

## Depth O — Demand Graph (listings finished / non-board power mode)

Use when the user says **listings finished**, **boards dry**, **make agent more powerful**, or after **Depth N manager-post dry**. Job aggregators and repeat career sweeps are exhausted — hunt **demand that is not a recycled listing**: buyer briefs, vertical product companies with live `/careers`, changelog/hire announcements, and **new** owned-ATS slugs. Keep dual-proof for Tier A/B. Zero OK.

**Do not** re-run Depth E–N pipelines the same day. Convert Cyrolo/Propr first if still open and not applied.

```text
/leads /lead-engine /linkedin-search /job-scraper
DEMAND GRAPH — listings finished / non-board power mode. Max 6. Zero OK. Depth E–N / convert / applied → DROP immediately.

HARD EXCLUDE (never table):
Silence Laboratories, SwiftGuest, BotDigit, WebAccessibility.co, BidPilotPro, BairesDev, Kake, Squads, Ruby Labs, Improbable, Wizdaa, XCEED, LockedIn AI, People Profilers / Tokyo Next.js / Lâm Trịnh, Siena / Silver.dev, AP US Tax Advisory / Artur Polyak, Collabify / dejayy, Deel (any), Tether Keet, Search Atlas, Kraken, NOUS LATAM, MixRank, Proofline, Fluence, Lemon.io, Canonical, Blinq, Benrey, Equitable Earth, Peratera, Utorg, Syscov, Salmon Group, Opinov8, Over99, Globalli, eventfirst, Proxify, Lazer, Brainverse, Dataspecc, Qualitesoft, Jeda.ai / Dojoit, Arounda, Lexin, ClickHouse, Laine, Georion, Tailor, Remote People / RemotePeople, aicente, Toggl, Dispensed, Fueled, Praktika, NextMatch, Wobbit, Virmondo, Sphere Labs, Cyrolo, Propr, Genki / Staygenki, bluepina, WAct / WAConversionTracking, Flaredog, Quayutec + full preferences.md recycle + tracker applied/rejected + any URL already in job_scraper/seen_jobs.json.

MISSION: Find NEW React / Next.js / TypeScript / full-stack demand from product SaaS / marketplace / analytics / adtech / e-comm buyers (Path A remote-int / worldwide / EOR or Path B visa/reloc) — WITHOUT leading on Remotive, LinkedIn job-search padding, or re-sweeps of Depth E–N keywords.

DUAL PROOF (Tier A/B both required; Tier C max 1 if eligibility alone ≤3d):
(1) ELIGIBILITY — employer domain or owned ATS quote: visa for remote OR worldwide / from anywhere / overseas / international / EOR / Deel / Remote.com / hire globally / any country. Country-only remote = FAIL.
(2) CONTACT — published careers@/jobs@/hiring@/founders@/hello@/join@ (quote URL) OR named founder/eng-manager/recruiter on About/Team/Press/post (quote person URL).

CANDIDATE: Senior/full-stack React–Next–TypeScript–Node, SaaS dashboards, remote collab, 5+ yrs. English only — DROP required RU/DE/AR/NL/UKR.
GEOS: US CA UK IE NL DE AU NZ UAE EU/EEA + remote-international into those.
WORKPLACE: FULLY REMOTE only. Onsite/hybrid = DROP.

SIGNAL PIPELINE (order matters — non-board first):
1) BUYER BRIEFS ≤7d — WebSearch for product-company demand (NOT job boards): ("looking for" OR "need a" OR "seeking") + (React OR "Next.js" OR "full-stack" OR TypeScript) + (contractor OR freelance OR "remote engineer" OR "for our product" OR "our SaaS") + (founder OR CTO OR "engineering manager"). Keep only when company is named + human named. Cap 12 seeds. Convert via /careers.
2) VERTICAL COMPANY-SITE HUNT (Plai-adjacent) — WebSearch THIS WEEK: (adtech OR "advertising analytics" OR "SaaS dashboard" OR marketplace OR "e-commerce platform") + (careers OR "/jobs") + (React OR "Next.js" OR TypeScript) + (worldwide OR "from anywhere" OR EOR OR "will sponsor" OR overseas). Prefer *.com/careers employer domains. WebFetch /careers /contact /about /team. Quote eligibility + harvest email/named human.
3) CHANGELOG / HIRE ANNOUNCEMENTS ≤14d — WebSearch ("we're hiring" OR "joined as" OR "growing the eng team" OR "engineering blog") + (React OR Next.js) + (remote OR worldwide) on company blogs — then find the live role on their ATS. Post without open role = drop.
4) NEW OWNED-ATS SLUGS — discover Ashby/Greenhouse/Lever/Workable boards for companies NOT in HARD EXCLUDE / seen_jobs (search "jobs.ashbyhq.com" OR "boards.greenhouse.io" OR "jobs.lever.co" + React + remote + worldwide). Detail-check ≤8. Dual-proof or drop.
5) LIGHT visa_discover — verified_in_listing + fully remote + dual-proof enrichment only; else drop. Cap 20.
6) NO: Remotive/YC dump, SEEK, LinkedIn job-search padding, Depth J–N re-runs, Dual-Proof careers re-sweep, Manager-Post re-run, Morning Minutes, Claude Code keyword re-sweep, HN November re-scrape, Cyrolo/Propr/Genki/Flaredog re-table.

RULES:
• Prefer product companies. Agencies only if they are BUYING capacity into client delivery THIS WEEK (overflow), with dual-proof — never seat-sellers (Lemon/Fluence/Proxify class).
• Thin SEO / fake testimonials / 404 contact → drop.
• Unpaid / equity-only cofounder → drop.
• Conflicting sources → FLAG Confidence.
• If 0 NEW → say “demand-graph dry”; STOP. Convert Cyrolo/Propr via `/apply` or `/outcome` only — do not invent a fifth listing sweep.

OUTPUT — Tier A→B→C NEW only:
| # | Tier | Company | Named human (role) | Ask / role | Geo / Mode | Posted | Eligibility quote + URL | Email (source URL) | Person / post URL | Job link | Dual-proof (✓/✗) | Signal source | Confidence | Next |

End counts: discovered / exclude-hits-dropped / detail-checked / dual-proof-pass / dual-proof-fail / qualified / with email / named-human / rejected(onsite-hybrid) / rejected(local-rights) / rejected(language) / rejected(repeat/seen) / rejected(thin-SEO) / rejected(unpaid) / rejected(agency-seller) / expired.
One question: number → outreach / apply / skip. If 0 NEW → convert Cyrolo (1) / Propr (2) or `/outcome` hygiene only.
```

---

## Depth P — Sponsored Mobility (remote-first; onsite/hybrid only with visa/relocation)

Use **after Demand Graph (Depth O)** or when the user opens **onsite/hybrid with sponsorship**. Workplace rule flip vs Depth E–O: prefer remote-international; **also keep** onsite/hybrid **only** when the listing quotes **visa sponsorship** and/or **relocation**. No sponsor/relocate quote → remote-only gate (same as before). Zero repeats of Depth E–O keeps.

**Before discover:** prefer convert Signals / InsightIQ / Cyrolo / Propr if not applied.

```text
/leads /lead-engine /linkedin-search /job-scraper
SPONSORED MOBILITY — remote-first; onsite/hybrid only with visa OR relocation. Max 6. Zero OK. Depth E–O / convert / applied → DROP immediately.

HARD EXCLUDE (never table):
Silence Laboratories, SwiftGuest, BotDigit, WebAccessibility.co, BidPilotPro, BairesDev, Kake, Squads, Ruby Labs, Improbable, Wizdaa, XCEED, LockedIn AI, People Profilers / Tokyo Next.js / Lâm Trịnh, Siena / Silver.dev, AP US Tax Advisory / Artur Polyak, Collabify / dejayy, Deel (any), Tether Keet, Search Atlas, Kraken, NOUS LATAM, MixRank, Proofline, Fluence, Lemon.io, Canonical, Blinq, Benrey, Equitable Earth, Peratera, Utorg, Syscov, Salmon Group, Opinov8, Over99, Globalli, eventfirst, Proxify, Lazer, Brainverse, Dataspecc, Qualitesoft, Jeda.ai / Dojoit, Arounda, Lexin, ClickHouse, Laine, Georion, Tailor, Remote People / RemotePeople, aicente, Toggl, Dispensed, Fueled, Praktika, NextMatch, Wobbit, Virmondo, Sphere Labs, Cyrolo, Propr, Genki / Staygenki, bluepina, WAct / WAConversionTracking, Flaredog, Quayutec, Signals / Recruit With Signals, InsightIQ / DataWize + full preferences.md recycle + tracker applied/rejected + any URL already in job_scraper/seen_jobs.json.

MISSION: Find NEW React / Next.js / TypeScript / full-stack product SaaS / marketplace / analytics / adtech / e-comm roles via Path A remote-int / worldwide / EOR or Path B:
  Path A — FULLY REMOTE + (visa for remote OR worldwide / from anywhere / overseas / EOR / hire globally), OR
  Path B — ONSITE or HYBRID in target geos ONLY when listing quotes visa sponsorship AND/OR relocation support.

WORKPLACE GATE (fail closed):
• Remote without overseas/visa path → DROP (country-only remote = FAIL).
• Onsite/hybrid without “will sponsor” / “visa sponsorship” / “relocation” / “relocation package” quote → DROP.
• Prefer Path A in ranking; Path B is additive inventory, not a replacement for remote.

DUAL PROOF (Tier A/B both; Tier C max 1 if eligibility alone ≤3d):
(1) ELIGIBILITY — quote Path A or Path B language on employer domain or owned ATS.
(2) CONTACT — published careers@/jobs@/hiring@/founders@/hello@/join@ (URL) OR named founder/eng-manager/recruiter on About/Team/Press (person URL).

CANDIDATE: Senior/full-stack React–Next–TypeScript–Node, SaaS dashboards, 5+ yrs. English only — DROP required RU/DE/AR/NL/UKR.
GEOS: US CA UK IE NL DE AU NZ UAE EU/EEA (+ remote-international into those; Path B relocate into those).

SIGNAL PIPELINE:
1) PATH A — REMOTE-INT / EOR ≤7d — company /careers + owned Ashby/Greenhouse/Lever/Workable: React/Next/TS + worldwide/from anywhere/EOR/overseas. Dual-proof enrich. Cap seeds 12.
2) PATH B — VISA/RELOCATE ONSITE·HYBRID ≤14d — WebSearch + visa_discover verified_in_listing: (React OR Next.js OR TypeScript OR “full stack”) + (sponsor OR “will sponsor” OR “visa sponsorship” OR relocation) + (hybrid OR onsite OR “office” OR city in target geos). Quote the sponsorship/relocation sentence. DROP if quote missing. Cap 10 detail-checks.
3) LINKEDIN — Path A: `--remote remote --jobage 7` cap 10 (company-name seed only). Path B: **no** `--remote` filter, query `React OR Next.js visa OR sponsor OR relocation`, `--jobage 7`, cap 10; detail-fetch; keep only if sponsorship/relocation quote survives.
4) LIGHT visa_discover — keep verified_in_listing; split into Path A (remote) vs Path B (onsite/hybrid + sponsor/relocate). Dual-proof or drop. Cap 25.
5) NO: Remotive/YC dump, SEEK, Depth E–O re-runs, Demand Graph keyword re-sweep, Signals/InsightIQ/Cyrolo/Propr re-table.

RULES:
• Prefer product companies. Agencies only if buying overflow THIS WEEK + dual-proof.
• Thin SEO / unpaid cofounder / 404 contact → drop.
• Path B: must be willing to relocate (user accepts) — mark Mode = Onsite+Visa or Hybrid+Visa/Relocate in table.
• Conflicting sources → FLAG Confidence.
• If 0 NEW → say “sponsored-mobility dry”; convert Signals/InsightIQ/Cyrolo/Propr or `/outcome` only.

OUTPUT — Tier A→B→C NEW only:
| # | Tier | Company | Named human (role) | Ask / role | Path (A remote / B onsite·hybrid) | Geo / Mode | Posted | Eligibility quote + URL | Email (source URL) | Person / post URL | Job link | Dual-proof (✓/✗) | Confidence | Next |

End counts: discovered / exclude-hits-dropped / detail-checked / dual-proof-pass / dual-proof-fail / path-A / path-B / qualified / with email / named-human / rejected(onsite-hybrid-no-sponsor) / rejected(local-rights) / rejected(language) / rejected(repeat/seen) / rejected(thin-SEO) / expired.
One question: number → outreach / apply / skip. If 0 NEW → convert backlog only.
```

---

## Depth Q — Sponsor Hub Cities (Path B–primary after Depth P)

Use **after Sponsored Mobility (Depth P)** when Path A remote-int was dry but Path B hybrid/onsite+visa produced keeps (Omnea, STRATOS). Do **not** re-run Path A keyword sweeps or Depth P. Invert energy: **Path B first** in sponsor hub cities; Path A is a tiny additive check only.

**Before discover:** convert Omnea FE Lead + STRATOS Product Engineer (and Signals / InsightIQ / Cyrolo / Propr) if not applied.

```text
/leads /lead-engine /linkedin-search /job-scraper
SPONSOR HUB CITIES — Path B primary (hybrid/onsite + visa OR relocation on owned ATS). Path A additive only (cap 5). Max 6. Zero OK.
Depth E–P / Omnea / STRATOS / Borderless / Manex / convert / applied → DROP immediately.

HARD EXCLUDE (never table):
Omnea, STRATOS / STRATOS Technologies, Borderless, Manex AI, SaaSify Labs, GetLaunchDay, Remanence, Nebius, Silence Laboratories, SwiftGuest, BotDigit, WebAccessibility.co, BidPilotPro, BairesDev, Kake, Squads, Ruby Labs, Improbable, Wizdaa, XCEED, LockedIn AI, People Profilers / Tokyo Next.js / Lâm Trịnh, Siena / Silver.dev, AP US Tax Advisory / Artur Polyak, Collabify / dejayy, Deel (any), Tether Keet, Search Atlas, Kraken, NOUS LATAM, MixRank, Proofline, Fluence, Lemon.io, Canonical, Blinq, Benrey, Equitable Earth, Peratera, Utorg, Syscov, Salmon Group, Opinov8, Over99, Globalli, eventfirst, Proxify, Lazer, Brainverse, Dataspecc, Qualitesoft, Jeda.ai / Dojoit, Arounda, Lexin, ClickHouse, Laine, Georion, Tailor, Remote People / RemotePeople, aicente, Toggl, Dispensed, Fueled, Praktika, NextMatch, Wobbit, Virmondo, Sphere Labs, Cyrolo, Propr, Genki / Staygenki, bluepina, WAct / WAConversionTracking, Flaredog, Quayutec, Signals / Recruit With Signals, InsightIQ / DataWize, Owen Thomas, Doctolib, Clera, CanadaVisa, HUD, Interfere + full preferences.md recycle + tracker applied/rejected + any URL already in job_scraper/seen_jobs.json.

MISSION: Find NEW React / Next.js / TypeScript / full-stack product SaaS roles via Path A remote-int / worldwide / EOR or Path B:
  Path B (PRIMARY) — ONSITE or HYBRID in hub cities ONLY when employer-domain or owned Ashby/Greenhouse/Lever/Teamtailor quotes visa sponsorship AND/OR relocation (≤10d posted).
  Path A (ADDITIVE, cap 5 seeds) — FULLY REMOTE + worldwide/from anywhere/EOR/overseas/remote visa — only if dual-proof falls in the lap; do not burn the run on Path A.

HUB CITIES (Path B only): London, Berlin, Amsterdam, Dublin, Munich, Zurich, Toronto, Vancouver, NYC, SF / Bay Area, Sydney, Auckland, Dubai, Stockholm, Copenhagen, Helsinki.
Stack must be React OR Next.js OR TypeScript full-stack (not iOS-only / ML-only / pure backend-Go).

WORKPLACE GATE (fail closed):
• Path B without literal “will sponsor” / “visa sponsorship” / “relocation” / “relocation package” on employer domain or owned ATS → DROP (Arbeitnow/Relocate.me/EUVisaJobs alone = FAIL).
• Posted date >10d for Path B → DROP (stale Borderless-class miss).
• Path A country-only remote → DROP.
• Required DE/NL/AR/RU/UKR → DROP.

DUAL PROOF (Tier A/B; Tier C max 1 if ≤3d + crystal Path B quote):
(1) ELIGIBILITY — quote sponsor/relocate sentence from employer domain or owned ATS URL.
(2) CONTACT — published careers@/jobs@/hiring@/hello@/join@/talent@ (URL) OR named founder/CTO/VP Eng/recruiter on About/Team/Press (person URL).

CANDIDATE: Senior/full-stack React–Next–TypeScript–Node, SaaS dashboards, 5+ yrs. English only.

SIGNAL PIPELINE:
1) PATH B HUBS ≤10d — WebSearch + LinkedIn (NO --remote): query `(React OR Next.js OR TypeScript OR "full stack") (visa OR sponsor OR relocation) (Hybrid OR Onsite)` scoped to hub cities; detail-fetch; keep only if owned-ATS/employer quote survives. Cap 12 detail-checks.
2) OWNED ATS SWEEP — Ashby/Greenhouse/Lever company boards in hubs with React/Next/TS + sponsor/relocate in body. Cap 10 boards.
3) LIGHT visa_discover — keep verified_in_listing AND workplace onsite/hybrid AND stack match; require employer/owned-ATS dual-proof (Arbeitnow = seed only). Cap 20.
4) PATH A TINY — at most 5 remote-int dual-proof seeds if they appear; do not expand.
5) NO: Remotive/YC dump, SEEK, Depth E–P re-runs, Path A keyword re-sweep, Demand Graph re-sweep, Omnea/STRATOS/Borderless/Manex/Signals/InsightIQ/Cyrolo/Propr re-table.

RULES:
• Prefer product SaaS over agencies; agencies only if buying overflow THIS WEEK + dual-proof.
• Thin SEO / unpaid cofounder / 404 contact → drop.
• Mark Mode = Hybrid+Visa or Onsite+Visa/Relocate.
• Conflicting sources → FLAG Confidence.
• If 0 NEW → say “sponsor-hubs dry”; next run = **Depth R Listing Navigator** (or convert Omnea/STRATOS/Signals/InsightIQ/Cyrolo/Propr).

OUTPUT — Tier A→B→C NEW only:
| # | Tier | Company | Named human (role) | Ask / role | Path (B hub / A remote) | Geo / Mode | Posted | Eligibility quote + URL | Email (source URL) | Person / post URL | Job link | Dual-proof (✓/✗) | Confidence | Next |

End counts: discovered / exclude-hits-dropped / detail-checked / dual-proof-pass / dual-proof-fail / path-A / path-B / qualified / with email / named-human / rejected(onsite-hybrid-no-sponsor) / rejected(aggregator-only) / rejected(stale>10d) / rejected(local-rights) / rejected(language) / rejected(repeat/seen) / rejected(thin-SEO) / expired.
One question: number → outreach / apply / skip. If 0 NEW → convert backlog only.
```

---

## Depth R — Listing Navigator (super search after Q dry)

Use when Depth Q returned **0 NEW**, or the user says **listings empty / agent not finding jobs / make searching better / navigator**. This is a **methodology upgrade**, not another keyword re-sweep of Depth Q.

**Why Q failed (fix):** LinkedIn noise without owned-ATS quotes; eligibility on Ashby but contact harvest stopped at `support@`; Tier C window too tight (≤3d); no near-miss log so runs looked “empty” when they weren’t.

**Navigator doctrine (non-negotiable):**
1. **Company → owned ATS → eligibility → contact ladder** (never stop at LinkedIn alone).
2. **Contact ladder before dual-proof-fail** — Imprint / Contact / Careers FAQ / Press / About-Team / Ashby “questions before applying” / founder LinkedIn from Press or company LinkedIn About. Only then mark contact-fail.
3. **Near-miss log required** — always show 1–5 near-misses (eligibility ✓ contact ✗, or stale, or wrong hub) so the run is auditable.
4. **Tier C expanded** — crystal Path A/B eligibility on owned ATS ≤7d + apply URL may table as Tier C (max 2) even without email/named human.
5. **Seed diversity** — rotate hubs; prefer companies *not* already in `seen_jobs` this week.

**Before discover:** convert Omnea / STRATOS / Signals / InsightIQ / Cyrolo / Propr if not applied.

```text
/leads /lead-engine /linkedin-search /job-scraper
LISTING NAVIGATOR — company→ATS→contact ladder. Max 6 NEW + near-miss log. Zero OK but near-misses REQUIRED.
Depth E–Q / Omnea / STRATOS / Borderless / Manex / Retell / convert / applied → DROP from NEW table.

HARD EXCLUDE (never table as NEW):
Retell / Retell AI, Omnea, STRATOS / STRATOS Technologies, Borderless, Manex AI, SaaSify Labs, GetLaunchDay, Remanence, Nebius, Fidamy, Silence Laboratories, SwiftGuest, BotDigit, WebAccessibility.co, BidPilotPro, BairesDev, Kake, Squads, Ruby Labs, Improbable, Wizdaa, XCEED, LockedIn AI, People Profilers / Tokyo Next.js / Lâm Trịnh, Siena / Silver.dev, AP US Tax Advisory / Artur Polyak, Collabify / dejayy, Deel (any), Tether Keet, Search Atlas, Kraken, NOUS LATAM, MixRank, Proofline, Fluence, Lemon.io, Canonical, Blinq, Benrey, Equitable Earth, Peratera, Utorg, Syscov, Salmon Group, Opinov8, Over99, Globalli, eventfirst, Proxify, Lazer, Brainverse, Dataspecc, Qualitesoft, Jeda.ai / Dojoit, Arounda, Lexin, ClickHouse, Laine, Georion, Tailor, Remote People / RemotePeople, aicente, Toggl, Dispensed, Fueled, Praktika, NextMatch, Wobbit, Virmondo, Sphere Labs, Cyrolo, Propr, Genki / Staygenki, bluepina, WAct / WAConversionTracking, Flaredog, Quayutec, Signals / Recruit With Signals, InsightIQ / DataWize, Owen Thomas, Doctolib, Clera, CanadaVisa, HUD, Interfere, EMBL-EBI / European Bioinformatics Institute + full preferences.md recycle + tracker applied/rejected + any URL already in job_scraper/seen_jobs.json.

MISSION: Find NEW React / Next.js / TypeScript / full-stack product SaaS roles via Path A (remote-int/EOR/worldwide) OR Path B (hub hybrid/onsite + visa OR relocation on owned ATS).

NAVIGATOR PIPELINE (run in order — do not skip steps):
1) SEED COMPANIES (cap 20 names) — LinkedIn hub searches (London, Berlin, Amsterdam, Dublin, Munich, SF Bay, Toronto, Sydney, Stockholm) `--jobage 7` query `React OR Next.js OR "full stack" OR TypeScript` — collect **company names only** (drop agencies/recruiters). Also WebSearch `site:jobs.ashbyhq.com OR site:boards.greenhouse.io (React OR "Next.js") ("visa sponsorship" OR relocation OR "work from anywhere" OR worldwide) 2026` — company names only. Dedup vs exclude/seen.
2) OPEN OWNED ATS (cap 15 boards) — for each seed, open `jobs.ashbyhq.com/<slug>` / Greenhouse / Lever / Teamtailor / careers subdomain. List React/Next/TS/full-stack roles. Record `datePosted`. Drop >14d Path B / >7d Path A.
3) ELIGIBILITY GATE — quote Path A or Path B sentence from that ATS/employer page. Aggregator-only = FAIL. Cap 12 detail-checks.
4) CONTACT LADDER (mandatory before fail) — for every eligibility pass, hunt in order until one hits:
   a) careers@ / jobs@ / hiring@ / hello@ / join@ / talent@ / people@ on Contact/Careers/Imprint
   b) Ashby/Greenhouse “questions? email …” on any role on same board
   c) Named founder / CEO / CTO / VP Eng / Talent Lead on About/Team/Press with person URL (LinkedIn OK if public)
   d) Company LinkedIn About / Featured with named exec + profile link
   If a–d all miss → near-miss (eligibility ✓ contact ✗), may still Tier C if ≤7d.
5) PATH A SWEEP (additive, cap 8 seeds) — remote + worldwide/from anywhere/EOR/overseas on product company ATS; same contact ladder.
6) LIGHT visa_discover (cap 20) — verified_in_listing seed → step 2–4 only (Arbeitnow never eligibility alone).
7) NO: Remotive/YC dump, SEEK, Depth E–Q keyword re-runs, Retell/Omnea/STRATOS re-table.

WORKPLACE GATE: same as Depth P/Q (fail closed). English only — DROP required DE/NL/AR/RU/UKR.
HUBS Path B: London, Berlin, Amsterdam, Dublin, Munich, Zurich, Toronto, Vancouver, NYC, SF/Bay, Sydney, Auckland, Dubai, Stockholm, Copenhagen, Helsinki.

TIERS:
• A = eligibility ✓ + published hiring email
• B = eligibility ✓ + named human URL
• C = eligibility ✓ + apply URL only, posted ≤7d (max 2 rows)
Near-misses (eligibility ✓ contact ✗ and not tabled as C) go in NEAR-MISS LOG only.

OUTPUT:
### NEW (Tier A→B→C)
| # | Tier | Company | Named human | Ask/role | Path | Geo/Mode | Posted | Eligibility quote+URL | Email (URL) | Person URL | Job link | Dual-proof | Confidence | Next |

### NEAR-MISS LOG (required even if 0 NEW)
| Company | Role | Why missed | Fix next |

End counts: seeds / boards-opened / detail-checked / eligibility-pass / contact-ladder-pass / dual-proof-pass / dual-proof-fail / path-A / path-B / Tier-C / near-misses / rejected(*) …
One question: number → outreach / apply / skip. If 0 NEW → convert backlog OR run contact-ladder only on near-miss #N.
```

---

## Depth S — Parametric Board Sweep (more parameters after R)

Use when Depth R returned **0 NEW** (or only waiver/near-miss salvage), contact-ladder already ran, and the user wants **more listings / better search / more parameters / Depth S** — without re-pasting O–R keyword sweeps.

**Why R under-yielded (fix):** single LinkedIn query; Ashby/Greenhouse-only WebSearch; Path A geo-locks (EU-only) counted as misses not seeds; Personio/Teamtailor/Workable slugs under-tried; no `jobage-minutes` / 48h pulse; visa✓+stale roles died without a separate “sponsor-watch” near-miss band.

**Before discover:** convert Omnea / STRATOS / Cyrolo / Propr if not applied. Faction outreach is salvage-only (recycle) — do not re-table as NEW.

```text
/leads /lead-engine /linkedin-search /job-scraper
PARAMETRIC BOARD SWEEP (Depth S) — multi-query + multi-ATS. Max 8 NEW + near-miss log. Zero OK but near-misses REQUIRED.
Depth E–R / Faction / Stream Staff Backend / Cloover Staff / a16z-speedrun Stealth / Omnea / STRATOS / Retell / convert / applied → DROP from NEW.

HARD EXCLUDE: full Depth R exclude list + Faction, Cloover, Stream (GetStream Staff Backend Amsterdam), a16z-speedrun Stealth SR006, Reflection, Profound Frontend, Air Apps, Brainial, Brightflag, Twenty, DualEntry London Backend + preferences.md recycle + tracker + seen_jobs URLs.

MISSION: NEW React / Next.js / TypeScript / full-stack **product SaaS** via Path A OR Path B. English only.

### PARAMETER MATRIX (run all — do not skip rows)
| Param | Values |
|-------|--------|
| Stack queries (rotate) | (1) `React OR Next.js` (2) `"full stack" OR fullstack TypeScript` (3) `"frontend engineer" React` (4) `"product engineer" React OR Next` |
| Path A LI | `-l Remote --remote remote --jobage 7` AND one pass `--jobage 3` AND one `--jobage-minutes 2880` (48h). Queries add: `worldwide OR "from anywhere" OR EOR OR overseas OR "work from anywhere"` |
| Path B LI | hubs: London, Berlin, Amsterdam, Dublin, Munich, Zurich, Toronto, Vancouver, NYC, SF Bay, Sydney, Auckland, Dubai, Stockholm, Copenhagen, Helsinki, Lisbon, Vienna, Paris (English-only filter). `--jobage 14`. Query add: `visa OR sponsorship OR relocation OR "Skilled Worker" OR "will sponsor"` |
| ATS WebSearch sites | `jobs.ashbyhq.com` · `boards.greenhouse.io` · `jobs.lever.co` · `jobs.teamtailor.com` · `*.jobs.personio.com` OR `jobs.personio.de` · `apply.workable.com` · `jobs.smartrecruiters.com` |
| ATS eligibility terms | `"visa sponsorship" OR relocation OR "work from anywhere" OR worldwide OR "from anywhere" OR EOR OR "hire internationally" OR overseas OR "Skilled Worker" OR "relocation package" OR "IND" OR "open to relocation"` |
| Vertical company-site | WebSearch `"careers" OR "/jobs" (React OR "Next.js") (SaaS OR "product engineer") (2026) (remote OR visa OR relocation)` — open employer domain only |
| visa_discover | `--limit 30` · keep `verified_in_listing` → owned ATS step only (Arbeitnow never eligibility alone) |
| Caps | seeds 30 companies · boards-opened 25 · detail-checks 18 · Path A additive seeds 12 · NEW table max 8 · Tier C max 2 |

### PIPELINE
1) SEED from Path A LI + Path B LI + ATS WebSearch + vertical careers — company names only; drop agencies/recruiters; dedup exclude/seen.
2) OPEN owned ATS (Ashby/GH/Lever/Teamtailor/Personio/Workable/SmartRecruiters/careers subdomain). Record `datePosted`. Path A drop >10d; Path B drop >14d.
3) ELIGIBILITY — quote Path A/B sentence from **owned** page. Aggregator-only = FAIL.
4) CONTACT LADDER a–d (same as Depth R) before dual-proof-fail.
5) SPONSOR-WATCH LOG (not NEW): eligibility ✓ + contact ✓/✗ but `datePosted` 15–90d — max 5 rows for user waiver later. Do not count as NEW.
6) NO Remotive/YC dump; NO Depth E–R re-paste; NO Faction/Cloover/Stream-AMS/a16z-stealth re-table.

WORKPLACE GATE: Depth P/Q fail-closed. DROP required DE/NL/AR/RU/UKR. DROP US-citizen-only / “no sponsorship” without remote-international.

TIERS: A = email+eligibility · B = named human+eligibility · C = apply-only eligibility still-open (max 3 when A+B thin; undated OK if Conf. med).

OUTPUT:
### NEW (Tier A→B→C)
| # | Tier | Company | Named human | Ask/role | Path | Geo/Mode | Posted | Eligibility quote+URL | Email (URL) | Person URL | Job link | Dual-proof | Confidence | Next |

### SALVAGE (only if NEW empty — max 2)
| # | Company | Role | Why salvage | Email/Person | Job link | Next |

### NEAR-MISS LOG (required)
| Company | Role | Why missed | Fix next |

### SPONSOR-WATCH (optional, ≤5, not NEW)
| Company | Role | Posted | Visa/reloc quote | Contact? | Waiver? |

End counts: seeds / boards / details / elig-pass / contact-pass / dual-pass / dual-fail / path-A / path-B / Tier-C / salvage / near-miss / sponsor-watch / rejected(*) / query-matrix-cells-run …
One question: number → outreach / apply / skip / convert. If 0 NEW+salvage → Convert Day (stop inventing Depths the same day).
```

---

## Convert Day (after Depth S dry — same day only)

Use when Depth S returned **0 NEW** (near-miss / Sponsor-Watch OK). **No new discovery.** No Depth T. No O–S re-paste.

**Priority order:** (1) `/apply` or `/outcome` on open backlog still not applied — Omnea FE Lead, STRATOS Product Engineer, Signals, InsightIQ, Cyrolo, Propr (skip if already applied/rejected/closed). (2) Optional **Sponsor-Watch outreach/apply** from the last S table (e.g. Scope AI ≤90d Path B, Seamflow FE/MTS) — drafts `send_approved: false`. (3) `/leads review` / `/outcome` hygiene only.

**Tomorrow (optional re-entry):** Morning Minutes / Fresh Pulse ≤24h **or** re-check Sponsor-Watch ages — do **not** invent a new Depth letter until convert + outcomes are clean.

```text
CONVERT DAY — no discovery. Depth S was 0 NEW.

HARD RULES: no WebSearch hunting, no LinkedIn matrix, no visa_discover, no Remotive/YC, no Depth O–S re-paste, no Depth T.

DO IN ORDER:
1) List open backlog not yet applied/rejected (River AI Product Engineer; Propellerhead Senior SWE NZ; Anthropic Business Tech London; CEA Software Engineer salvage; Wheely London/Nicosia Sponsor-Watch; prior Path A/B Supabase/Aries/Aurora/Discord/Nexcess/Ruya if still open + tracker “to apply”).
2) For each: confirm URL still open → `/apply <url>` OR `/outcome <id> --status skipped|applied|rejected` with one-line note.
3) Optional same turn: outreach/apply on Sponsor-Watch from last Depth S only — quote visa line + founder LI; drafts send_approved false.
4) OUTPUT: Convert table | # | Company | Role | Action taken | URL | Blocker if any |
One question: next backlog # → apply / outreach / skip / stop until tomorrow.
```

---

## Zero-Repeat Worldwide (next discovery after Convert Day)

Use **tomorrow** (or after convert is clean) when the user says worldwide search keeps returning the **same listings**. Goal: **only never-seen employers/URLs**. Empty NEW is success if everything searched was a repeat.

```text
ZERO-REPEAT WORLDWIDE — React/Next/TS SaaS Path A remote-int OR Path B visa/reloc. Max 6 NEW. Zero OK.

MISSION: Find listings that have NEVER appeared in this workspace. Worldwide internet search is allowed ONLY as a seed — every hit must pass the repeat gate before NEW.

HARD DROP (do not put in NEW / near-miss-as-fresh / “found again”):
• ANY url OR company+title already in job_scraper/seen_jobs.json
• ANY company+role in job_search_tracker.csv (applied/drafted/rejected)
• Full preferences.md recycle blocklist
• Entire Convert Day + Depth S Sponsor-Watch set: Omnea, STRATOS, Signals, InsightIQ, Cyrolo, Propr, Scope AI/Getscope, Seamflow, Casavi, Metaview, Conduct, Aiomic, Optimal, Re-Leased, ClearGrid, Outset, nano
• Depth E–R hard excludes: Faction, Cloover, Stream Staff Backend AMS, a16z-speedrun Stealth, Reflection, Profound FE, Air Apps, Brainial, Brightflag, Twenty, DualEntry, Retell, Borderless, Manex, Fidamy, HUD, …
• Aggregator mirrors of the above (Arbeitnow / Remotive / freehire / LinkedIn guest pointing at same Ashby/GH/Lever UUID)

REPEAT GATE (mandatory before NEW table):
1) Collect seeds ≤30 from LI (jobage 1–3 only) + owned ATS + company /careers — not Remotive/YC dumps.
2) Write candidates JSON → python tools/scrape_state.py candidates --results <file>
3) Keep ONLY selected[]. already_seen / already_applied / repeated_in_batch = DROP (count as dropped_as_repeat).
4) Extra: if company name matches recycle OR was in yesterday’s Convert/Sponsor-Watch → DROP even if URL is new slug for same employer this week.

ELIGIBILITY: Path A remote-int/EOR/worldwide OR Path B hub + quoted visa/reloc. English only.
OUTPUT: NEW table (0–6) + NEAR-MISS (eligibility fail only — NOT repeats) + End counts: seeds / selected / dropped_as_repeat / elig-pass / NEW.
If dropped_as_repeat ≥ 80% of seeds → say “worldwide saturated with repeats”; stop; do not invent Depth T; suggest convert leftover # or wait ≤24h Fresh Pulse.
One question: number → outreach / apply / skip.
```

---

## After Zero-Repeat dry (0 NEW — same day / next morning)

Zero-Repeat found **new URLs** but **0 Path A/B elig-pass**. Do **not** invent Depth T or re-paste O–S / Zero-Repeat the same day.

**Priority:**
1. **Convert leftover** (same day) — Elile → Supabase → older Cyrolo/Propr/STRATOS/InsightIQ/Omnea if still open.
2. **Next morning — Fresh Minutes Zero-Repeat** (≤24h / jobage-minutes) — paste below. Not a full worldwide re-sweep.
3. Only if convert is clean **and** Fresh Minutes dry → Async/EOR contractor overseas (Depth L style) **tomorrow+**, still with scrape_state gate.

```text
CONVERT LEFTOVER — no discovery.
Apply or /outcome only (skip if already applied/closed):
1) Elile AI — Senior Front-end Engineer — https://www.elile.ai/careers/senior-front-end-engineer
2) Supabase — Developer Relations Engineer — https://jobs.ashbyhq.com/supabase/26f7817d-ca92-4094-a2b5-f22e07a218c4
Then older backlog if still open: Cyrolo → Propr → STRATOS → InsightIQ → Omnea.
After each apply: /outcome <company> with status applied.
One question: # → apply / outreach / skip / stop.
```

```text
FRESH MINUTES ZERO-REPEAT — ≤24h only. Max 5 NEW. Zero OK.

HARD DROP: full preferences recycle + Convert/Sponsor-Watch set (Omnea STRATOS Signals InsightIQ Cyrolo Propr Scope Seamflow Casavi Metaview Conduct …) + ALL urls/company+title in seen_jobs + tracker.
FAKE-REMOTE DROP: "within the U.S." / "US only" / "Remote - United States" / "Fully Remote (US)" / "U.S. Based" / country-only remote — even if WWR says Worldwide.

PIPELINE:
1) Prefer volume pulse if not run today: python tools/board_scrape.py --limit 20 --since 2d  (Hiring Cafe via APIFY_TOKEN). Else LinkedIn: -l Remote --remote remote --jobage-minutes 180 (fallback --jobage 1). Queries: React OR Next.js | "full stack" TypeScript | "product engineer" React. Cap seeds ≤20.
2) Optional: 3 Path B hubs only (London Berlin Amsterdam) --jobage 1 + visa|sponsorship|relocation — cap ≤10.
3) scrape_state.py candidates → keep selected[] only; count dropped_as_repeat.
4) Detail only selected; Path A remote-int/EOR/worldwide OR Path B hub+visa/reloc; English only. Engine path_filter fake-remote applies on --path-ab volume runs.
5) NO WebSearch worldwide dump, NO Remotive/YC, NO Zero-Repeat full re-paste, NO Depth O–S.

OUTPUT: NEW 0–5 + NEAR-MISS (elig fail only) + counts (seeds / dropped_as_repeat / elig-pass / NEW).
If 0 NEW → stop discovery; convert leftover (Elile → Supabase) or /outcome only until next calendar day.
One question: number → outreach / apply / skip.
```

---

## Classic lanes (use only if Depth A–D dry)

| Lane | When |
|------|------|
| 1 Visa scrape | `/job-scraper` verified_in_listing 7d |
| 2 YC Will-sponsor | Explicit open role + Will sponsor — **not** bare WAAS “[Hiring]” |
| 5 Contract | Day-rate EU/UK/AU |
| 6 Gulf/AU/NZ | Visa or remote-int |
| 7 Direct contact | Email/phone on company pages only |
| 8 Fresh ≤3d | Nordics/CH/IE/NZ window |

---

## After a good hit
- Number → `outreach` or `/apply <url>`
- Mark company into recycle / `/outcome` after apply or reject

## Weekly hygiene

```text
/leads review shortlist — drop Tier D and anything already emailed/rejected/closed; export remaining Tier A emails only
```
