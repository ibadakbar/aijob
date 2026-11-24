# Visa / Relocation Job Source Comparison

Evidence gathered 2026-10-27; expanded 2026-11-17 from career-ops / ats-scrapers / ever-jobs / job-boards analysis.

Prefer official public feeds. Do not bypass auth, CAPTCHAs, or robots restrictions.

Scoring (1–5): **Q** data quality · **S** sponsorship relevance · **C** geo coverage · **F** freshness · **I** integration effort (5 = easy) · **M** maintenance (5 = low cost).

| Source | Official API / feed? | Apply URL? | Sponsorship signal? | Collection OK? | Q | S | C | F | I | M | Verdict |
|--------|----------------------|------------|---------------------|----------------|---|---|---|---|---|---|---------|
| **Arbeitnow** | Yes — `GET /api/job-board-api?visa_sponsorship=true` | Yes | First-class visa filter; link-back required | Yes | 4 | 5 | 3 | 5 | 5 | 5 | **Live** |
| **Greenhouse** | `boards-api.greenhouse.io/.../jobs` | Yes | Description | Yes | 5 | 3 | 4 | 5 | 4 | 4 | **Live** (boards.json + inventories) |
| **Ashby** | `api.ashbyhq.com/posting-api/job-board/{slug}` | Yes | Description + workplaceType | Yes | 5 | 3 | 4 | 5 | 4 | 4 | **Live** |
| **Lever** | `api.lever.co/v0/postings/{site}?mode=json` | Yes | Description | Yes | 5 | 3 | 4 | 5 | 4 | 4 | **Live** |
| **Workable** | widget `.../accounts/{slug}?details=true` | Yes | Description | Yes | 4 | 3 | 4 | 4 | 4 | 3 | **Live** |
| **Personio** | `{host}/xml?language=en` | Yes | Description | Yes | 4 | 3 | 3 (DE/EU) | 4 | 4 | 3 | **Live** |
| **Teamtailor** | `{host}/jobs.json` | Yes | Description | Yes | 4 | 3 | 3 (EU) | 4 | 4 | 3 | **Live** |
| **SmartRecruiters** | `api.smartrecruiters.com/v1/companies/{slug}/postings` | Yes | Detail sections | Yes | 4 | 3 | 4 | 4 | 4 | 3 | **Live** |
| **Recruitee** | `{slug}.recruitee.com/api/offers` | Yes | Inline description | Yes | 4 | 3 | 3 | 4 | 4 | 3 | **Live** |
| **Landing.jobs** | `landing.jobs/api/v1/offers` | Yes | Relocation/visa flags often present | Yes | 4 | 4 | 3 (EU) | 4 | 5 | 4 | **Live** (ever-jobs idea) |
| **JobSpy** | python-jobspy (Indeed/LinkedIn/Glassdoor/…) | Yes | Description + optional emails/salary | Yes (optional dep) | 3 | 2 | 5 | 4 | 4 | 3 | **Live** via `--volume` |
| **RemoteOK** | `remoteok.com/api` | Yes | Worldwide remote by product | Yes; link-back | 3 | 2 | 4 | 4 | 5 | 4 | **Live** via `--volume` |
| **We Work Remotely** | Programming RSS | Yes | Fully remote | Yes | 3 | 2 | 4 | 3 | 5 | 4 | **Live** via `--volume` |
| **Hiring Cafe** | Apify actor (no free bulk API) | Yes | Structured `visaSponsorship` | Needs `APIFY_TOKEN` | 4 | 5 | 5 | 4 | 3 | 3 | **Optional** via `--volume` |
| **freehire.me** | Existing portal CLI | Yes | Keyword | Yes | 4 | 2 | 5 | 4 | 5 | 4 | **Keep** via portal CLI |
| **LinkedIn** | Guest / CLI | Yes | Keyword | Personal-use; rate-limit | 3 | 3 | 5 | 4 | 4 | 2 | **Keep** via portal CLI |
| **UK sponsor CSV** | GOV.UK CSV | No jobs | Company licence ≠ vacancy | Yes | 5 | 2* | 2 | 4 | 3 | 3 | Registry helper only |
| **Relocate.me / Wellfound / EURES** | No verified free job API | — | — | Stub | — | — | — | — | 1 | 1 | **Stub** |

\* Registry membership ≠ vacancy sponsorship.

## Power tools (from repo analysis)

| Tool | Inspired by | Purpose |
|------|-------------|---------|
| `visa_discover.py --since 7d --new-only --path-ab` | job-boards + career-ops | Fresh + unseen + Path A/B |
| `probe_boards.py` | job-boards | Validate board tokens before merge |
| `harvest_boards.py` | ats-scrapers inventories + job-boards | Probe inventory CSVs → boards.json |
| `discover_company_ats.py` | career-ops `discover` / ats-scrapers `find_company` | Name/slug → live ATS |
| `check_liveness.py` | career-ops liveness | Drop closed URLs before apply |
| `job_scraper/ats_inventories/*.csv` | ats-scrapers `ats-companies/` | ~35k board slugs (MIT) |

Set `JOB_SCRAPER_CONTACT=you@email` so outbound UA identifies your traffic (job-boards etiquette).

## Recommended run for /scrape + /leads

```bash
python tools/visa_discover.py --path-ab --since 14d --new-only --limit 40 --format scrape --scrape-hits %TEMP%\visa_hits.json
python tools/scrape_state.py candidates --results %TEMP%\visa_hits.json
```

Expand boards when dry:

```bash
python tools/harvest_boards.py --ats greenhouse,ashby,smartrecruiters --limit 40 --write
python tools/discover_company_ats.py "CompanyName" --write
```

## Legal / ops notes

- Never auto-submit applications.
- Arbeitnow: link back when presenting their results.
- ATS APIs are per-company — grow `boards.json` via harvest/probe, not blind Internet crawls in the agent loop.
- Full Wayback/Common Crawl discovery (job-boards `--refresh-boards`) is optional offline; inventories already cover tens of thousands of slugs.
