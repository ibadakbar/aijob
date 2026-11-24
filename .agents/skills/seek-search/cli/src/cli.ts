#!/usr/bin/env bun
// SEEK AU/NZ listings via freehire index of seek.com.au / seek.co.nz URLs.
// Personal use only. Direct SEEK scrapes are blocked (Cloudflare + robots).

import { runSearch, type SearchOpts } from "./commands/search.js"
import { runDetail, type DetailOpts } from "./commands/detail.js"
import { writeError } from "./helpers.js"

interface Flags {
  _: string[]
  [k: string]: string | boolean | string[]
}

function parseFlags(argv: string[]): Flags {
  const flags: Flags = { _: [] }
  const alias: Record<string, string> = { q: "query", l: "location", n: "limit" }
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i]
    if (a.startsWith("--") || a.startsWith("-")) {
      const key = alias[a.replace(/^-+/, "")] ?? a.replace(/^-+/, "")
      const next = argv[i + 1]
      if (next === undefined || next.startsWith("-")) {
        flags[key] = true
      } else {
        flags[key] = next
        i++
      }
    } else {
      ;(flags._ as string[]).push(a)
    }
  }
  return flags
}

const HELP = `seek-cli — SEEK Australia / New Zealand listings (via freehire index)

USAGE
  bun run src/cli.ts search -q "<keywords>" [flags]
  bun run src/cli.ts detail <slug|seek-url|seek-job-id> [--format json|plain]

SEARCH FLAGS
  --query, -q <text>      Keywords (React, Next.js, full stack, …)
  --site au|nz|both       Default: both
  --location, -l <text>   City/region hint (appended to query)
  --jobage <days>         Posted within N days (default 14; 0 = any)
  --remote <mode>         remote | hybrid | onsite
  --page <n>              1-indexed page of SEEK-filtered results (default 1)
  --limit, -n <n>         Cap SEEK results (default 20)
  --format <fmt>          json (default) | table | plain

EXAMPLES
  bun run src/cli.ts search -q "React" --site au --jobage 7 --format table
  bun run src/cli.ts search -q "Next.js" --site nz --remote remote
  bun run src/cli.ts detail <slug-from-search> --format plain

Personal use only. SEEK blocks direct scrapes; this reads SEEK URLs from freehire.me.
`

const KNOWN_FLAGS: Record<string, Set<string>> = {
  search: new Set([
    "query", "site", "location", "jobage", "remote", "page", "limit", "format", "help", "h",
  ]),
  detail: new Set(["format", "help", "h"]),
}

function str(v: string | boolean | string[] | undefined): string | undefined {
  if (typeof v === "string") return v
  return undefined
}

async function main(): Promise<number> {
  const argv = process.argv.slice(2)
  const flags = parseFlags(argv)
  const cmd = (flags._ as string[])[0]

  if (!cmd || cmd === "help" || flags.help || flags.h) {
    process.stdout.write(HELP)
    return 0
  }

  const known = KNOWN_FLAGS[cmd]
  if (!known) {
    writeError(`Unknown command "${cmd}". Use search or detail.`, "BAD_ARG")
    return 1
  }
  for (const key of Object.keys(flags)) {
    if (key === "_") continue
    if (!known.has(key)) {
      writeError(`Unknown flag --${key} for ${cmd}`, "BAD_ARG")
      return 1
    }
  }

  if (cmd === "search") {
    if (flags.help || flags.h) {
      process.stdout.write(HELP)
      return 0
    }
    const siteRaw = (str(flags.site) || "both").toLowerCase()
    if (!["au", "nz", "both"].includes(siteRaw)) {
      writeError(`--site must be au|nz|both, got "${siteRaw}"`, "BAD_ARG")
      return 1
    }
    const remote = str(flags.remote)
    if (remote && !["remote", "hybrid", "onsite"].includes(remote)) {
      writeError(`--remote must be remote|hybrid|onsite, got "${remote}"`, "BAD_ARG")
      return 1
    }
    const format = (str(flags.format) || "json").toLowerCase()
    if (!["json", "table", "plain"].includes(format)) {
      writeError(`--format must be json|table|plain, got "${format}"`, "BAD_ARG")
      return 1
    }
    const jobage = flags.jobage === undefined ? 14 : Number(str(flags.jobage))
    const page = flags.page === undefined ? 1 : Number(str(flags.page))
    const limit = flags.limit === undefined ? 20 : Number(str(flags.limit))
    if (![jobage, page, limit].every((n) => Number.isFinite(n) && n >= 0)) {
      writeError("jobage/page/limit must be non-negative numbers", "BAD_ARG")
      return 1
    }
    if (page < 1) {
      writeError("--page must be >= 1", "BAD_ARG")
      return 1
    }

    const opts: SearchOpts = {
      query: str(flags.query),
      location: str(flags.location),
      site: siteRaw as SearchOpts["site"],
      jobage,
      remote,
      page,
      limit,
      format: format as SearchOpts["format"],
    }
    return runSearch(opts)
  }

  if (cmd === "detail") {
    const target = (flags._ as string[])[1]
    if (!target) {
      writeError("detail requires a slug, SEEK URL, or numeric SEEK job id", "BAD_ARG")
      return 1
    }
    const format = (str(flags.format) || "json").toLowerCase()
    if (!["json", "plain"].includes(format)) {
      writeError(`--format must be json|plain for detail, got "${format}"`, "BAD_ARG")
      return 1
    }
    const opts: DetailOpts = { target, format: format as DetailOpts["format"] }
    return runDetail(opts)
  }

  writeError(`Unknown command "${cmd}"`, "BAD_ARG")
  return 1
}

main().then((code) => process.exit(code))
