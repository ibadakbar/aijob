# SUPER PROMPT — Ibad Akbar (paste under `/leads`)

One paste. Agent auto-routes. You do not pick flags.

Copy everything inside the fence below.

```text
/leads
SUPER PIPELINE — do everything. Auto-route. Only NEW. Max 8. Never invent email/phone. No Depth T same day after Convert.

WHO I AM (load CLAUDE.md + leads/preferences.md + 01-candidate-profile.md):
- Ibad Akbar · Karachi, PK · 5+ yrs Full Stack · React / Next.js / TypeScript / Node · SaaS
- Target geos: US CA UK IE NL DE AU NZ EU/EEA UAE SA QA CH SE FI DK PK + remote that hires into those
- Prefer fully remote. Onsite/hybrid ONLY with quoted visa sponsorship and/or relocation into target geo
- English OK. DROP required German/Dutch/Arabic as working language
- Windows: use python not python3

════════════════════════════════════════
HARD RULES (never break)
════════════════════════════════════════
1) Never invent leads, emails, phones, budgets, or “I reviewed your site”
2) Never send email/LI/applications — drafts send_approved:false until I say send
3) Rank Tier A > B > C; bury Tier D. Intent EXPLICIT_DEMAND > STRONG_SIGNAL > POTENTIAL_FIT
4) Funding/launch alone ≠ lead unless demand_proven or Tier A/B contact
5) Prefer tools/leads_cli.py + visa_discover/board_scrape + LinkedIn CLI + owned ATS WebFetch
6) Skip peer freelancers / white-label vendors selling capacity (not buyers)
7) Fake-remote DROP: "within the U.S." / "US only" / "Remote - United States" / "Fully Remote (US)" / "U.S. Based" / country-only remote (UK/AU/CA-only) even if feed says Worldwide
8) ZERO-REPEAT: DROP if URL or company+title in seen_jobs.json OR tracker OR preferences recycle OR Convert/Sponsor-Watch this week OR aggregator mirror of same ATS UUID. Run: python tools/scrape_state.py candidates --results <file> → keep selected[] only; count dropped_as_repeat
9) Email/phone only if literally on a public page — quote source URL. Tier A mailboxes: careers@ jobs@ hiring@ hello@ join@ talent@ people@ founders@ (support@/info@ alone ≠ Tier A unless labeled hiring)
10) Remotive/YC = seeds only — never main table if ≥40% recycle

PATH A (remote): worldwide / from anywhere / hire globally / overseas / EOR / remote visa sponsorship
PATH B (onsite/hybrid): quoted will sponsor / visa sponsorship / relocation support / relocation package into target geo
Freshness default: Path A ≤10d · Path B ≤14d · undated+still open owned ATS → Tier C OK (Conf. med)
Navigator-strict when on Depth R: Path A ≤7d
Phone optional. Cap NEW 3–8 (+ salvage ≤2 if NEW empty). Tier C ≤3 when A+B thin. Sponsor-Watch ≤5 (elig ✓, posted 15–90d, not NEW)

OUTPUT always:
### NEW (Tier A→B→C) | ### SALVAGE (if NEW empty) | ### NEAR-MISS (required if dry) | ### SPONSOR-WATCH (≤5) | End counts
One question: # → outreach / apply / skip / convert
After every apply reminder: /outcome <company>

CONVERT BACKLOG (always keep ready — confirm still open before /apply):
1) Elile — Senior Front-end — https://www.elile.ai/careers/senior-front-end-engineer
2) Supabase — DevRel — https://jobs.ashbyhq.com/supabase/26f7817d-ca92-4094-a2b5-f22e07a218c4
3) Flexport — SWE II Autonomous Supply Chains AMS (if still open) — https://job-boards.greenhouse.io/flexport/jobs/8393237
4) Optional: Picnic SW1/SW2 if I waive freshness · Termius Desktop if still open
Older if still open: Cyrolo → Propr → STRATOS → InsightIQ → Omnea · Orbii/Ruya/IntelSQ already shown today = not re-NEW

════════════════════════════════════════
AUTO-ROUTER (pick ONE mode this turn — do not stack O→S unless I stack)
════════════════════════════════════════
IF I said nothing / find leads / best / today’s / worldwide / warm / deep / authentic
  → MODE: DAILY BEST LEADS

IF I said zero-repeat / no repeats / same listings / worldwide keeps repeating
  → MODE: ZERO-REPEAT WORLDWIDE

IF I said fresh minutes / after zero-repeat / next strategy morning
  → MODE: FRESH MINUTES ZERO-REPEAT (≤24h)

IF I said convert / backlog / after Depth S dry
  → MODE: CONVERT DAY (no discovery)

IF I said Depth R / navigator / listings empty / agent not finding
  → MODE: DEPTH R Listing Navigator

IF I said Depth S / more parameters / parametric / multi-ATS / after R dry
  → MODE: DEPTH S Parametric Board Sweep

IF I said visa / relocation / onsite / hybrid / sponsored mobility
  → MODE: DEPTH P (then stop; wait for my next turn for Q)

IF I said sponsor hubs / Path B primary / hub cities / after P
  → MODE: DEPTH Q

IF I said listings finished / Demand Graph / more powerful
  → MODE: DEPTH O

IF I said apply + URL → hand off /apply <url> (fit eval first)
IF I said outreach + id → tools/leads_cli.py outreach <id>
IF I said outcome + id → tools/leads_cli.py outcome …

Default when unclear: DAILY BEST LEADS

════════════════════════════════════════
MODE: DAILY BEST LEADS
════════════════════════════════════════
1) python tools/board_scrape.py --limit 30 --since 7d
   (or visa_discover --volume --path-ab --since 14d --new-only --limit 40)
   Keep verified_in_listing for Path proof; Arbeitnow never eligibility alone
2) If volume thin: LI Path A -l Remote --remote remote --jobage-minutes 2880 (cap 8)
   + Path B 2–3 hubs London+Berlin+Amsterdam --jobage 14 + visa|reloc (cap 8). Drop agencies
3) WebSearch owned ATS: ashby / greenhouse / lever / teamtailor / personio / workable + Path A/B terms
4) scrape_state candidates → selected only
5) Detail elig-pass; contact ladder; Tier A/B then C≤3; salvage≤2 if dry; Sponsor-Watch≤5
6) If 0 NEW + salvage empty → suggest ONE Depth R OR Convert Day — NOT full O→S same turn
7) Cap 1 discovery turn/day when saturated; rest = convert + /outcome

════════════════════════════════════════
MODE: DEPTH R — Listing Navigator
════════════════════════════════════════
Company → owned ATS → contact ladder. Path A ≤7d worldwide/EOR OR Path B ≤14d visa|reloc.
Seeds ≤30 · boards ≤25 · details ≤18 · NEW max 8 · Tier C max 2 on Navigator
Contact ladder a–d before dual-proof-fail. Near-miss REQUIRED if dry. Zero-repeat hard.
If 0 NEW → offer Depth S OR Convert Day (not O→S stack)

════════════════════════════════════════
MODE: DEPTH S — Parametric Board Sweep
════════════════════════════════════════
Multi-query + multi-ATS matrix (PROMPT_PACK Depth S). Path A ≤10d / Path B ≤14d.
Stack queries rotate: React OR Next.js | "full stack" TypeScript | "frontend engineer" React | "product engineer" React OR Next
ATS sites: ashby · greenhouse · lever · teamtailor · personio · workable · smartrecruiters
Sponsor-Watch ≤5. Near-miss REQUIRED. Max 8 NEW.
If 0 NEW+salvage → CONVERT DAY only. No Depth T.

════════════════════════════════════════
MODE: ZERO-REPEAT WORLDWIDE
════════════════════════════════════════
Only never-seen employers/URLs. Seeds ≤30 from LI jobage 1–3 + owned ATS + /careers — not Remotive/YC dumps.
scrape_state candidates mandatory. Empty NEW OK if everything was repeat.
If dropped_as_repeat ≥80% of seeds → say “worldwide saturated”; stop; convert leftover or wait ≤24h Fresh Minutes. No Depth T.

════════════════════════════════════════
MODE: FRESH MINUTES ZERO-REPEAT
════════════════════════════════════════
≤24h only. Max 8 NEW (user override; else 5).
1) Prefer: python tools/board_scrape.py --limit 20 --since 2d
   Else LI: -l Remote --remote remote --jobage-minutes 180 (fallback --jobage 1)
   Queries: React OR Next.js | "full stack" TypeScript | "product engineer" React · seeds ≤20
2) Optional Path B: London Berlin Amsterdam --jobage 1 + visa|sponsorship|relocation · cap ≤10
3) scrape_state → selected only · detail · Path A/B · English · fake-remote DROP
4) NO WebSearch worldwide dump, NO Remotive/YC, NO O→S, NO Depth T
If 0 NEW → CONVERT LEFTOVER only until next calendar day

════════════════════════════════════════
MODE: CONVERT DAY (no discovery)
════════════════════════════════════════
HARD: no WebSearch hunting, no LI matrix, no visa_discover, no Remotive/YC, no Depth O–S, no Depth T
1) Confirm backlog URLs still open
2) Table: # | Company | Role | Status | URL | Blocker | Action
3) Optional Sponsor-Watch waive → apply
4) One question: # → /apply / outreach / skip / stop
After submit: /outcome <company> --status applied

════════════════════════════════════════
MODE: DEPTH P / Q / O (only when named)
════════════════════════════════════════
Run exact prompt from leads/PROMPT_PACK.md for that Depth. One Depth per turn.
P = sponsored mobility · Q = sponsor hub cities Path B dual-proof · O = Demand Graph non-board buyers

════════════════════════════════════════
END — RUN NOW
════════════════════════════════════════
Detect my intent from this message (or default Best Leads). Execute that ONE mode fully.
Present tables. One next-action question. Remind /outcome after applies.
```

---

## Tiny shortcuts (optional)

| You type | Agent runs |
|----------|------------|
| `/leads` | Best Leads (super default) |
| `/leads convert` | Convert Day only |
| `/leads zero-repeat` | Zero-Repeat Worldwide |
| `/leads fresh minutes` | Fresh Minutes ≤24h |
| `/leads Depth R` | Navigator |
| `/leads Depth S` | Parametric sweep |
| `/leads` + paste **SUPER PIPELINE** block above | Full auto-router |

## After a hit
1. Reply `1` / `1+2` → `/apply` those URLs  
2. `/outcome <company>` after you submit  
3. Next day → `/leads` or Fresh Minutes — not another Depth letter the same night Convert ran
