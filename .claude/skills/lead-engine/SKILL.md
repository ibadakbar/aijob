---
name: lead-engine
description: >
  Best-Leads-first finder: board_scrape/--volume (+ Hiring Cafe) then light
  LinkedIn 48h + owned ATS + contact ladder; fake-remote DROP; adapters are
  seeds only. Yield-smart: Path A ≤10d / Path B ≤14d,
  Tier C ≤3 when A/B thin, salvage ≤2 if NEW empty, phone optional. When Best
  Leads dry, escalates Demand Graph (O) → Sponsored Mobility (P) → Sponsor Hub
  Cities (Q) → Listing Navigator (R) → Parametric Board Sweep (S) — one Depth
  per turn unless user stacks. Ranks Tier A (email) > B (founder LinkedIn) > C
  (apply URL); prefers 3–8 authentic hireable signals over Remotive/YC dumps.
  Triggers on: /leads, find leads, best leads, today's leads, deep leads,
  authentic leads, warm leads, demand graph, listings finished, navigator,
  listings empty, more parameters, find more listings, Depth S, parametric,
  multi-ATS, sponsor hubs, Path B, find clients, find contracts, freelance,
  outreach, visa, YC, Remotive, Arbeitnow, worldwide leads
allowed-tools: Read, Write, Edit, Glob, Grep, WebFetch, WebSearch, AskUserQuestion, Bash(python tools/leads_cli.py:*), Bash(python3 tools/leads_cli.py:*)
---

# Lead Engine (Best Leads + Depth Intelligence)

User writes what they need. You run `.claude/commands/leads.md` — do not make them choose CLI flags.

**Default for vague “find leads” / “best leads”:** Best Leads Mode (`preferences.md` + Daily Best Leads in `PROMPT_PACK.md`). Not Remotive/YC dumps. Not same-day O→S.

## Source of truth

- Defaults / playbook: `leads/preferences.md` (Best Leads Mode + listings-saturated / Demand Graph)
- Paste prompts: `leads/PROMPT_PACK.md` (Daily Best Leads first; Depth A–S; **Depth O** when boards dry; **Depth Q** after P; **Depth R** when Q dry; **Depth S** after R / more parameters)
- Profile: `.claude/skills/job-application-assistant/01-candidate-profile.md` + `CLAUDE.md`
- Orchestration: `.claude/commands/leads.md`
- CLI: `tools/leads_cli.py` (Windows: `python`)
- Visa/ATS pool: prefer `python tools/board_scrape.py --limit 30 --since 7d` (volume + Hiring Cafe via `APIFY_TOKEN`) or `visa_discover --volume --path-ab --new-only`; weekly `harvest_boards.py --write`; fake-remote enforced in `path_filter.py`
- Quality tiers: `leads/engine/quality.py`
- Docs: `leads/README.md`

## How to behave

1. Read `leads/preferences.md` and the candidate profile.
2. Interpret the user’s sentence; **empty / find leads / best leads / today’s / worldwide / deep / authentic → Best Leads Mode** (`preferences.md` + `PROMPT_PACK.md` Daily Best Leads). If **listings finished / Demand Graph** → **Depth O**. If **visa / relocation / onsite / hybrid / sponsored mobility** → **Depth P**. If **sponsor hubs / Path B primary / hub cities / after Depth P** → **Depth Q**. If **navigator / listings empty / agent not finding / search better / after Depth Q dry** → **Depth R Listing Navigator**. If **more parameters / find more listings / Depth S / parametric / multi-ATS / after Depth R dry** → **Depth S Parametric Board Sweep**. If **convert / backlog / after Depth S dry** → **Convert Day** (no discovery). If **zero-repeat / no repeats / same listings again / worldwide keeps repeating** → **Zero-Repeat Worldwide** (`PROMPT_PACK.md`). If **after zero-repeat dry / next strategy / fresh minutes** → Convert leftover same day, else **Fresh Minutes Zero-Repeat** next morning (no Depth T).
3. Expand with default geos + stack if missing. Cap **3–8** rows (+ ≤2 salvage if NEW empty). Freshness: Best Leads Path A ≤10d / Path B ≤14d; Navigator Path A ≤7d; Depth S Path A ≤10d / Path B ≤14d; Depth Q ≤10d. Undated + still open on owned ATS → Tier C OK.
4. Apply workplace gate from `preferences.md`: remote-international/EOR **or** onsite/hybrid **with quoted visa/relocation**. Never keep bare onsite/hybrid. Phone optional.
5. Show **Tier A → B → C** with Email? / Phone? / Proof URL (and Path A/B). Include **salvage** if NEW empty; Navigator/S always include **near-miss**; S may include Sponsor-Watch ≤5.
6. Ask one next step: outreach, apply, or skip. Do **not** auto-stack O→S on a vague find-leads. If two consecutive Best Leads/Depth runs are 0 NEW+salvage **and** near-miss empty → Convert Day / `/outcome` only. After R + S dry → **Convert Day** only (no Depth T same day).

## Non-negotiables

- No fabricated emails, phones, or leads
- **No repeated listings in NEW** — drop seen_jobs URL/company+title, tracker rows, recycle blocklist, Convert/Sponsor-Watch names; count `dropped_as_repeat`
- Intent ≠ fit; explicit demand ranks first
- Funding/launch alone ≠ demand (`demand_proven` required)
- Agency outreach = partnership pitch, not generic freelance
- Contact path = founder / eng manager / recruiter / application form — never invent executives
- Uncertain leads → `needs_review`; Tier D not presented as warm
- No external sends without explicit user approval
- Preserve `/scrape` `/rank` `/apply` `/outcome`
