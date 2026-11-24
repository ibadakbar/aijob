import { describe, expect, test } from "bun:test"
import { parseJSON, runCLI } from "./helpers.ts"

describe("seek-cli live search", () => {
  test("search React AU returns SEEK urls when index has them", async () => {
    const r = await runCLI([
      "search",
      "-q",
      "React",
      "--site",
      "au",
      "--jobage",
      "30",
      "--limit",
      "5",
      "--format",
      "json",
    ])
    // Live index may be empty for SEEK on a given day — exit 0 with count 0 is OK.
    expect(r.exitCode).toBe(0)
    const data = parseJSON<{
      meta: { count: number; source: string }
      results: Array<{ id: string; title: string; url: string }>
    }>(r)
    expect(data.meta.source).toBe("freehire-index-of-seek")
    expect(Array.isArray(data.results)).toBe(true)
    for (const row of data.results) {
      expect(row.id).toBeTruthy()
      expect(row.title).toBeTruthy()
      expect(row.url).toMatch(/seek\.com\.au\/job\//i)
    }
  }, 30000)
})
