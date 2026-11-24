# Visa / relocation discovery engine

Python package under `engine/` for international candidates who need sponsorship
or relocation. Complements LinkedIn / freehire portal CLIs — does not replace them.

## Quick start (Windows: `python`)

```bash
set JOB_SCRAPER_CONTACT=you@example.com
python tools/visa_discover.py --path-ab --since 14d --new-only --limit 30 --format summary

# Board volume (Indeed/LinkedIn/Glassdoor + RemoteOK + WWR + optional Hiring Cafe)
python -m pip install -r job_scraper/requirements-volume.txt
python tools/board_scrape.py --limit 30
```

## Live sources

| Source | Notes |
|--------|--------|
| Arbeitnow | `visa_sponsorship=true`; attribute/link back |
| Landing.jobs | EU tech; relocation/visa flags |
| Greenhouse / Ashby / Lever | Curated tokens in `../boards.json` |
| Workable / Personio / Teamtailor | Curated boards |
| SmartRecruiters / Recruitee | Curated boards + inventory harvest |
| JobSpy (`--volume`) | Indeed multi-country remote/visa + Pakistan any-mode (onsite/hybrid/remote) + LinkedIn/Glassdoor remote pass (`python-jobspy`) |
| RemoteOK / WeWorkRemotely (`--volume`) | Worldwide remote feeds |
| Hiring Cafe (`--volume`) | Needs `APIFY_TOKEN`; skips if unset |

Inventories: `../ats_inventories/` (from ats-scrapers, MIT). Grow boards with
`tools/harvest_boards.py` and `tools/discover_company_ats.py`.

## Filters

- `--path-ab` — Path A remote-intl/sponsor, Path B onsite/hybrid + verified sponsor/reloc, or **Path PK** (Pakistan local, any workplace)
- **Fake-remote DROP** (inside Path A/B): `within the U.S.`, `US only`, `Remote - United States`, `Fully Remote (US)`, UK/AU/CA-only remote — even when RemoteOK/WWR labels the row “Worldwide”
- `--since 7d` — drop dated rows older than N days (undated kept)
- `--new-only` — drop seen_jobs / tracker identities **and** companies in `job_scraper/block_companies.txt` (plus tracker rows already applied/rejected)

## Power tools

| Tool | Role |
|------|------|
| `probe_boards.py` | Validate tokens |
| `harvest_boards.py` | Inventory → live boards.json (**run weekly** with `--write`) |
| `discover_company_ats.py` | Company → ATS |
| `check_liveness.py` | URL still open? |
| `board_scrape.py` | Volume pack wrapper (prefer over LinkedIn-only) |

```bash
# Weekly — grow curated boards beyond the same ~12 slugs
python tools/harvest_boards.py --ats greenhouse,ashby,lever,smartrecruiters --limit 40 --write
```

## Sponsorship classes

`verified_in_listing` · `sponsor_company_only` · `possible` · `not_available` · `unknown`

Registry membership alone never becomes `verified_in_listing`.
