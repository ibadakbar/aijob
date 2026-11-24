import {
  apiGet,
  toSeekResult,
  writeError,
  type FreehireJob,
  type SeekJobResult,
  type SeekSite,
} from "../helpers.js"

const SEARCH_PATH = "/api/v1/agent/jobs/search"

export interface SearchOpts {
  query?: string
  location?: string
  site: "au" | "nz" | "both"
  jobage: number
  remote?: string
  page: number
  limit: number
  format: "json" | "table" | "plain"
}

function countriesForSite(site: SearchOpts["site"]): string[] {
  if (site === "au") return ["AU"]
  if (site === "nz") return ["NZ"]
  return ["AU", "NZ"]
}

function siteAllowed(row: SeekJobResult, site: SearchOpts["site"]): boolean {
  if (site === "both") return true
  return row.site === site
}

function buildQuery(opts: {
  q: string
  countries: string[]
  jobage: number
  remote?: string
  limit: number
  offset: number
}): string {
  const p = new URLSearchParams()
  if (opts.q) p.set("q", opts.q)
  p.set("limit", String(opts.limit))
  p.set("offset", String(opts.offset))
  p.set("description_format", "text")
  if (opts.jobage > 0 && opts.jobage < 9999) p.set("posted_within_days", String(opts.jobage))
  if (opts.remote) p.set("work_mode", opts.remote)
  for (const c of opts.countries) p.append("countries", c)
  return p.toString()
}

function shortDate(date: string | null): string {
  return date ? date.slice(0, 10) : "—"
}

function renderTable(rows: SeekJobResult[]): string {
  if (rows.length === 0) return "No SEEK results."
  const cols = [
    { h: "SEEK_ID", w: 10, c: (r: SeekJobResult) => r.seek_job_id ?? "—" },
    { h: "SITE", w: 4, c: (r: SeekJobResult) => r.site ?? "—" },
    { h: "TITLE", w: 36, c: (r: SeekJobResult) => r.title },
    { h: "COMPANY", w: 22, c: (r: SeekJobResult) => r.company ?? "—" },
    { h: "LOCATION", w: 18, c: (r: SeekJobResult) => r.location ?? "—" },
    { h: "DATE", w: 10, c: (r: SeekJobResult) => shortDate(r.date) },
  ]
  const row = (cells: string[]) => cells.map((c, i) => c.slice(0, cols[i].w).padEnd(cols[i].w)).join("  ")
  const header = row(cols.map((c) => c.h))
  const body = rows.map((r) => row(cols.map((c) => c.c(r))))
  return [header, "-".repeat(header.length), ...body].join("\n")
}

function renderPlain(rows: SeekJobResult[]): string {
  if (rows.length === 0) return "No SEEK results."
  return rows
    .map(
      (r, i) =>
        `${i + 1}. ${r.title}\n   ${r.company ?? "—"} · ${r.location ?? "—"} · ${r.site ?? "—"}\n   ${r.url}\n   id=${r.id}`,
    )
    .join("\n\n")
}

/**
 * Pull freehire pages until we have enough SEEK-filtered rows for the requested
 * page window, or the API runs out.
 */
export async function collectSeekJobs(opts: SearchOpts): Promise<{
  rows: SeekJobResult[]
  scanned: number
  freehireTotal: number | null
}> {
  const qParts = [opts.query?.trim(), opts.location?.trim()].filter(Boolean)
  const q = qParts.join(" ")
  const countries = countriesForSite(opts.site)
  const need = opts.page * opts.limit
  const pageSize = 25
  const maxScan = 200
  const collected: SeekJobResult[] = []
  const seen = new Set<string>()
  let offset = 0
  let scanned = 0
  let freehireTotal: number | null = null

  while (collected.length < need && scanned < maxScan) {
    const qs = buildQuery({
      q,
      countries,
      jobage: opts.jobage,
      remote: opts.remote,
      limit: pageSize,
      offset,
    })
    const envelope = await apiGet<FreehireJob[]>(`${SEARCH_PATH}?${qs}`)
    if (!envelope) break
    const batch = Array.isArray(envelope.data) ? envelope.data : []
    if (typeof envelope.meta?.total === "number") freehireTotal = envelope.meta.total
    if (batch.length === 0) break

    scanned += batch.length
    for (const job of batch) {
      const row = toSeekResult(job)
      if (!row || !siteAllowed(row, opts.site)) continue
      if (seen.has(row.url)) continue
      seen.add(row.url)
      collected.push(row)
      if (collected.length >= need) break
    }

    offset += pageSize
    if (batch.length < pageSize) break
  }

  const start = (opts.page - 1) * opts.limit
  return {
    rows: collected.slice(start, start + opts.limit),
    scanned,
    freehireTotal,
  }
}

export async function runSearch(opts: SearchOpts): Promise<number> {
  try {
    const { rows, scanned, freehireTotal } = await collectSeekJobs(opts)
    const payload = {
      meta: {
        count: rows.length,
        page: opts.page,
        site: opts.site,
        scanned,
        freehire_total: freehireTotal,
        source: "freehire-index-of-seek",
      },
      results: rows,
    }

    if (opts.format === "table") {
      process.stdout.write(renderTable(rows) + "\n")
    } else if (opts.format === "plain") {
      process.stdout.write(renderPlain(rows) + "\n")
    } else {
      process.stdout.write(JSON.stringify(payload, null, 2) + "\n")
    }
    return 0
  } catch (e) {
    writeError(e instanceof Error ? e.message : String(e), "FETCH_FAILED")
    return 1
  }
}

export type { SeekSite }
