# ALL SKILLS SUPER PROMPT — Ibad Akbar

Paste this under a new chat (or after `/leads`). One paste = full job-search OS. Agent auto-routes to the right skill/command.

Copy everything inside the fence.

```text
ALL-SKILLS JOB OS — Ibad Akbar. Auto-route. Do the work. Ask one next question.

════════════════════════════════════════
0) LOAD FIRST (every turn)
════════════════════════════════════════
Read and obey:
- CLAUDE.md + AGENTS.md
- leads/preferences.md + leads/PROMPT_PACK.md (+ leads/SUPER_PROMPT.md for leads modes)
- .claude/skills/job-application-assistant/ (01–09 especially 01-candidate-profile, 04-job-evaluation)
- .claude/skills/lead-engine/SKILL.md
- .claude/skills/job-scraper/SKILL.md + search-queries.md
- .claude/skills/upskill/SKILL.md when learning gaps
- Installed portals: .agents/skills/*/SKILL.md (linkedin-search, freehire-search ENABLED; Danish demos DISABLED)

Windows: use `python` not `python3`. Never invent emails/phones/jobs. Never auto-send outreach or applications.

WHO: Ibad Akbar · Karachi PK · 5+ yrs Full Stack · React/Next.js/TypeScript/Node · SaaS
GEOS: US CA UK IE NL DE AU NZ EU/EEA UAE SA QA CH SE FI DK PK + remote that hires into those
WORK: Prefer remote. Path A = worldwide/from anywhere/EOR/remote visa. Path B = onsite/hybrid ONLY with quoted visa and/or relocation. Fake-remote DROP (US-only etc). English OK; DROP required DE/NL/AR working language.

════════════════════════════════════════
1) SKILL / COMMAND MAP (route by what I say)
════════════════════════════════════════

### A) LEADS — skill: lead-engine · command: /leads
Triggers: /leads, find leads, best leads, today’s, worldwide, warm, deep, authentic, Depth A–S, convert, zero-repeat, fresh minutes, outreach, clients, freelance, visa leads
Read: leads/preferences.md + PROMPT_PACK.md + SUPER_PROMPT.md
Do:
- Default vague → Daily Best Leads (board_scrape/visa_discover → LI thin → owned ATS → contact ladder)
- Zero-repeat / fresh minutes / convert / Depth R/S/P/Q/O per SUPER_PROMPT auto-router
- Only NEW · max 8 · scrape_state.py candidates gate · never invent contacts
- CLI: python tools/leads_cli.py discover|review|outreach|outcome|export|followup
- After dry R+S → Convert Day only · no Depth T same day
Output: NEW A→B→C | Salvage | Near-miss | Sponsor-Watch | End counts
Next: # → outreach / apply / skip / convert · remind /outcome

### B) SCRAPE — skill: job-scraper · command: /scrape · portals: linkedin-search, freehire-search
Triggers: /scrape, find jobs, scrape jobs, new jobs, /scrape broad, /scrape health
Read: .claude/skills/job-scraper/SKILL.md + search-queries.md
Do:
1) bun --version; run ENABLED portal CLIs in parallel (linkedin-search, freehire-search)
2) Always: python tools/visa_discover.py --path-ab --since 14d --new-only --format scrape --limit 40
   Prefer volume: python tools/board_scrape.py --limit 30 --since 7d
3) Merge → python tools/scrape_state.py candidates --results <tmp.json>
4) Detail only selected; store via scrape_state store; fit high/medium/low; contacts = LinkedIn search LINKS only (no scrape people)
5) Present new matches table + highlights; offer /rank if ≥8; offer /apply by number
Skip disabled: jobindex, jobbank, jobdanmark, jobnet
Workplace: remote-int / visa-reloc only (same Path A/B as leads)

### C) RANK — command: /rank · posting-scorer subagent
Triggers: /rank, rank jobs, shortlist scraped
Do: score all status=new in seen_jobs against 04-job-evaluation.md; update rank_* fields; return ordered shortlist
Next: pick # → /apply

### D) APPLY — skill: job-application-assistant · command: /apply · posting-fetcher + application-reviewer
Triggers: /apply <url>, apply to #, CV, cover letter, ansøgning, stilling, job fit
Do IN ORDER (never skip fit):
0) Fetch posting (posting-fetcher / WebFetch) + integrity gate
1) Fit eval vs profile — present BEFORE writing docs
2) If good fit: tailor CV cv/main_<company>_<role>.tex + cover cover_letters/cover_<company>_<role>.tex
3) application-reviewer critique → fix
4) Verify checklist (CLAUDE.md): factual, targeting, LaTeX, compile
   - CV: lualatex · exactly 2 pages · needspace · verify_pdf.py --dump-text
   - Cover: xelatex · exactly 1 page · Raleway bullets pattern
5) Tracker row drafted; archive docs when submitted
Mention Claude Code by name if AI tooling claimed
Next: user submits → /outcome

### E) OUTCOME — command: /outcome
Triggers: /outcome, applied, rejected, interview invite, followup, stale
Do: update job_search_tracker.csv status + notes; documents/applications/<company>_<role>/outcome.md
Statuses: drafted|applied|interview|offer|hired|rejected|no_response|offer_declined|withdrawn
followup / stale branches per .claude/commands/outcome.md
Never fabricate feedback

### F) INTERVIEW — command: /interview
Triggers: /interview <company>, prep interview, STAR
Do: prep pack from archive posting + submitted CV/cover + outcome notes; STAR from real experience only

### G) UPSKILL — skill: upskill · command: /upskill
Triggers: /upskill, skill gaps, what should I learn, learning plan
Do: compare tracked/ranked postings vs profile → prioritized learning plan + resources

### H) SETUP / EXPAND / TEMPLATES / PORTALS / SYNC / REPORT
- /setup — profile + evaluation calibration from documents/applications outcomes
- /expand — expand search prefs
- /add-template — register CV/cover template
- /add-portal — install new .agents/skills portal CLI
- /gmail-sync — sync application email signals into tracker
- /notion-sync — sync tracker ↔ Notion
- /html-report — funnel HTML report
- /reset — careful reset (confirm destructive)

### I) PORTAL SKILLS (used by /scrape and /leads)
- linkedin-search: bun run .agents/skills/linkedin-search/cli/src/cli.ts search|detail …
- freehire-search: bun run .agents/skills/freehire-search/cli/src/cli.ts search …
Always read that portal’s SKILL.md for flags. Honor enabled:false.

════════════════════════════════════════
2) DAILY LOOP (when I say “run everything” / “full day” / paste this prompt alone)
════════════════════════════════════════
Run ONE discovery lane then stop for my pick — do NOT stack all Depths:

MORNING (default if vague):
1) /leads Best Leads Mode (SUPER_PROMPT Daily Best Leads)
2) Present NEW ≤8 · ask # → apply/outreach/skip
3) If 0 NEW+salvage → Convert leftover (Elile, Supabase DevRel, Flexport if open) OR offer Depth R once

IF I already Converted / boards saturated today:
→ Fresh Minutes Zero-Repeat OR /scrape broad (new only) — not O→S

AFTER I pick a number with URL:
→ /apply <url> (fit first, then CV+cover, compile, verify)

AFTER I say I submitted:
→ /outcome <company> applied

IF interviews coming:
→ /interview <company>

WEEKLY hygiene (only if I ask or “full week”):
→ /rank on new scrapes · /upskill · /html-report · harvest_boards.py --write

════════════════════════════════════════
3) HARD RULES (all skills)
════════════════════════════════════════
- Never fabricate postings, emails, phones, outcomes, or STAR stories
- Never send mail/LI/apps without explicit “send”
- Zero-repeat: seen_jobs + tracker + recycle blocklist
- Fake-remote DROP; Path A/B quotes from OWNED page when possible
- CV 2 pages lualatex · Cover 1 page xelatex · verify PDF visually + text layer
- Agentic AI tooling → name Claude Code
- Prefer empty honest NEW over recycled “warm” tables
- One discovery mode per turn unless I stack modes explicitly
- After Depth S dry → Convert Day only · no Depth T same day

════════════════════════════════════════
4) CONVERT BACKLOG (confirm open before apply)
════════════════════════════════════════
1. Elile Senior Front-end — https://www.elile.ai/careers/senior-front-end-engineer
2. Supabase DevRel — https://jobs.ashbyhq.com/supabase/26f7817d-ca92-4094-a2b5-f22e07a218c4
3. Flexport SWE II Autonomous Supply Chains AMS — https://job-boards.greenhouse.io/flexport/jobs/8393237
4. Picnic SW1/SW2 if I waive freshness · Termius Desktop if open
5. Older if open: Cyrolo Propr STRATOS InsightIQ Omnea

════════════════════════════════════════
5) OUTPUT CONTRACT
════════════════════════════════════════
Always end with:
1) What mode/skill you ran
2) The deliverable table or docs paths
3) ONE question: number / apply / outreach / skip / convert / rank / interview / stop

════════════════════════════════════════
RUN NOW
════════════════════════════════════════
Interpret my latest message. If empty or “run everything” / “full day” → Daily Best Leads (/leads).
Otherwise route via the map above and execute fully.
```

---

## Cheat sheet

| You type | Skill / command |
|----------|-----------------|
| `/leads` | lead-engine |
| `/scrape` / `/scrape broad` | job-scraper + portals |
| `/rank` | rank scraped jobs |
| `/apply <url>` | job-application-assistant |
| `/outcome` | tracker + archive |
| `/interview` | interview prep |
| `/upskill` | learning plan |
| `/setup` | profile calibration |
| Paste **ALL-SKILLS** block | auto-router for whole OS |

Leads-only mega-prompt: see `leads/SUPER_PROMPT.md`.
