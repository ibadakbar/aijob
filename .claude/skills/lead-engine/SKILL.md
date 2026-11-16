---
name: lead-engine
description: >
  Depth-first lead finder: company careers + published contacts first; adapters
  are seeds only. Ranks Tier A (email) > B (founder LinkedIn) > C (apply URL);
  prefers 3–8 authentic ≤7-day listings over Remotive/YC dumps. Triggers on:
  /leads, find leads, today's leads, deep leads, authentic leads, warm leads,
  find clients, find contracts, freelance, outreach, visa, YC, Remotive,
  Arbeitnow, worldwide leads
allowed-tools: Read, Write, Edit, Glob, Grep, WebFetch, WebSearch, AskUserQuestion, Bash(python tools/leads_cli.py:*), Bash(python3 tools/leads_cli.py:*)
---

# Lead Engine (Depth Intelligence)

User writes what they need. You run `.claude/commands/leads.md` — do not make them choose CLI flags.

**Default for vague “find leads”:** Depth Intelligence World path (company-site → LinkedIn → visa_discover → ATS seeds). Not Remotive/YC dumps.

## Source of truth

- Defaults / playbook: `leads/preferences.md`
- Paste prompts: `leads/PROMPT_PACK.md` (Depth A–D)
- Profile: `.claude/skills/job-application-assistant/01-candidate-profile.md` + `CLAUDE.md`
- Orchestration: `.claude/commands/leads.md`
- CLI: `tools/leads_cli.py` (Windows: `python`)
- Quality tiers: `leads/engine/quality.py`
- Docs: `leads/README.md`

## How to behave

1. Read `leads/preferences.md` and the candidate profile.
2. Interpret the user’s sentence; **empty / find leads / worldwide / deep / authentic → Depth World path**.
3. Expand with default geos + stack if missing. Cap **3–8** rows; freshness ≤7 days.
4. Run Depth path from `leads.md` (company WebSearch first; adapters only as seeds; contact enrichment with quoted URLs).
5. Show a short table sorted **Tier A → B → C** with Email? / Phone? / Proof URL.
6. Ask one next step: outreach, apply, or skip. If saturated → say so; rotate Depth A–D.

## Non-negotiables

- No fabricated emails, phones, or leads
- Intent ≠ fit; explicit demand ranks first
- Funding/launch alone ≠ demand (`demand_proven` required)
- Agency outreach = partnership pitch, not generic freelance
- Contact path = founder / eng manager / recruiter / application form — never invent executives
- Uncertain leads → `needs_review`; Tier D not presented as warm
- No external sends without explicit user approval
- Preserve `/scrape` `/rank` `/apply` `/outcome`
