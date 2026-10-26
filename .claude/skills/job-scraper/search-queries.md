# Search Queries for Job Scraper

<!-- SETUP: Ibad Akbar — full-stack / React / SaaS; DE / SA / CH / Europe / AU / NZ / PK + visa/relocation -->

## Installed portal CLIs (primary for `/scrape`)

`/scrape` discovers every portal skill under `.agents/skills/*/SKILL.md` and runs its CLI first. Enabled by default for this profile: `linkedin-search` and `freehire-search`. Danish demos (Jobindex, Jobbank, Jobdanmark, Jobnet) stay **disabled** (not the target market).

The `site:` query templates below are the **WebSearch fallback**.

**Language scope:** Queries are in English (working language for target roles). Urdu/Hindi are not used as job-search query languages. Language Gate rules still apply from `04-job-evaluation.md`. German or Arabic as a *required* working language is a FAIL unless listed on the Languages table.

## Search Sites

Primary:
- **linkedin.com/jobs** — covered by `linkedin-search` CLI; run with location filters for Germany, Saudi Arabia, Switzerland, Europe hubs, Australia, New Zealand, Pakistan, and Remote
- **freehire.me** — covered by `freehire-search` CLI (tech/SaaS aggregations; filter by country when supported)

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

```
site:linkedin.com/jobs "Full Stack" (React OR Next.js OR TypeScript) ("visa sponsorship" OR "relocation") (Germany OR Switzerland OR Europe OR Australia OR "New Zealand" OR "Saudi Arabia" OR Pakistan)
site:linkedin.com/jobs "Full Stack Engineer" TypeScript SaaS (Germany OR Switzerland OR Australia OR remote)
site:linkedin.com/jobs "Software Engineer" "Next.js" ("visa sponsorship" OR relocation) (Germany OR Switzerland OR Australia OR "New Zealand")
site:linkedin.com/jobs "Full Stack Developer" React ("Saudi Arabia" OR Riyadh OR Jeddah) (visa OR relocation OR Iqama)
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

**Target geography checklist:** Germany · Saudi Arabia · Switzerland · Europe (EU/EEA + UK) · Australia · New Zealand · Pakistan

## Language Filter

Working languages and levels are in CLAUDE.md's Languages table. Apply `04-job-evaluation.md`'s Language Gate. English-required roles are PASS; roles requiring undeclared languages as the primary working language are FAIL.

## Date Filter

Only include jobs posted within the last 14 days, or with an application deadline that has not yet passed. If a posting date cannot be determined, include it but flag as "date unknown".

## Adapting Queries

If the user specifies a focus area, select queries from the matching category and also generate 2-3 custom queries for that focus. For example:
- "/scrape [focus_area]" -> relevant category queries + custom focus-specific queries
- "/scrape Germany visa" -> Priority 1 Germany + sponsorship queries
- "/scrape contract Australia" -> Priority 3 + Australia location
