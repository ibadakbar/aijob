# Lead generation engine

Evidence-based client, freelance, contract, and job-lead discovery. Complements `/scrape` (job boards) with intent classification, contact provenance, outreach drafts, and export — without sending any messages.

**Best Leads (default for `/leads` / “find leads” / “best leads”):** `visa_discover` + LinkedIn 48h/7d + owned ATS + contact ladder. Ranks **Tier A** (published email) → **B** (founder LinkedIn) → **C** (apply URL). Phone optional. Salvage ≤2 if NEW would be empty. Remotive/YC are seeds only. Depth O→S only after Best Leads is dry — not stacked in one vague run.

## How to use correctly (daily)

1. **Morning:** `/leads` or `/leads best leads` — expect 3–8 rows or honest dry + salvage/near-miss.
2. **Act:** reply with a number → `/apply <url>` or ask for outreach draft (never auto-send).
3. **Close the loop:** `/outcome` after apply / reject / no-reply so recycle learns.
4. **If dry once:** run **one** `/leads Depth R` **or** wait and try again later — do **not** paste O→S the same morning.
5. **Depth S** only when you say `more parameters` / `Depth S` after R.
6. **After S dry:** `/leads convert` — backlog + Sponsor-Watch only. Next calendar day → `/leads` again or Fresh Minutes.

## Quick start

```bash
# Windows
python tools/leads_cli.py discover --prompt "Find 15 React or Next.js contract or freelance projects" --yes

# Offline / CI (fixture source, no network)
python tools/leads_cli.py discover --prompt "Find React SaaS freelance work" --sources fixture --yes --no-persist

# Review / export / outreach / outcomes
python tools/leads_cli.py review --shortlist
python tools/leads_cli.py export --status all
python tools/leads_cli.py outreach <lead-id>
python tools/leads_cli.py outcome <lead-id> --status contacted --notes "Manual send after review"
python tools/leads_cli.py followup
```

In Claude Code / Cursor agent workflows, use `/leads` (see `.claude/commands/leads.md`).

**Easy mode:** write what you want in plain language. The agent reads `leads/preferences.md` (default geos, email rule, stack) and runs the right path — you do not need CLI flags.

Examples:

```text
/leads jobs in USA Canada UK Australia New Zealand
/leads React contracts with published email
/leads agency white-label partners in UK and Australia
/leads review
```

## Research missions (prompt → plan)

One natural-language prompt becomes a structured `SearchPlan` (`engine/mission.py`):

```bash
python tools/leads_cli.py plan --prompt "Find 200 remote React/Next.js jobs worldwide with visa sponsorship"
python tools/leads_cli.py discover --prompt "..." --yes   # sources default from the plan
```

Plans include opportunity kinds, sources to search, freshness, max results (up to **300**), verification floor, and an honest coverage claim (never “entire internet”).

## Live sources

| Source | Notes |
|--------|--------|
| **Remotive** | Public API `https://remotive.com/api/remote-jobs`. Attribute Remotive; link back to listing URLs; keep request volume low (≈≤4/day). |
| **Arbeitnow** | Reuses `job_scraper` Arbeitnow adapter (visa-friendly software roles). |
| **Greenhouse / Ashby / Lever** | Public ATS APIs; **curated** board tokens only (`job_scraper/boards.json`). |
| **Y Combinator (`ycombinator` / `yc`)** | Public YC directory (Algolia search-only key + yc-oss fallback). Returns **app/company name**, batch, website, hiring flag, and **founder names + LinkedIn** when published on the YC page. Does **not** scrape private co-founder emails. |
| **fixture** | `leads/fixtures/sample_leads.json` for tests and demos. |

Each adapter supports rate-safe HTTP via `job_scraper.engine.http`, source attribution, timestamps, and error reporting. Coverage of searched / failed / not-in-scope sources is written to export meta and CLI summary.

## Authenticity verification

Every lead gets a verification report (`engine/verify.py`) with status:

`verified` | `partially_verified` | `unverified` | `contradictory` | `stale` | `rejected`

Missing emails, salaries, or domains stay empty / listed under `missing_information` — never fabricated. Export includes recommended §11 fields in `lead_records.csv` / `lead_records.json`.

## Stubs (not scraped)

Upwork, Contra, Wellfound, LinkedIn posts — documented in `engine/sources/stubs.py`. The `/leads` agent may use **WebSearch** for public pages only; never bypass login/CAPTCHA.

## Intent classes

- `EXPLICIT_DEMAND` — public request, contract, project brief, or active opening
- `STRONG_SIGNAL` — funding/launch/scaling evidence without an explicit ask
- `POTENTIAL_FIT` — possible fit, no established buying intent (ranked lowest)

Intent score and skill fit are **separate**. Explicit demand outranks speculative company fit.

## Opportunity radar

Detects demand-creating events, then requires a second signal before treating the row as a lead:

| Event | Alone | Becomes demand when also… |
|-------|-------|---------------------------|
| Funding | signal only | hiring ask / project brief / budget |
| SaaS launch | signal only | hiring ask / project brief / budget |
| Agency client win | signal only | contractor / white-label ask |
| Eng team expansion | signal | explicit hiring or budget |
| Tech hiring (React/Next/…) | demand when ask is explicit | — |

`demand_proven=false` → always `needs_review`. Do not pitch on funding news alone.

```bash
python tools/leads_cli.py discover --prompt "Find funded startups that are also hiring React" --mode jobs,radar --yes

# YC startups + published founder LinkedIn (no invented emails)
python tools/leads_cli.py discover --prompt "Find 15 YC startups hiring React SaaS" --sources ycombinator --mode radar --yes
```

## Agency partnership finder

Looks for digital agencies that need engineering capacity and drafts a **partnership** pitch (white-label / overflow), not a generic freelance note.

Fits: `white_label`, `overflow_capacity`, `design_only_gap`, `consultancy_contract`.

```bash
python tools/leads_cli.py discover --prompt "Find agencies seeking white-label React partners" --mode agency --yes
```

## Contact-path intelligence

Picks the most relevant **published** route into the org and explains why:

- Founder — small startup or agency partnership
- Engineering manager / tech lead — technical contract work
- Recruiter — published vacancy
- Application / contact form — when no named contact is published

Never invents executives or emails. Prefers the official application URL over guessing.

## Contacts

Emails are taken only when they **literally appear** in source text. Labels:

- `published_on_official_source`
- `domain_mx_present` (MX/A lookup — does **not** prove the mailbox exists)
- `unverified` / `unknown` / `not_applicable`

Never fabricate or guess personal emails. Prefer the official application URL or contact form when unsure.

## Storage

- `leads/store/leads_store.json` — durable lead map (gitignored)
- `leads/store/discovery_state.json` — per-source fetch time and vacancy hashes (gitignored)
- `leads/store/research_cache.json` — company, domain, vacancy, and extraction cache (gitignored)
- `leads/store/evidence.jsonl` — append-only source URL, timestamp, and excerpt log (gitignored)
- `leads/store/runs/` — checkpoints for failed and interrupted searches (gitignored)
- `leads/exports/<run-id>/` — `report.md`, `leads.csv`, `outreach-drafts.md`, `sources-and-limitations.md`, `leads.json` (gitignored)

## Efficiency

Discovery is incremental by default. The same search is not fetched again for 12 hours, and a later fetch scores only vacancies whose URL is new or whose excerpt, date, or intent changed. `--full` repeats the search and still reuses cached extraction.

```bash
python tools/leads_cli.py discover --prompt "Find React contract work" --yes
python tools/leads_cli.py discover --prompt "Find React contract work" --full --yes
python tools/leads_cli.py review --queue
python tools/leads_cli.py failures
python tools/leads_cli.py discover --resume <run-id> --yes
python tools/leads_cli.py evidence <lead-id>
python tools/leads_cli.py sources
```

- **Review queue.** Explicit, current demand at or above confidence 0.72 is stored as `qualified`. Everything else is `needs_review` and is not auto-qualified. `review --shortlist` does not include the queue.
- **Cost.** Scoring and outreach drafts are cached by content hash on the cheap extraction path. Ambiguous companies (no explicit ask, or no excerpt) are marked `research_deferred` for a stronger pass and are not researched automatically. A company already in the cache stays on the cheap path.
- **Evidence.** Each qualified or queued lead appends the source URL, the time it was recorded, and the excerpt to `evidence.jsonl`.
- **Failure recovery.** Transient errors (timeouts, connection failures, HTTP 429/5xx) are retried. The run file records sources that still failed. `--resume <run-id>` fetches only those unfinished sources.
- **New sources.** Subclass `LeadSourceAdapter`, implement `fetch`, and call `register_source("name", YourSource)`. The pipeline picks it up by name. Job-board and company-site adapters stay independent of the rest of the engine.

## Safety

- External content is sanitized (`engine/sanitize.py`)
- Outreach always has `send_approved: false`
- Existing `/setup`, `/scrape`, `/rank`, `/apply`, `/outcome` workflows are unchanged
