// SEEK listings via freehire.me public JSON (seek.com.au / seek.co.nz URLs only).
// Direct SEEK HTML/API is blocked (Cloudflare 403; robots Disallow /api/jobsearch/, */job/).

export const DEFAULT_BASE_URL = "https://freehire.me"

export function baseUrl(): string {
  const raw = (process.env.FREEHIRE_API_URL ?? "").trim()
  return (raw || DEFAULT_BASE_URL).replace(/\/+$/, "")
}

export function writeError(error: string, code: string): void {
  process.stderr.write(JSON.stringify({ error, code }) + "\n")
}

const UA = "MadsLorentzen/ai-job-search/1.0 (seek-search)"

export interface Envelope<T> {
  data: T
  meta?: { total?: number; limit?: number; offset?: number }
  error?: string
}

const RETRY_BUDGET_MS = 30_000

export function retryAfterMs(header: string | null, now = Date.now()): number | null {
  if (!header) return null
  const value = header.trim()
  if (/^\d+$/.test(value)) return Number(value) * 1000
  const date = Date.parse(value)
  if (Number.isNaN(date)) return null
  return Math.max(date - now, 0)
}

function sleep(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms))
}

export async function apiGet<T>(path: string): Promise<Envelope<T> | null> {
  const url = `${baseUrl()}${path}`
  const maxRetries = 6
  let delay = 500
  let waited = 0

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    let response: Response
    try {
      response = await fetch(url, {
        headers: { "User-Agent": UA, Accept: "application/json" },
        redirect: "follow",
        signal: AbortSignal.timeout(15000),
      })
    } catch (e) {
      throw new Error(
        `could not reach freehire API at ${baseUrl()} (${e instanceof Error ? e.message : String(e)})`,
      )
    }

    if (response.status === 429 || response.status >= 500) {
      if (attempt === maxRetries) {
        throw new Error(`freehire API request failed: ${response.status} ${response.statusText}`)
      }
      const backoff = delay + Math.floor(Math.random() * 500)
      const retryAfter = retryAfterMs(response.headers.get("Retry-After"))
      const wait = Math.max(backoff, retryAfter ?? 0)
      if (waited + wait > RETRY_BUDGET_MS) {
        throw new Error(
          `freehire API request failed: ${response.status} ${response.statusText}; retry budget exceeded`,
        )
      }
      await sleep(wait)
      waited += wait
      delay = Math.min(delay * 2, 8000)
      continue
    }
    if (response.status === 404) return null

    const body = (await response.json().catch(() => null)) as Envelope<T> | null
    if (!response.ok) {
      throw new Error(body?.error || `freehire API request failed: ${response.status} ${response.statusText}`)
    }
    if (!body) throw new Error("freehire API returned an unparseable response body")
    return body
  }
  throw new Error("freehire API request failed after retries")
}

export interface FreehireJob {
  public_slug: string
  source: string
  external_id: string
  url: string
  title: string
  company: string
  company_slug: string
  location: string
  description: string
  skills: string[]
  work_mode?: string
  regions: string[]
  countries: string[]
  cities: string[]
  posted_at: string | null
  created_at: string | null
  enrichment: {
    seniority?: string
    category?: string
    employment_type?: string
    salary_min?: number
    salary_max?: number
    salary_currency?: string
    salary_period?: string
  }
}

export type SeekSite = "au" | "nz"

export interface SeekJobResult {
  id: string
  title: string
  company: string | null
  location: string | null
  date: string | null
  url: string
  seek_job_id: string | null
  site: SeekSite | null
  work_mode: string | null
  description: string | null
}

export interface SeekJobDetail extends SeekJobResult {
  seniority: string | null
  employment_type: string | null
  skills: string[]
}

const SEEK_HOST_AU = /(^|\.)seek\.com\.au$/i
const SEEK_HOST_NZ = /(^|\.)seek\.co\.nz$/i

export function seekSiteFromUrl(url: string): SeekSite | null {
  try {
    const host = new URL(url).hostname.replace(/^www\./i, "")
    if (SEEK_HOST_AU.test(host) || host === "seek.com.au") return "au"
    if (SEEK_HOST_NZ.test(host) || host === "seek.co.nz") return "nz"
  } catch {
    return null
  }
  return null
}

export function isSeekUrl(url: string): boolean {
  return seekSiteFromUrl(url) !== null
}

export function seekJobIdFromUrl(url: string): string | null {
  const m = url.match(/\/job\/(\d+)/i)
  return m ? m[1] : null
}

export function dateOnly(iso: string | null | undefined): string | null {
  if (!iso) return null
  const m = iso.match(/^(\d{4}-\d{2}-\d{2})/)
  return m ? m[1] : null
}

function decodeEntities(s: string): string {
  return s
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&nbsp;/g, " ")
    .trim()
}

export function toSeekResult(job: FreehireJob): SeekJobResult | null {
  if (!isSeekUrl(job.url)) return null
  return {
    id: job.public_slug,
    title: decodeEntities(job.title || ""),
    company: job.company ? decodeEntities(job.company) : null,
    location: job.location || null,
    date: dateOnly(job.posted_at) ?? dateOnly(job.created_at),
    url: job.url.split("?")[0],
    seek_job_id: seekJobIdFromUrl(job.url),
    site: seekSiteFromUrl(job.url),
    work_mode: job.work_mode || null,
    description: job.description || null,
  }
}

export function toSeekDetail(job: FreehireJob): SeekJobDetail | null {
  const base = toSeekResult(job)
  if (!base) return null
  return {
    ...base,
    description: job.description || null,
    seniority: job.enrichment?.seniority || null,
    employment_type: job.enrichment?.employment_type || null,
    skills: job.skills || [],
  }
}

/** Parse seek numeric id or freehire slug or full SEEK URL into a detail lookup key. */
export function parseDetailTarget(raw: string): { kind: "slug" | "seekId" | "url"; value: string } {
  const s = raw.trim()
  if (/^https?:\/\//i.test(s)) return { kind: "url", value: s }
  if (/^\d+$/.test(s)) return { kind: "seekId", value: s }
  return { kind: "slug", value: s }
}
