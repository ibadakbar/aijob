# 24/7 Opportunity Discovery Agent (Excel-only)

Local autonomous worker that discovers jobs and related opportunities and persists **everything** in `data/opportunities.xlsx`.

**No database.** Storage = Excel (`openpyxl`) + JSON only for checkpoints/config/logs.

Existing `/scrape`, `/leads`, `/apply`, `/outcome` workflows are **unchanged**. This agent wraps:

- `tools/visa_discover.py` / `tools/board_scrape.py` (jobs, Path A/B)
- `tools/harvest_boards.py` (optional ATS slug refresh)
- `tools/leads_cli.py` + `leads/store/leads_store.json` (bridge + founder/recruiter/agency hunters)

## Quick start (Windows 11)

```bat
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-agent.txt
.venv\Scripts\python.exe -m pip install -r job_scraper\requirements-volume.txt
.venv\Scripts\python.exe agent\cli.py init
start_agent.bat
run_dashboard.bat
```

Or one shot: `run_all.bat`

### 24/7 requirement

The PC must stay **powered on**, **online**, and **not sleeping**. The agent does not run in Cursor/Claude — use `start_agent.bat` or Task Scheduler.

## Quality gates (v0.2 — always on before Excel write)

| Gate | Behavior |
|------|----------|
| **Zero-repeat** | Fingerprint company+title+URL; block applied companies; fold `seen_jobs` + tracker; N-day kill (`quality.kill_days`) |
| **Path A/B + fake-remote** | Same rules as `job_scraper/engine/path_filter.py` — country-only remote and unsponsored onsite never enter Excel |
| **Contact ladder** | Public email → founder LinkedIn → apply URL only. Inferred/guessed emails stripped |
| **Grade A hireability** | Grade A only when **demand signal** + **reachable contact** (email or `/in/` LinkedIn) |

## Live collectors

| Engine | CLI | What it hunts |
|--------|-----|----------------|
| Jobs | `run-once --engine jobs` | **Intelligent multi-strategy + auto-improve:** rotating freehire packs + visa_fast + volume; if `added=0` dry streak → emergency visa/worldwide/PK packs, wider `since`, same-cycle escalation |
| ATS / careers | `hunt-ats` / `--engine ats` | `board_scrape` (+ optional `harvest_boards`) |
| Leads bridge | `--engine leads` | `leads_cli` + gated `leads_store` ingest |
| Clients | `hunt-clients` | Worldwide buyers needing React/Next/TS; email/phone if published |
| Founders | `hunt-founders` | YC/founders + founder-titled contacts from store |
| Recruiters | `hunt-recruiters` | Published recruiter/talent emails |
| Agencies | `hunt-agencies` | `partnership.is_agency` overflow partners |
| Contact chain | `enrich-contacts` / `--engine enrichment` | Public pages only: company → `/contact` `/about` `/team` → published email/phone/WhatsApp (never invent) |

## CLI

```bat
python agent\cli.py init
python agent\cli.py status
python agent\cli.py run-once --engine all
python agent\cli.py run-once --engine jobs
python agent\cli.py hunt-ats
python agent\cli.py hunt-founders
python agent\cli.py hunt-recruiters
python agent\cli.py hunt-agencies
python agent\cli.py ingest-leads
python agent\cli.py start
python agent\cli.py stop | pause | resume | run-now
python agent\cli.py backup
```

## Excel workbook

Path: `data/opportunities.xlsx`

Sheets: All Opportunities, Jobs, Contracts & Freelance, Founders & Clients, Recruiters, Agencies, Companies, Contacts, Source Performance, Discovery History, Search Queries, Agent Statistics.

Manual **Status** / **Notes** / **Next Action** edits are preserved on agent upserts.

Backups: `backups/opportunities_*.xlsx`

## Config

`agent/config/default.yaml` — intervals, engine toggles, `quality.*` gates.

## Privacy / safety

- Never fabricates emails or contacts
- Never auto-sends outreach or applications
- Respects rate limits; one failing source does not stop the agent
- Fake-remote / Path A/B enforced in the agent gate **and** in visa_discover

## Tests

```bat
python -m pytest tests\test_agent_excel_store.py tests\test_agent_quality_gates.py -q
```
