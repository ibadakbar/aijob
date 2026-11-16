# Job scraper + visa discovery engine

`seen_jobs.json` remains the `/scrape` / `/rank` history file.

## Visa / relocation discovery

Python package under `engine/` extends discovery for international candidates who need sponsorship or relocation support. It does **not** replace LinkedIn / freehire portal CLIs.

```bash
# Windows: use python (full path if needed)
python tools/visa_discover.py --format summary --limit 25
python tools/visa_discover.py --sources arbeitnow --scrape-hits %TEMP%\visa_hits.json
python tools/scrape_state.py candidates --results %TEMP%\visa_hits.json
```

### Live sources (verified public APIs)

| Source | Notes |
|--------|--------|
| Arbeitnow | `visa_sponsorship=true`; attribute/link back to Arbeitnow |
| Greenhouse | Curated tokens in `boards.json` |
| Ashby | Curated slugs in `boards.json` |
| Lever | Curated sites in `boards.json` |

### Stubs (interface only)

Relocate.me, Wellfound, EURES — see `.claude/skills/job-scraper/visa-sources.md`.

### Sponsorship classifications

`verified_in_listing` · `sponsor_company_only` · `possible` · `not_available` · `unknown`

Registry membership alone never becomes `verified_in_listing`.

### Ranking

Each job gets separate `sponsorship_score` and `skill_score` (plus country/freshness). Explicit `not_available` cannot rank as a confirmed sponsored role.
