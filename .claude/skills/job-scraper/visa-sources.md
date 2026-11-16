# Visa / Relocation Job Source Comparison

Evidence gathered 2026-10-27. Prefer official public feeds. Do not bypass auth, CAPTCHAs, or robots restrictions.

Scoring (1–5): **Q** data quality · **S** sponsorship relevance · **C** geo coverage · **F** freshness · **I** integration effort (5 = easy) · **M** maintenance (5 = low cost).

| Source | Official API / feed? | Apply URL? | Sponsorship signal? | Collection OK? | Q | S | C | F | I | M | Verdict |
|--------|----------------------|------------|---------------------|----------------|---|---|---|---|---|---|---------|
| **Arbeitnow** | Yes — `GET /api/job-board-api?visa_sponsorship=true` (no key) | Yes (Arbeitnow job URL) | First-class `visa_sponsorship` filter; terms require link-back | Yes (public free API; be polite) | 4 | 5 | 3 (DE/EU/UK-heavy) | 5 (hourly) | 5 | 5 | **Implement first** |
| **Greenhouse Job Board API** | Yes — `boards-api.greenhouse.io/v1/boards/{token}/jobs` | Yes (`absolute_url`) | In description only | Yes (public GET, no auth) | 5 | 3 | 4 (per company) | 5 | 4 | 4 | **Implement** (curated boards) |
| **Ashby Posting API** | Yes — `api.ashbyhq.com/posting-api/job-board/{slug}` | Yes (`jobUrl` / `applyUrl`) | In description; workplaceType useful | Yes (public GET) | 5 | 3 | 4 | 5 | 4 | 4 | **Implement** (curated boards) |
| **Lever Postings API** | Yes — `api.lever.co/v0/postings/{site}?mode=json` | Yes | In description | Yes (public GET) | 5 | 3 | 4 | 5 | 4 | 4 | **Implement** (curated boards) |
| **freehire.me** (existing) | Yes — public agent search API | Yes (often ATS apply link) | Keyword / description only | Yes (existing portal skill) | 4 | 2 | 5 | 4 | 5 | 4 | **Keep** via portal CLI |
| **LinkedIn jobs-guest** (existing) | Semi-public HTML guest endpoints | Yes | Keyword search | Personal-use only; rate-limit sensitive | 3 | 3 | 5 | 4 | 4 | 2 | **Keep** via portal CLI |
| **UK Register of Licensed Sponsors** | CSV on GOV.UK (no official job API) | No jobs | Company *licensed* ≠ vacancy sponsors | Yes (OGL CSV download) | 5 | 2* | 2 (UK only) | 4 | 3 | 3 | **Registry helper only** → `sponsor_company_only` |
| **Relocate.me** | No verified public job API | Unknown | High (product focus) | Unverified; likely ToS/scrape risk | — | 5 | 4 | — | 1 | 1 | **Stub** — do not scrape until API/ToS clear |
| **Wellfound** | No stable public board API found | — | Some listings | Auth / anti-bot common | — | 3 | 3 | — | 1 | 1 | **Stub** |
| **EURES** | EU portal; programmatic access unclear / restricted | Yes | Varies | Prefer official channels only | — | 3 | 4 | — | 1 | 2 | **Stub** |
| **AU / NZ / Gulf sponsor registries** | Fragmented PDFs/portals; no unified job API | No | Company eligibility ≠ offer | Manual / future | — | 2* | 2 | — | 1 | 2 | Document only |
| **Employer career pages (generic HTML)** | N/A | Sometimes | In JD | Only if robots/ToS allow | 3 | 3 | 5 | 3 | 2 | 1 | Prefer ATS APIs above |

\* Registry membership means the employer *may* sponsor under that country's rules — never treat it as confirmation for a specific vacancy.

## Recommended implementation order

1. Arbeitnow (visa filter) + sponsorship classifier on descriptions  
2. Curated Greenhouse / Ashby / Lever boards for target-geo product companies  
3. Enrich existing LinkedIn / freehire hits with the same classifier  
4. Optional UK sponsor CSV lookup → `sponsor_company_only`  
5. Leave Relocate.me / Wellfound / EURES as adapter stubs until a permitted feed exists  

## Legal / ops notes

- Never auto-submit applications.  
- Arbeitnow: link back to arbeitnow.com when presenting their results; do not abuse the free API.  
- ATS board APIs are per-company — maintain `job_scraper/boards.json`, not a blind crawl of the internet.  
- UK sponsor CSV is large (~10 MB); cache locally under `job_scraper/cache/` (gitignored) when used.  
