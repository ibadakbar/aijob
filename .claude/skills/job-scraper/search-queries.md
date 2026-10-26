# Search Queries for Job Scraper

<!-- SETUP: Configured for Ibad Akbar — full-stack / React / SaaS, English CV, remote-first -->

## Installed portal CLIs (primary for `/scrape`)

`/scrape` discovers every portal skill under `.agents/skills/*/SKILL.md` and runs its CLI first. Enabled by default for this profile: `linkedin-search` and `freehire-search`. Danish demos (Jobindex, Jobbank, Jobdanmark, Jobnet) stay **disabled** (not the target market).

The `site:` query templates below are the **WebSearch fallback**.

**Language scope:** Queries are in English (working language for target roles). Urdu/Hindi are not used as job-search query languages. Language Gate rules still apply from `04-job-evaluation.md`.

## Search Sites

Primary:
- **linkedin.com/jobs** — covered by `linkedin-search` CLI; remote + Pakistan filters
- **freehire.me** — covered by `freehire-search` CLI (tech/SaaS aggregations)

Secondary (WebSearch fallback):
- Direct Google `site:` searches for target titles and remote roles

## Query Categories

### Priority 1: Full-stack / SaaS product engineering

These match the strongest career direction (React, Next.js, Node, TypeScript SaaS).

```
site:linkedin.com/jobs "Full Stack Developer" React OR Next.js remote
site:linkedin.com/jobs "Full Stack Engineer" TypeScript SaaS remote
site:linkedin.com/jobs "Software Engineer" "Next.js" remote
site:linkedin.com/jobs "SaaS" "React" developer remote
```

### Priority 2: Frontend / React / Next.js

```
site:linkedin.com/jobs "Frontend Engineer" React Next.js remote
site:linkedin.com/jobs "React Developer" TypeScript remote
site:linkedin.com/jobs "Next.js Developer" remote
site:linkedin.com/jobs "Frontend Developer" Redux OR TypeScript remote OR Pakistan
```

### Priority 3: Adjacent — Shopify, React Native, solutions-leaning

```
site:linkedin.com/jobs "Shopify Developer" Liquid OR React remote
site:linkedin.com/jobs "React Native Developer" TypeScript remote
site:linkedin.com/jobs "Solutions Engineer" JavaScript OR React remote
site:linkedin.com/jobs "Frontend Lead" React OR Next.js remote
```

### Priority 4: Broader technical / Pakistan + remote net

```
site:linkedin.com/jobs "Node.js" developer remote
site:linkedin.com/jobs "MERN" developer remote OR Pakistan
site:linkedin.com/jobs "Software Engineer" React Karachi OR Pakistan
site:linkedin.com/jobs "Full Stack" Firebase OR Supabase remote
```

## Location Filter

When evaluating results:
- **Ideal:** Fully remote (worldwide / async-friendly), or remote with US/EU overlap compatible with Karachi
- **Acceptable:** Karachi / Pakistan remote or hybrid in Karachi
- **Borderline:** Hybrid requiring frequent travel outside Pakistan — discuss with candidate
- **Too far / FAIL:** Strict on-site only outside Karachi with no remote option (relocation not assumed)

## Language Filter

Working languages and levels are in CLAUDE.md's Languages table. Apply `04-job-evaluation.md`'s Language Gate. English-required roles are PASS; roles requiring undeclared languages (e.g. Danish, German as a job condition) are FAIL.

## Date Filter

Only include jobs posted within the last 14 days, or with an application deadline that has not yet passed. If a posting date cannot be determined, include it but flag as "date unknown".

## Adapting Queries

If the user specifies a focus area, select queries from the matching category and also generate 2-3 custom queries for that focus. For example:
- "/scrape [focus_area]" -> relevant category queries + custom focus-specific queries
