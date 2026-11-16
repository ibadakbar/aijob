"""Honest coverage reporting — what was searched, failed, or out of scope."""

from __future__ import annotations

from typing import Any, Optional

from .mission import SearchPlan
from .sources import LIVE_SOURCES, STUB_SOURCES


def build_coverage(
    *,
    plan: Optional[SearchPlan] = None,
    source_meta: Optional[dict[str, Any]] = None,
    errors: Optional[list[str]] = None,
    sources_requested: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Summarize research coverage without claiming a full-internet search."""
    meta = source_meta or {}
    requested = list(sources_requested or (plan.sources if plan else []) or [])
    searched: list[str] = []
    failed: list[dict[str, str]] = []
    skipped: list[dict[str, str]] = []
    stubbed: list[str] = []

    for name in requested:
        key = name.lower().strip()
        entry = meta.get(key) or {}
        if entry.get("stub") or entry.get("implemented") is False:
            stubbed.append(key)
            skipped.append({"source": key, "reason": str(entry.get("reason") or "stub")})
            continue
        if entry.get("error"):
            failed.append({"source": key, "error": str(entry["error"])})
            continue
        if entry.get("skipped") or entry.get("incremental") == "fetch_skipped":
            searched.append(key)
            skipped.append(
                {
                    "source": key,
                    "reason": str(
                        entry.get("skipped")
                        or entry.get("incremental")
                        or "skipped"
                    ),
                }
            )
            continue
        if key in meta or key in LIVE_SOURCES:
            searched.append(key)

    # Errors that mention a source name
    for err in errors or []:
        lower = err.lower()
        for key in requested:
            if key in lower and not any(f["source"] == key for f in failed):
                failed.append({"source": key, "error": err})

    not_in_scope = list(plan.sources_not_in_scope) if plan else sorted(
        set(STUB_SOURCES.keys()) | {s for s in LIVE_SOURCES if s not in requested}
    )

    return {
        "claim": (
            plan.claim
            if plan
            else (
                "Partial research over configured public adapters - "
                "not a claim that the entire internet was searched."
            )
        ),
        "opportunity_kinds": list(plan.opportunity_kinds) if plan else [],
        "sources_requested": requested,
        "sources_searched": sorted(set(searched)),
        "sources_failed": failed,
        "sources_skipped": skipped,
        "sources_stubbed": stubbed,
        "sources_not_in_scope": not_in_scope,
        "live_adapters_available": sorted(LIVE_SOURCES.keys()),
        "notes": list(plan.notes) if plan else [],
        "max_results": plan.max_results if plan else None,
        "freshness_days": plan.freshness_days if plan else None,
        "min_verification": plan.min_verification if plan else None,
    }
