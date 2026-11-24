---
name: seek-search
version: 1.0.0
description: >
  Use this skill to search SEEK job listings for Australia and New Zealand
  (seek.com.au / seek.co.nz), including React, Next.js, full-stack, and remote
  roles. Trigger phrases: SEEK jobs, seek.com.au, seek.co.nz, jobs Australia,
  jobs New Zealand, Australian job search, NZ vacancies, SEEK React, SEEK
  frontend, scrape SEEK.
context: fork
enabled: true
allowed-tools: Bash(bun run .agents/skills/seek-search/cli/src/cli.ts *)
---

# SEEK Search Skill (AU / NZ)

Search **SEEK** listings for Australia (`seek.com.au`) and New Zealand (`seek.co.nz`).

## How data is fetched (important)

SEEK’s own site blocks ordinary CLI scrapes (Cloudflare 403) and `robots.txt`
disallows `/api/jobsearch/`, `/graphql`, and `*/job/` for generic user-agents.
This skill therefore reads **SEEK-hosted apply URLs from the public freehire.me
index** (same unauthenticated JSON API as `freehire-search`), then keeps only
rows whose `url` is on `seek.com.au` or `seek.co.nz`.

> **Personal use only.** Keep volume low. Do not use commercially or for bulk
> harvesting. You are responsible for compliance with SEEK and freehire terms.
> Prefer Path A/B filtering after search — many SEEK roles are AU/NZ-only remote
> or hybrid with no overseas hire / visa quote.

## Commands

### Search

```bash
bun run .agents/skills/seek-search/cli/src/cli.ts search -q "React" [flags]
```

Flags:
- `--query` / `-q` — keywords (recommended)
- `--site au|nz|both` — default `both`
- `--location` / `-l` — city/region hint (folded into the keyword query)
- `--jobage <days>` — posted within N days (default 14; `0` = no age filter)
- `--remote <mode>` — `remote` | `hybrid` | `onsite` (freehire work_mode facet)
- `--page <n>` — 1-indexed page into the filtered SEEK set (default 1)
- `--limit` / `-n` — max SEEK results to emit (default 20)
- `--format json|table|plain` — default `json`

### Detail

```bash
bun run .agents/skills/seek-search/cli/src/cli.ts detail <id|seek-url> [--format json|plain]
```

`id` is the freehire public slug from search results (needed to hydrate the
description). A full `https://www.seek.com.au/job/<id>` URL is also accepted
when that posting is still in freehire’s index.

## Examples

```bash
bun run .agents/skills/seek-search/cli/src/cli.ts search -q "React" --site au --jobage 7 --format table
bun run .agents/skills/seek-search/cli/src/cli.ts search -q "Next.js" --site nz --remote remote --format json
bun run .agents/skills/seek-search/cli/src/cli.ts search -q "full stack TypeScript" -l "Sydney" --site au --limit 10
bun run .agents/skills/seek-search/cli/src/cli.ts detail <slug-from-search> --format plain
```

## Output

| Format | Use |
|--------|-----|
| `json` | Default — `{ meta, results }` for `/scrape` |
| `table` | Quick scan |
| `plain` | Full detail text |

Errors → stderr JSON `{ "error", "code" }`, exit `1`.

## Notes

- Result `url` is the SEEK job URL; `id` is the freehire slug used by `detail`.
- Extra fields: `seek_job_id`, `site` (`au`|`nz`).
- Empty SEEK hits with a successful freehire response is normal (index lag) — not a CLI bug.
- For `/scrape`: still apply Ibad’s Path A/B workplace gate after selection.
