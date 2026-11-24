import { describe, expect, test } from "bun:test"
import { runCLI } from "./helpers.ts"

describe("seek-cli flag validation", () => {
  test("unknown command exits 1 with JSON error", async () => {
    const r = await runCLI(["nope"])
    expect(r.exitCode).toBe(1)
    const err = JSON.parse(r.stderr)
    expect(err.code).toBe("BAD_ARG")
  })

  test("bad --site exits 1", async () => {
    const r = await runCLI(["search", "-q", "React", "--site", "uk"])
    expect(r.exitCode).toBe(1)
    expect(JSON.parse(r.stderr).code).toBe("BAD_ARG")
  })

  test("detail without target exits 1", async () => {
    const r = await runCLI(["detail"])
    expect(r.exitCode).toBe(1)
    expect(JSON.parse(r.stderr).code).toBe("BAD_ARG")
  })

  test("help exits 0", async () => {
    const r = await runCLI(["help"])
    expect(r.exitCode).toBe(0)
    expect(r.stdout).toContain("seek-cli")
  })
})
