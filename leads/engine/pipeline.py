"""Orchestrate criteria → fetch → enrich → score → dedupe → outreach → persist."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .agency_partnership import attach_partnership
from .confidence import confidence_of, decide_status
from .contact_path import attach_contact_path
from .contacts import build_contacts_from_listing
from .coverage import build_coverage
from .criteria import parse_prompt
from .dedupe import dedupe_leads, normalize_url
from .evidence_log import append_evidence
from .export import export_run
from .incremental import (
    content_fingerprint,
    fetch_is_fresh,
    load_state,
    merged_records,
    query_fingerprint,
    remember_fetch,
    runtime_paths,
    save_state,
    select_records,
)
from .mission import SearchPlan, plan_mission
from .model import Lead, LeadScores, OutreachDraft, SearchCriteria
from .opportunity_radar import attach_opportunity
from .outreach import generate_outreach
from .persist import load_store, upsert_leads
from .recovery import (
    is_transient,
    load_run,
    mark_completed,
    mark_failed,
    retry_call,
    save_run,
    start_run,
)
from .research_cache import TIER_EXTRACT, TIER_RESEARCH, ResearchCache, model_tier_for
from .score import fit_score, intent_rank_key, score_lead
from .sources import LIVE_SOURCES, STUB_SOURCES
from .verify import attach_verification

CANDIDATE_NAME = "Ibad Akbar"


def discover_leads(
    prompt: str = "",
    *,
    criteria: Optional[SearchCriteria] = None,
    sources: Optional[list[str]] = None,
    persist: bool = True,
    export: bool = True,
    store_path: Optional[Path] = None,
    fixture_path: Optional[Path] = None,
    check_mx: bool = False,
    skip_known: bool = True,
    generate_drafts: bool = True,
    incremental: bool = True,
    resume_run: Optional[str] = None,
    qualify_threshold: float = 0.72,
    retry_attempts: int = 3,
    retry_delay: float = 0.0,
) -> dict[str, Any]:
    """Run the lead engine. Returns ranked leads + meta. Never sends messages.

    Incremental discovery (default) reuses a fresh identical fetch and returns
    only new or changed vacancies. Uncertain leads are stored as
    ``needs_review`` instead of being auto-qualified.
    """
    crit = criteria or parse_prompt(prompt)
    if prompt and criteria is None:
        crit = parse_prompt(prompt)

    plan: SearchPlan = plan_mission(prompt or crit.raw_prompt or "", criteria=crit)
    # Keep criteria aligned with mission planner (e.g. limit up to 300)
    crit = plan.criteria

    paths = runtime_paths(store_path)
    state = load_state(paths["state"]) if persist else {"version": 1, "sources": {}, "logged": {}}
    cache = ResearchCache(paths["cache"]) if persist else ResearchCache(paths["cache"])
    if not persist:
        cache.data = {"version": 1, "vacancies": {}, "companies": {}, "domains": {}, "ai": {}}

    resuming = bool(resume_run)
    if resuming:
        run = load_run(paths["runs"], resume_run or "")
        if run is None:
            raise FileNotFoundError(f"discovery run not found: {resume_run}")
        pending = [s for s in run.get("sources") or [] if s not in set(run.get("completed") or [])]
        if sources:
            wanted_set = {s.lower().strip() for s in sources}
            wanted = [s for s in pending if s in wanted_set]
        else:
            wanted = list(pending)
        run["status"] = "running"
    else:
        if sources is not None:
            wanted = [s.lower().strip() for s in sources if s.strip()]
        else:
            wanted = list(plan.sources) or ["remotive", "arbeitnow"]
        if sources == ["fixture"] or (fixture_path and sources is None and not prompt):
            wanted = ["fixture"]
        run = {
            "id": datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f"),
            "status": "running",
            "sources": list(wanted),
            "completed": [],
            "failed": {},
            "query": query_fingerprint(crit, ",".join(wanted)),
            "mission": plan.to_dict(),
        }
        if persist:
            run = start_run(
                paths["runs"],
                run_id=run["id"],
                sources=list(wanted),
                query=run["query"],
            )
            run["mission"] = plan.to_dict()
            save_run(paths["runs"], run)

    force_fetch = (not incremental) or (not skip_known)
    drop_unchanged = incremental and skip_known
    previous_records = merged_records(state)

    collected: list[Lead] = []
    errors: list[str] = []
    source_meta: dict[str, Any] = {}
    incremental_meta: dict[str, Any] = {
        "enabled": drop_unchanged,
        "new": 0,
        "changed": 0,
        "unchanged": 0,
        "fetch_skipped": [],
    }

    try:
        if resuming and not wanted:
            payload = _empty_payload(
                crit,
                run=run,
                errors=errors,
                source_meta=source_meta,
                incremental_meta=incremental_meta,
                note="Run already completed. Nothing left to resume.",
            )
            run["status"] = "complete"
            return payload

        for name in wanted:
            key = name.lower().strip()
            if key in STUB_SOURCES:
                source_meta[key] = STUB_SOURCES[key].fetch(crit).meta
                mark_completed(run, key)
                _checkpoint(persist, paths["runs"], run)
                continue
            adapter_cls = LIVE_SOURCES.get(key)
            if adapter_cls is None:
                errors.append(f"unknown source: {key}")
                mark_failed(run, key, ValueError(f"unknown source: {key}"), attempts=1)
                source_meta[key] = {"error": f"unknown source: {key}", "attempts": 1}
                continue

            query = query_fingerprint(crit, key)
            entry = (state.get("sources") or {}).get(key) or {}
            if not force_fetch and fetch_is_fresh(entry, query):
                skipped = len(entry.get("records") or {})
                source_meta[key] = {
                    "incremental": "fetch_skipped",
                    "fetched_at": entry.get("fetched_at"),
                    "unchanged": skipped,
                }
                incremental_meta["fetch_skipped"].append(key)
                incremental_meta["unchanged"] += skipped
                mark_completed(run, key)
                _checkpoint(persist, paths["runs"], run)
                continue

            adapter = _build_adapter(key, adapter_cls, fixture_path)
            kwargs: dict[str, Any] = {}
            if fixture_path:
                kwargs["fixture_path"] = fixture_path
            try:
                result, attempts = retry_call(
                    lambda a=adapter, kw=kwargs: _fetch_or_raise(a, crit, kw),
                    attempts=retry_attempts,
                    base_delay=retry_delay,
                )
            except Exception as exc:  # noqa: BLE001
                used = retry_attempts if is_transient(exc) else 1
                errors.append(f"{key}: {exc}")
                mark_failed(run, key, exc, attempts=used)
                source_meta[key] = {"error": str(exc), "attempts": used, "transient": is_transient(exc)}
                _checkpoint(persist, paths["runs"], run)
                continue

            for lead in result.leads:
                lead.content_hash = lead.content_hash or content_fingerprint(lead)
            if persist:
                remember_fetch(state, source=key, query=query, leads=result.leads)
            collected.extend(result.leads)
            errors.extend(result.errors)
            source_meta[key] = {"count": len(result.leads), "attempts": attempts, **result.meta}
            mark_completed(run, key)
            _checkpoint(persist, paths["runs"], run)

        for sname, stub in STUB_SOURCES.items():
            if sname not in source_meta:
                source_meta[sname] = stub.fetch(crit).meta

        if check_mx:
            for lead in collected:
                desc = " ".join(e.excerpt or e.summary for e in lead.evidence)
                lead.contacts = build_contacts_from_listing(
                    description=desc,
                    listing_url=lead.url,
                    company=lead.company,
                    check_mx=True,
                )

        deduped = dedupe_leads(collected)
        store_index = _store_index(store_path) if persist and drop_unchanged else {}
        fresh, changed, unchanged = select_records(
            deduped,
            previous_records=previous_records,
            store_index=store_index,
        )
        incremental_meta["new"] += len(fresh)
        incremental_meta["changed"] += len(changed)
        incremental_meta["unchanged"] += len(unchanged)
        work = fresh + changed if drop_unchanged else fresh + changed + unchanged

        for lead in work:
            _prepare_lead(
                lead,
                crit=crit,
                cache=cache,
                generate_drafts=generate_drafts,
                qualify_threshold=qualify_threshold,
            )

        work.sort(
            key=lambda item: (
                {"A": 0, "B": 1, "C": 2, "D": 3}.get(
                    str((item.raw or {}).get("quality_tier") or "C"), 2
                ),
                intent_rank_key(item.intent),
                -(item.scores.overall if item.scores else 0.0),
                item.expired,
            )
        )
        limited = [item for item in work if not item.expired][: crit.limit]
        if len(limited) < crit.limit:
            limited.extend([item for item in work if item.expired][: crit.limit - len(limited)])

        qualified = sum(1 for item in limited if item.status == "qualified")
        review_queue = sum(1 for item in limited if item.status == "needs_review")

        coverage = build_coverage(
            plan=plan,
            source_meta=source_meta,
            errors=errors,
            sources_requested=wanted,
        )
        source_meta["coverage"] = coverage
        source_meta["mission"] = plan.to_dict()

        persist_info: dict[str, Any] = {}
        if persist:
            if limited:
                persist_info = upsert_leads(limited, store_path)
            append_evidence(paths["evidence"], limited, logged=state.setdefault("logged", {}))
            save_state(paths["state"], state)
            cache.save()

        export_paths: dict[str, Any] = {}
        if export and limited:
            export_paths = {
                k: str(v) for k, v in export_run(limited, crit, source_meta=source_meta).items()
            }

        run["status"] = "partial" if run.get("failed") else "complete"
        return {
            "date": date.today().isoformat(),
            "criteria": crit.to_dict(),
            "mission": plan.to_dict(),
            "coverage": coverage,
            "results": [item.to_dict() for item in limited],
            "leads": limited,
            "meta": _meta(
                collected=collected,
                deduped=deduped,
                limited=limited,
                errors=errors,
                source_meta=source_meta,
                persist_info=persist_info,
                export_paths=export_paths,
                incremental_meta=incremental_meta,
                cache=cache,
                run=run,
                qualified=qualified,
                review_queue=review_queue,
                resumed=resuming,
            ),
        }
    except Exception:
        if run is not None:
            run["status"] = "interrupted"
        raise
    finally:
        _checkpoint(persist, paths["runs"], run)


def _build_adapter(key: str, adapter_cls: type, fixture_path: Optional[Path]) -> Any:
    if key == "fixture":
        from .sources.fixture import FixtureSource

        return FixtureSource(path=fixture_path) if fixture_path else FixtureSource()
    return adapter_cls()


def _fetch_or_raise(adapter: Any, crit: SearchCriteria, kwargs: dict[str, Any]) -> Any:
    result = adapter.fetch(crit, **kwargs)
    if result.errors and not result.leads and is_transient(RuntimeError("; ".join(result.errors))):
        raise TimeoutError("; ".join(result.errors))
    return result


def _checkpoint(persist: bool, runs_dir: Path, run: Optional[dict[str, Any]]) -> None:
    if persist and run and run.get("id"):
        save_run(runs_dir, run)


def _store_index(store_path: Optional[Path]) -> dict[str, dict[str, Any]]:
    data = load_store(store_path)
    index: dict[str, dict[str, Any]] = {}
    for row in (data.get("leads") or {}).values():
        if not isinstance(row, dict):
            continue
        if row.get("id"):
            index[str(row["id"])] = row
        url = normalize_url(row.get("url") or "")
        if url:
            index[url] = row
    return index


def _scores_from(payload: dict[str, Any]) -> LeadScores:
    return LeadScores(
        intent_score=float(payload.get("intent_score") or 0),
        fit_score=float(payload.get("fit_score") or 0),
        contact_score=float(payload.get("contact_score") or 0),
        freshness_score=float(payload.get("freshness_score") or 0),
        overall=float(payload.get("overall") or 0),
        reasons=list(payload.get("reasons") or []),
    )


def _outreach_from(payload: dict[str, Any]) -> OutreachDraft:
    return OutreachDraft(**{k: v for k, v in payload.items() if k in OutreachDraft.__dataclass_fields__})


def _prepare_lead(
    lead: Lead,
    *,
    crit: SearchCriteria,
    cache: ResearchCache,
    generate_drafts: bool,
    qualify_threshold: float,
) -> None:
    # Intelligence layer: radar → agency partnership → contact path (before scoring).
    attach_opportunity(lead, criteria=crit)
    attach_partnership(lead, criteria=crit)
    attach_contact_path(lead)
    attach_verification(lead, freshness_days=crit.freshness_days)

    _, reasons = fit_score(
        title=lead.title,
        description=" ".join(lead.technical_requirements),
        requirements=lead.technical_requirements,
        criteria=crit,
    )
    lead.profile_match_reasons = list(dict.fromkeys(list(lead.profile_match_reasons) + reasons))
    if not lead.content_hash:
        lead.content_hash = content_fingerprint(lead)

    cached = cache.vacancy(lead.url, lead.content_hash)
    company_hit = False if cached else cache.company_cached(lead)
    if cached and cached.get("scores"):
        lead.scores = _scores_from(cached["scores"])
        tier = str(cached.get("model_tier") or TIER_EXTRACT)
        # Re-attach nested intelligence if cache only stored scores/outreach
        if lead.opportunity is None:
            attach_opportunity(lead, criteria=crit)
        if lead.partnership is None:
            attach_partnership(lead, criteria=crit)
        if lead.preferred_contact is None:
            attach_contact_path(lead)
    else:
        tier = model_tier_for(lead, company_cached=company_hit)

        def _score(current: Lead = lead) -> dict[str, Any]:
            return score_lead(current, crit).to_dict()

        payload, _hit = cache.cached_compute(
            task="score",
            tier=TIER_EXTRACT,
            content_hash=lead.content_hash,
            compute=_score,
        )
        lead.scores = _scores_from(payload)

    confidence, _why = confidence_of(lead)
    lead.confidence = round(confidence, 3)
    status, review_reason = decide_status(lead, confidence, threshold=qualify_threshold)
    if lead.status == "new":
        lead.status = status  # type: ignore[assignment]
    lead.review_reason = review_reason
    # Partnership drafts are useful even while in review when fit is explicit.
    partnership_ready = bool(
        lead.partnership
        and lead.partnership.is_agency
        and lead.partnership.partnership_fit != "none"
        and lead.intent == "EXPLICIT_DEMAND"
    )
    if tier == TIER_RESEARCH:
        lead.review_reason = (lead.review_reason + " Strong-model research was deferred.").strip()
        lead.raw["research_deferred"] = True
        lead.raw["model_tier"] = TIER_RESEARCH
    else:
        lead.raw["research_deferred"] = False
        lead.raw["model_tier"] = TIER_EXTRACT
        if company_hit:
            lead.review_reason = (
                lead.review_reason + " Company/domain research reused from cache."
            ).strip()
        if generate_drafts and lead.outreach is None and (
            lead.status == "qualified" or partnership_ready
        ):
            if cached and cached.get("outreach"):
                lead.outreach = _outreach_from(cached["outreach"])
            else:
                def _draft(current: Lead = lead) -> dict[str, Any]:
                    return generate_outreach(current, candidate_name=CANDIDATE_NAME).to_dict()

                draft, _hit = cache.cached_compute(
                    task="outreach",
                    tier=TIER_EXTRACT,
                    content_hash=lead.content_hash,
                    compute=_draft,
                )
                lead.outreach = _outreach_from(draft)
    if not cached:
        cache.remember_vacancy(lead, tier=tier)
        cache.remember_company(lead, tier=tier)


def _meta(
    *,
    collected: list[Lead],
    deduped: list[Lead],
    limited: list[Lead],
    errors: list[str],
    source_meta: dict[str, Any],
    persist_info: dict[str, Any],
    export_paths: dict[str, Any],
    incremental_meta: dict[str, Any],
    cache: ResearchCache,
    run: dict[str, Any],
    qualified: int,
    review_queue: int,
    resumed: bool,
    note: str = "",
) -> dict[str, Any]:
    meta = {
        "raw_count": len(collected),
        "deduped_count": len(deduped),
        "returned": len(limited),
        "errors": errors,
        "sources": source_meta,
        "persist": persist_info,
        "export": export_paths,
        "send_approved_default": False,
        "incremental": incremental_meta,
        "cache": {
            "vacancy_hits": cache.vacancy_hits,
            "company_hits": cache.company_hits,
            "ai_hits": cache.ai_hits,
        },
        "qualified": qualified,
        "review_queue": review_queue,
        "run_id": run.get("id"),
        "run_status": run.get("status"),
        "failed_sources": run.get("failed") or {},
        "resumed": resumed,
    }
    if note:
        meta["note"] = note
    return meta


def _empty_payload(
    crit: SearchCriteria,
    *,
    run: dict[str, Any],
    errors: list[str],
    source_meta: dict[str, Any],
    incremental_meta: dict[str, Any],
    note: str,
) -> dict[str, Any]:
    return {
        "date": date.today().isoformat(),
        "criteria": crit.to_dict(),
        "results": [],
        "leads": [],
        "meta": _meta(
            collected=[],
            deduped=[],
            limited=[],
            errors=errors,
            source_meta=source_meta,
            persist_info={},
            export_paths={},
            incremental_meta=incremental_meta,
            cache=ResearchCache(Path(".")),
            run=run,
            qualified=0,
            review_queue=0,
            resumed=True,
            note=note,
        ),
    }


__all__ = ["discover_leads", "plan_mission"]
