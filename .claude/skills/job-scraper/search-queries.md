# Search Queries for Job Scraper

<!-- SETUP: Ibad Akbar — full-stack / React / SaaS; visa/relocation markets below -->

## Installed portal CLIs (primary for `/scrape`)

`/scrape` discovers every portal skill under `.agents/skills/*/SKILL.md` and runs its CLI first. Enabled by default for this profile: `linkedin-search` and `freehire-search`. Danish demos (Jobindex, Jobbank, Jobdanmark, Jobnet) stay **disabled** as HTML scrapers — Denmark is still a **target geography** via LinkedIn, freehire, and `tools/visa_discover.py` (Arbeitnow / ATS boards).

Also run **`python tools/visa_discover.py`** (Step 1d) for Arbeitnow visa-filtered jobs + curated Greenhouse/Ashby/Lever boards. Source research: `visa-sources.md`.

The `site:` query templates below are the **WebSearch fallback**.

**Language scope:** Queries are in English (working language for target roles). Urdu/Hindi are not used as job-search query languages. Language Gate rules still apply from `04-job-evaluation.md`. German or Arabic as a *required* working language is a FAIL unless listed on the Languages table.

## Search Sites

Primary:
- **linkedin.com/jobs** — `linkedin-search` CLI; location filters for the target geography checklist below + Remote
- **freehire.me** — `freehire-search` CLI (tech/SaaS; `--country` when supported)
- **visa discovery engine** — Arbeitnow (`visa_sponsorship=true`) + curated ATS boards in `job_scraper/boards.json`

Secondary (WebSearch fallback):
- Direct Google `site:` searches for target titles + geography + sponsorship keywords

## Employment types (all in scope)

Search and keep: **full-time**, **part-time**, **contract**. Tag employment type in scrape notes; do not drop PT or contract by default.

## Workplace types (all in scope)

Search and keep: **remote**, **hybrid**, **on-site**. Prefer remote/hybrid when ranking notes are close; do not drop hybrid or remote by default. For LinkedIn CLI runs, rotate `--remote remote`, `--remote hybrid`, and on-site (no remote filter or `--remote onsite`) across target locations.

## Mobility boosters (prefer / boost in ranking notes)

When present, call out strongly:
- **"visa sponsorship"** / "visa sponsor" / "relocation support" / "relocation package" / "work permit" / "skilled migrant"
- For Gulf: "Iqama" / "visa provided" (Saudi)
- For EU/CH/AU/NZ: "Blue Card", "skilled worker visa", "relocation assistance"

## Query Categories

### Priority 1: Full-stack / SaaS + target geos / sponsorship

Prefer **last 7 days** on sponsorship-focused `/scrape` runs. Always run `visa_discover` alongside LinkedIn/freehire. Drop hits that say US-citizen-only, local rights already required, or German/Dutch as required working language.

```
site:linkedin.com/jobs "Full Stack" (React OR Next.js OR TypeScript) ("visa sponsorship" OR "Will sponsor" OR "relocation") (Germany OR Netherlands OR "United Kingdom" OR Ireland OR Australia OR Canada OR UAE OR remote)
site:linkedin.com/jobs "Full Stack Engineer" TypeScript SaaS (Germany OR Netherlands OR "United Kingdom" OR Australia OR Canada OR remote)
site:linkedin.com/jobs "Software Engineer" "Next.js" ("visa sponsorship" OR relocation OR "work permit") (Germany OR Netherlands OR Ireland OR Australia OR "United Kingdom")
site:linkedin.com/jobs "Full Stack Developer" React (Dubai OR UAE OR Abu Dhabi) (visa OR relocation OR "work permit")
site:linkedin.com/jobs "Senior Software Engineer" React ("visa sponsorship" OR "Skilled Worker" OR "Blue Card" OR relocation) (Germany OR "United Kingdom" OR Netherlands OR Ireland)
site:linkedin.com/jobs "React" OR "Next.js" ("remote" AND ("worldwide" OR "international" OR "anywhere")) TypeScript (posted last week)
```

### Priority 2: Frontend / React / Next.js by market

```
site:linkedin.com/jobs "Frontend Engineer" React Next.js (Germany OR Berlin OR Munich OR Switzerland OR Zurich)
site:linkedin.com/jobs "React Developer" TypeScript (Australia OR Sydney OR Melbourne OR "New Zealand" OR Auckland)
site:linkedin.com/jobs "Frontend Developer" React (Pakistan OR Karachi OR Lahore) (full-time OR contract OR "part time")
site:linkedin.com/jobs "Next.js Developer" (remote OR Europe) ("visa sponsorship" OR relocation)
```

### Priority 3: Contract / part-time / adjacent stacks

```
site:linkedin.com/jobs "React" (contract OR "part-time" OR "part time") (Germany OR Switzerland OR Australia OR remote)
site:linkedin.com/jobs "React Native Developer" TypeScript (Germany OR Australia OR Pakistan OR remote)
site:linkedin.com/jobs "Shopify Developer" (React OR Liquid) (Europe OR Australia OR remote)
site:linkedin.com/jobs "Full Stack" (contract OR freelance) TypeScript (visa OR relocation OR remote)
```

### Priority 4: Broader Europe / AU / NZ / PK net

```
site:linkedin.com/jobs "Software Engineer" React (Netherlands OR "United Kingdom" OR Ireland OR Sweden OR Portugal) ("visa" OR relocation OR remote)
site:linkedin.com/jobs "MERN" OR "Full Stack" developer (Pakistan OR Karachi) (full-time OR contract)
site:linkedin.com/jobs "Node.js" React ("New Zealand" OR Wellington OR Auckland) (visa OR "work visa" OR relocation)
site:linkedin.com/jobs "Full Stack" Firebase OR Supabase (Germany OR Switzerland OR Australia OR remote)
```

## Location Filter

When evaluating results:
- **Ideal:** Target country on-site/hybrid **with visa sponsorship and/or relocation support**; or remote roles that explicitly hire internationally / from Pakistan into those markets
- **Acceptable:** Pakistan (Karachi local / hybrid / remote); remote worldwide English roles compatible with Karachi timezone overlap; target-geo roles that are FT, PT, or contract without sponsorship mentioned (FLAG sponsorship gap)
- **Borderline:** On-site in a non-listed country that still offers sponsorship — discuss with candidate
- **Too far / FAIL:** Strict on-site outside target geographies with no remote option and no visa/relocation path; roles requiring undeclared working languages (e.g. German-only, Arabic-only)

**Target geography checklist:** Germany · Netherlands · United Kingdom · Ireland · Australia · Canada · New Zealand · United States · Sweden · Finland · Denmark · UAE · Saudi Arabia · Qatar · Switzerland · Pakistan · broader EU/EEA when sponsorship/remote is clear

## Language Filter

Working languages and levels are in CLAUDE.md's Languages table. Apply `04-job-evaluation.md`'s Language Gate. English-required roles are PASS; roles requiring undeclared languages as the primary working language are FAIL.

## Date Filter

Only include jobs posted within the last 14 days, or with an application deadline that has not yet passed. If a posting date cannot be determined, include it but flag as "date unknown".

## Adapting Queries

If the user specifies a focus area, select queries from the matching category and also generate 2-3 custom queries for that focus. For example:
- "/scrape [focus_area]" -> relevant category queries + custom focus-specific queries
- "/scrape Germany visa" -> Priority 1 Germany + sponsorship queries
- "/scrape contract Australia" -> Priority 3 + Australia location
