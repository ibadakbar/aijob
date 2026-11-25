"""Compose freshness + Path A/B + contact ladder before Excel write."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from agent.models.opportunity import OpportunityRecord, norm_key
from agent.quality.contact_ladder import apply_contact_ladder_to_record
from agent.quality.freshness import (
    MAX_LISTING_AGE_DAYS,
    enrich_posted_date,
    index_from_excel_rows,
    is_repeat,
    is_too_old,
    merge_external_seen,
    register_kept,
)
from agent.quality.geo_gate import geo_drop_reason
from agent.quality.path_gate import path_gate
try:
    from agent.scoring.scores import score_opportunity
except ImportError:  # pragma: no cover — Streamlit stale module cache
    from agent.scoring.scores import score_client, score_job

    def score_opportunity(rec):  # type: ignore[misc]
        otype = (getattr(rec, "opportunity_type", "") or "").lower()
        if otype in ("job", "contract"):
            return score_job(rec)
        return score_client(rec)


@dataclass
class GateResult:
    kept: list[OpportunityRecord] = field(default_factory=list)
    dropped: list[dict[str, str]] = field(default_factory=list)
    stats: dict[str, int] = field(default_factory=dict)


def apply_quality_gates(
    records: list[OpportunityRecord],
    *,
    existing_rows: list[OpportunityRecord] | None = None,
    kill_days: int = 14,
    max_age_days: int = MAX_LISTING_AGE_DAYS,
    enforce_path: bool = True,
    check_mx: bool = False,
    allow_excel_refresh: bool = True,
) -> GateResult:
    """Filter + enrich records. Call before upsert_opportunities."""
    index = index_from_excel_rows(existing_rows or [])
    excel_urls = set(index.get("urls") or set())
    excel_pairs = set(index.get("pairs") or set())
    merge_external_seen(index)

    result = GateResult()
    counts = {
        "input": len(records),
        "kept": 0,
        "drop_repeat": 0,
        "drop_stale": 0,
        "drop_geo": 0,
        "drop_path": 0,
        "drop_inferred_email": 0,
        "drop_no_signal": 0,
    }

    for rec in records:
        url = (rec.source_url or "").rstrip("/")
        pair = (norm_key(rec.company), norm_key(rec.role_or_title))
        in_excel = (url and url in excel_urls) or (pair in excel_pairs and pair != ("", ""))

        # Infer posted date (LinkedIn snowflake / "4mo") before age + dedupe checks
        enrich_posted_date(rec)

        # Hard geo block — no India / India-primary listings
        geo_why = geo_drop_reason(rec)
        if geo_why:
            counts["drop_geo"] += 1
            result.dropped.append(
                {"company": rec.company, "title": rec.role_or_title, "reason": geo_why, "url": url}
            )
            continue

        # Hard 3-month ceiling — even for Excel refresh (do not keep stale rows alive)
        stale, stale_why = is_too_old(rec, max_age_days=max_age_days)
        if stale:
            counts["drop_stale"] += 1
            result.dropped.append(
                {"company": rec.company, "title": rec.role_or_title, "reason": stale_why, "url": url}
            )
            continue

        # Contact ladder first (strip inferred emails)
        verdict = apply_contact_ladder_to_record(rec, check_mx=check_mx)
        if verdict.drop:
            counts["drop_inferred_email"] += 1
            result.dropped.append(
                {"company": rec.company, "title": rec.role_or_title, "reason": verdict.drop_reason}
            )
            continue

        if enforce_path:
            keep, reason, _path = path_gate(rec)
            if not keep:
                counts["drop_path"] += 1
                result.dropped.append(
                    {"company": rec.company, "title": rec.role_or_title, "reason": reason, "url": url}
                )
                continue

        if not in_excel or not allow_excel_refresh:
            drop, why = is_repeat(rec, index, kill_days=kill_days, max_age_days=max_age_days)
            # is_repeat treats excel urls as seen — override when refreshing Excel rows
            if drop and in_excel and allow_excel_refresh and why in (
                "seen_url",
                "seen_company_title",
                "seen_fingerprint",
            ):
                drop = False
            if drop and why.startswith("stale_"):
                counts["drop_stale"] += 1
                result.dropped.append(
                    {"company": rec.company, "title": rec.role_or_title, "reason": why, "url": url}
                )
                continue
            if drop and not in_excel:
                counts["drop_repeat"] += 1
                result.dropped.append(
                    {"company": rec.company, "title": rec.role_or_title, "reason": why, "url": url}
                )
                continue

        # Rescore with hireability rules
        score_opportunity(rec)

        # Kill scrapey "maybe" with no contact and weak intent (clients/founders)
        otype = (rec.opportunity_type or "").lower()
        if otype in ("client", "founder", "freelance") and (rec.intent_classification or "") in (
            "",
            "POTENTIAL_FIT",
        ):
            if not rec.contact_email and not rec.linkedin_url and not rec.source_url:
                counts["drop_no_signal"] += 1
                result.dropped.append(
                    {
                        "company": rec.company,
                        "title": rec.role_or_title,
                        "reason": "no_demand_no_contact",
                    }
                )
                continue

        register_kept(rec, index)
        result.kept.append(rec)
        counts["kept"] += 1

    result.stats = counts
    return result
