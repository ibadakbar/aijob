import {
  apiGet,
  isSeekUrl,
  parseDetailTarget,
  seekJobIdFromUrl,
  toSeekDetail,
  writeError,
  type FreehireJob,
  type SeekJobDetail,
} from "../helpers.js"

const DETAIL_PATH = "/api/v1/jobs"
const SEARCH_PATH = "/api/v1/agent/jobs/search"

export interface DetailOpts {
  target: string
  format: "json" | "plain"
}

async function bySlug(slug: string): Promise<SeekJobDetail | null> {
  const envelope = await apiGet<FreehireJob>(`${DETAIL_PATH}/${encodeURIComponent(slug)}`)
  if (!envelope?.data) return null
  return toSeekDetail(envelope.data)
}

async function findBySeekUrlOrId(raw: string): Promise<SeekJobDetail | null> {
  const seekId = /^\d+$/.test(raw) ? raw : seekJobIdFromUrl(raw)
  const needle = seekId ? `/job/${seekId}` : raw

  // freehire search sometimes matches the numeric id in the indexed URL.
  const q = seekId ?? raw
  const p = new URLSearchParams({
    q,
    limit: "25",
    offset: "0",
    description_format: "text",
  })
  p.append("countries", "AU")
  p.append("countries", "NZ")
  const envelope = await apiGet<FreehireJob[]>(`${SEARCH_PATH}?${p}`)
  const batch = Array.isArray(envelope?.data) ? envelope!.data : []
  for (const job of batch) {
    if (!isSeekUrl(job.url)) continue
    if (seekId && seekJobIdFromUrl(job.url) === seekId) return toSeekDetail(job)
    if (job.url.includes(needle)) return toSeekDetail(job)
  }
  return null
}

function renderPlain(d: SeekJobDetail): string {
  const lines = [
    d.title,
    `${d.company ?? "—"} · ${d.location ?? "—"} · site=${d.site ?? "—"}`,
    `SEEK job: ${d.seek_job_id ?? "—"}`,
    `URL: ${d.url}`,
    `id (detail slug): ${d.id}`,
    d.seniority ? `Seniority: ${d.seniority}` : null,
    d.employment_type ? `Employment: ${d.employment_type}` : null,
    d.work_mode ? `Work mode: ${d.work_mode}` : null,
    "",
    d.description?.trim() || "(no description in index)",
  ]
  return lines.filter((x) => x !== null).join("\n")
}

export async function runDetail(opts: DetailOpts): Promise<number> {
  try {
    const parsed = parseDetailTarget(opts.target)
    let detail: SeekJobDetail | null = null

    if (parsed.kind === "slug") {
      detail = await bySlug(parsed.value)
      if (detail && !isSeekUrl(detail.url)) {
        writeError("That slug is not a SEEK-hosted listing", "NOT_SEEK")
        return 1
      }
    } else {
      detail = await findBySeekUrlOrId(parsed.value)
      if (!detail && parsed.kind === "url") {
        // Last resort: if URL somehow mapped to a freehire slug path — unlikely.
        detail = null
      }
    }

    if (!detail) {
      writeError(
        "SEEK listing not found in freehire index (direct SEEK fetch is blocked by Cloudflare/robots)",
        "NOT_FOUND",
      )
      return 1
    }

    if (opts.format === "plain") {
      process.stdout.write(renderPlain(detail) + "\n")
    } else {
      process.stdout.write(JSON.stringify(detail, null, 2) + "\n")
    }
    return 0
  } catch (e) {
    writeError(e instanceof Error ? e.message : String(e), "FETCH_FAILED")
    return 1
  }
}
