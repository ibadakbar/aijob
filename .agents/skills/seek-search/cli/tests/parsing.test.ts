import { describe, expect, test } from "bun:test"
import {
  isSeekUrl,
  seekJobIdFromUrl,
  seekSiteFromUrl,
  toSeekResult,
  type FreehireJob,
} from "../src/helpers.ts"

function job(over: Partial<FreehireJob> & Pick<FreehireJob, "url" | "public_slug" | "title">): FreehireJob {
  return {
    source: "seek",
    external_id: "1",
    company: "Acme",
    company_slug: "acme",
    location: "Sydney NSW",
    description: "Build React apps",
    skills: ["React"],
    regions: [],
    countries: ["AU"],
    cities: ["Sydney"],
    posted_at: "2026-11-20T00:00:00Z",
    created_at: null,
    enrichment: {},
    ...over,
  }
}

describe("seek URL helpers", () => {
  test("detects AU and NZ hosts", () => {
    expect(isSeekUrl("https://www.seek.com.au/job/96086439")).toBe(true)
    expect(isSeekUrl("https://www.seek.co.nz/job/95418537")).toBe(true)
    expect(isSeekUrl("https://www.linkedin.com/jobs/view/1")).toBe(false)
    expect(seekSiteFromUrl("https://www.seek.com.au/job/1")).toBe("au")
    expect(seekSiteFromUrl("https://seek.co.nz/job/1")).toBe("nz")
  })

  test("extracts numeric SEEK id", () => {
    expect(seekJobIdFromUrl("https://www.seek.com.au/job/96086439?utm_source=x")).toBe("96086439")
    expect(seekJobIdFromUrl("https://example.com/nope")).toBe(null)
  })

  test("toSeekResult keeps SEEK rows only", () => {
    const ok = toSeekResult(
      job({
        public_slug: "senior-react-peoplebank-abc",
        title: "Senior React Developer",
        url: "https://www.seek.com.au/job/96086439?utm_source=freehire.me",
      }),
    )
    expect(ok?.seek_job_id).toBe("96086439")
    expect(ok?.site).toBe("au")
    expect(ok?.url).toBe("https://www.seek.com.au/job/96086439")

    const drop = toSeekResult(
      job({
        public_slug: "other",
        title: "Other",
        url: "https://www.linkedin.com/jobs/view/1",
      }),
    )
    expect(drop).toBe(null)
  })
})
