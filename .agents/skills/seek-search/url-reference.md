# SEEK Search — URL / data reference

## Why not scrape SEEK HTML directly

Investigation (2026-11-24):

| Check | Result |
|-------|--------|
| `https://www.seek.com.au/robots.txt` | `User-agent: *` **Disallow** `/api/jobsearch/`, `/graphql`, `*/job/`; **Allow** `*?keywords` |
| Direct GET with browser UA / `fetch_page.py` | HTTP **403** Cloudflare “confirm you are human” |
| Browser automation | Cloudflare interstitial (“Just a moment…”) |
| Public SEEK jobsearch API | Disallowed by robots for generic agents |

Conclusion: a zero-credential HTML/API scraper against seek.com.au is not viable for this CLI pattern.

## Data path used by this skill

**freehire.me public REST API** (unauthenticated JSON), filtered client-side to SEEK hosts.

| Item | Value |
|------|--------|
| Base | `https://freehire.me` (override: `FREEHIRE_API_URL`) |
| Search | `GET /api/v1/agent/jobs/search` |
| Detail | `GET /api/v1/jobs/{public_slug}` |
| SEEK AU host | `www.seek.com.au` / `seek.com.au` |
| SEEK NZ host | `www.seek.co.nz` / `seek.co.nz` |
| SEEK job URL | `https://www.seek.com.au/job/{numericId}` |

### Search query params (freehire)

| Param | Maps from |
|-------|-----------|
| `q` | `--query` (+ optional `--location` appended) |
| `countries` | `--site au` → `AU`; `nz` → `NZ`; `both` → both |
| `posted_within_days` | `--jobage` |
| `work_mode` | `--remote` |
| `limit` / `offset` | Internal pagination while collecting SEEK rows |

### Result reshape

- `url` ← freehire `url` (must contain seek host)
- `id` ← freehire `public_slug` (for `detail`)
- `seek_job_id` ← digits from `/job/(\d+)`
- `site` ← `au` or `nz` from host

## Personal-use warning

Keep request volume low. Do not commercialize. Re-check robots/ToS if switching to a paid unlocker against SEEK itself.
