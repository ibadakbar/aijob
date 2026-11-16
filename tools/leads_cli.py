#!/usr/bin/env python3
"""CLI for the evidence-based lead generation engine.

Examples (Windows: python, not python3):
  python tools/leads_cli.py discover --prompt "Find 10 React freelance projects" --sources fixture
  python tools/leads_cli.py discover --prompt "..." --full
  python tools/leads_cli.py review --queue
  python tools/leads_cli.py failures
  python tools/leads_cli.py discover --resume <run-id> --yes
  python tools/leads_cli.py evidence <id>
  python tools/leads_cli.py sources
  python tools/leads_cli.py review
  python tools/leads_cli.py export --status shortlisted
  python tools/leads_cli.py outreach <id>
  python tools/leads_cli.py outcome <id> --status contacted --notes "Sent email"
  python tools/leads_cli.py followup

Never sends external messages. Outreach drafts always have send_approved=false.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from leads.engine.criteria import needs_clarification, parse_prompt  # noqa: E402
from leads.engine.export import export_run  # noqa: E402
from leads.engine.mission import plan_mission  # noqa: E402
from leads.engine.model import Lead, SearchCriteria  # noqa: E402
from leads.engine.outreach import generate_outreach  # noqa: E402
from leads.engine.evidence_log import read_evidence  # noqa: E402
from leads.engine.incremental import runtime_paths  # noqa: E402
from leads.engine.persist import (  # noqa: E402
    DEFAULT_STORE,
    due_followups,
    get_lead,
    list_leads,
    save_outreach,
    set_status,
)
from leads.engine.pipeline import discover_leads  # noqa: E402
from leads.engine.recovery import list_failures  # noqa: E402
from leads.engine.sources import list_sources  # noqa: E402


def _print_summary(payload: dict) -> None:
    meta = payload["meta"]
    cov = payload.get("coverage") or (meta.get("sources") or {}).get("coverage") or {}
    mission = payload.get("mission") or {}
    if mission.get("opportunity_kinds"):
        print(
            "Mission: kinds="
            + ",".join(mission.get("opportunity_kinds") or [])
            + f"  sources={','.join(mission.get('sources') or [])}"
            + f"  max={mission.get('max_results')}"
        )
    if cov.get("claim"):
        print(f"Coverage: {cov.get('claim')}")
        searched = cov.get("sources_searched") or []
        failed = cov.get("sources_failed") or []
        if searched:
            print(f"  Searched: {', '.join(searched)}")
        if failed:
            print(f"  Failed: {len(failed)}")
        not_scope = cov.get("sources_not_in_scope") or []
        if not_scope:
            print(f"  Not in scope this run: {', '.join(not_scope[:12])}"
                  + ("…" if len(not_scope) > 12 else ""))
    print(
        f"Leads {payload['date']}: {meta['returned']} returned "
        f"(raw {meta['raw_count']}, deduped {meta['deduped_count']})."
    )
    inc = meta.get("incremental") or {}
    if inc.get("fetch_skipped"):
        print(
            "Incremental: reused the last fetch for "
            f"{', '.join(inc['fetch_skipped'])} "
            f"({inc.get('unchanged', 0)} unchanged). Use --full to search again."
        )
    elif inc.get("enabled"):
        print(
            f"Incremental: {inc.get('new', 0)} new, {inc.get('changed', 0)} changed, "
            f"{inc.get('unchanged', 0)} unchanged."
        )
    print(
        f"Qualified {meta.get('qualified', 0)}; review queue {meta.get('review_queue', 0)}."
    )
    if meta.get("run_id"):
        print(f"Run {meta.get('run_id')} ({meta.get('run_status')}).")
    if meta.get("errors"):
        print(f"Source errors: {len(meta['errors'])}")
        for err in meta["errors"][:5]:
            print(f"  - {err}")
    if meta.get("failed_sources"):
        print("Failed sources can be resumed with --resume", meta.get("run_id"))
    if meta.get("export"):
        print("Export:")
        for k, v in meta["export"].items():
            print(f"  {k}: {v}")
    print()
    print(
        f"{'#':>3} {'Tier':<4} {'Intent':<16} {'Fit':>5} {'All':>5}  "
        f"{'Type':<10} Company / Title"
    )
    for i, row in enumerate(payload["results"], 1):
        sc = row.get("scores") or {}
        raw = row.get("raw") or {}
        tier = raw.get("quality_tier") or "?"
        emails = [
            c.get("value")
            for c in (row.get("contacts") or [])
            if c.get("channel_type") == "email"
        ]
        email_note = f"  email={emails[0]}" if emails else ""
        print(
            f"{i:3d} {tier:<4} {row.get('intent', ''):<16} {sc.get('fit_score', 0):5.2f} "
            f"{sc.get('overall', 0):5.2f}  {row.get('lead_type', ''):<10} "
            f"{row.get('company', '')} / {row.get('title', '')}{email_note}"
        )
        conf = row.get("confidence")
        conf_txt = f"{conf:.2f}" if isinstance(conf, (int, float)) else "—"
        print(
            f"     {row.get('status', '')}  confidence={conf_txt}  {row.get('review_reason', '')}"
        )
        opp = row.get("opportunity") or {}
        if opp.get("event_type") and opp.get("event_type") != "none":
            print(
                f"     radar={opp.get('event_type')} demand_proven={opp.get('demand_proven')} "
                f"{opp.get('reason', '')[:120]}"
            )
        part = row.get("partnership") or {}
        if part.get("is_agency"):
            print(
                f"     agency_fit={part.get('partnership_fit')} "
                f"{(part.get('pitch_angle') or '')[:100]}"
            )
        pc = row.get("preferred_contact") or {}
        if pc.get("role"):
            print(
                f"     contact={pc.get('role')} via {pc.get('channel_type')} "
                f"{pc.get('value') or '(listing URL)'} — {(pc.get('relevance') or '')[:100]}"
            )
        print(f"     {row.get('url', '')}")


def cmd_discover(args: argparse.Namespace) -> int:
    prompt = args.prompt or ""
    if args.criteria_json:
        data = json.loads(Path(args.criteria_json).read_text(encoding="utf-8"))
        criteria = SearchCriteria(**{k: v for k, v in data.items() if k in SearchCriteria.__dataclass_fields__})
    else:
        criteria = parse_prompt(prompt)
        if args.limit:
            criteria.limit = args.limit
        if args.freshness:
            criteria.freshness_days = args.freshness
    if getattr(args, "mode", "") :
        modes = [m.strip() for m in args.mode.split(",") if m.strip()]
        if modes:
            criteria.discovery_modes = modes  # type: ignore[assignment]

    clarify = needs_clarification(criteria)
    if clarify and not args.yes:
        print(json.dumps({"needs_clarification": clarify, "criteria": criteria.to_dict()}))
        return 2

    if args.resume and not args.sources:
        sources = None
    elif args.sources:
        sources = [s.strip() for s in args.sources.split(",") if s.strip()]
    else:
        # Mission planner chooses Remotive/Arbeitnow/ATS from the prompt
        sources = None
    fixture = Path(args.fixture) if args.fixture else None
    if sources and "fixture" in sources and fixture is None:
        fixture = ROOT / "leads" / "fixtures" / "sample_leads.json"

    try:
        payload = discover_leads(
            prompt=prompt,
            criteria=criteria,
            sources=sources,
            persist=not args.no_persist,
            export=not args.no_export,
            store_path=Path(args.store) if args.store else None,
            fixture_path=fixture,
            check_mx=args.check_mx,
            skip_known=not args.include_known,
            generate_drafts=not args.no_drafts,
            incremental=not args.full,
            resume_run=args.resume or None,
            qualify_threshold=args.threshold,
        )
    except FileNotFoundError as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 1
    # Drop live Lead objects for JSON
    out = {k: v for k, v in payload.items() if k != "leads"}
    if args.format == "json":
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        _print_summary(out)
    return 0


def cmd_review(args: argparse.Namespace) -> int:
    rows = list_leads(
        status=args.status,
        shortlist_only=args.shortlist,
        review_queue=args.queue,
        path=Path(args.store) if args.store else None,
    )
    rows = rows[: args.limit]
    if args.format == "json":
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0
    print(f"Review: {len(rows)} leads")
    for i, row in enumerate(rows, 1):
        sc = row.get("scores") or {}
        print(
            f"{i:3d} [{row.get('status')}] {row.get('intent')} "
            f"fit={sc.get('fit_score', 0):.2f} all={sc.get('overall', 0):.2f} "
            f"confidence={row.get('confidence')} "
            f"{row.get('company')} / {row.get('title')}"
        )
        print(f"     id={row.get('id')}  {row.get('url')}")
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    rows = list_leads(
        status=None if args.status == "all" else args.status,
        shortlist_only=args.status == "shortlisted",
        path=Path(args.store) if args.store else None,
    )
    if args.ids:
        wanted = {x.strip() for x in args.ids.split(",") if x.strip()}
        rows = [r for r in rows if r.get("id") in wanted]
    # Rehydrate minimal Lead objects for export helper
    leads: list[Lead] = []
    for r in rows:
        lead = Lead(
            id=r["id"],
            name=r.get("name") or r.get("company", ""),
            lead_type=r.get("lead_type") or "full_time",
            company=r.get("company") or "",
            title=r.get("title") or "",
            url=r.get("url") or "",
            source=r.get("source") or "",
            intent=r.get("intent") or "POTENTIAL_FIT",
            intent_explanation=r.get("intent_explanation") or "",
            technical_requirements=list(r.get("technical_requirements") or []),
            recommended_service=r.get("recommended_service") or "",
            budget_or_salary=r.get("budget_or_salary"),
            location=r.get("location") or "",
            published_date=r.get("published_date"),
            checked_date=r.get("checked_date"),
            status=r.get("status") or "new",
            expired=bool(r.get("expired")),
            risks=list(r.get("risks") or []),
            next_action=r.get("next_action") or "",
        )
        # Attach nested structures loosely
        from leads.engine.model import ContactChannel, Evidence, LeadScores, OutreachDraft

        lead.evidence = [Evidence(**e) for e in (r.get("evidence") or []) if isinstance(e, dict)]
        lead.contacts = [
            ContactChannel(**{k: v for k, v in c.items() if k in ContactChannel.__dataclass_fields__})
            for c in (r.get("contacts") or [])
            if isinstance(c, dict)
        ]
        if r.get("scores"):
            sc = r["scores"]
            lead.scores = LeadScores(
                intent_score=float(sc.get("intent_score") or 0),
                fit_score=float(sc.get("fit_score") or 0),
                contact_score=float(sc.get("contact_score") or 0),
                freshness_score=float(sc.get("freshness_score") or 0),
                overall=float(sc.get("overall") or 0),
                reasons=list(sc.get("reasons") or []),
            )
        if r.get("outreach"):
            o = r["outreach"]
            lead.outreach = OutreachDraft(
                **{k: v for k, v in o.items() if k in OutreachDraft.__dataclass_fields__}
            )
        leads.append(lead)

    criteria = SearchCriteria(raw_prompt="export", limit=len(leads))
    paths = export_run(leads, criteria, source_meta={"export_only": True}, run_id=args.run_id)
    print(json.dumps({k: str(v) for k, v in paths.items()}, indent=2))
    return 0


def cmd_outreach(args: argparse.Namespace) -> int:
    lead = get_lead(args.id, Path(args.store) if args.store else None)
    if lead is None:
        print(json.dumps({"error": "lead not found", "id": args.id}), file=sys.stderr)
        return 1
    # Build a Lead-like object for generator
    temp = Lead(
        id=lead["id"],
        name=lead.get("name") or "",
        lead_type=lead.get("lead_type") or "full_time",
        company=lead.get("company") or "",
        title=lead.get("title") or "",
        url=lead.get("url") or "",
        source=lead.get("source") or "",
        intent=lead.get("intent") or "POTENTIAL_FIT",
        intent_explanation=lead.get("intent_explanation") or "",
        technical_requirements=list(lead.get("technical_requirements") or []),
        recommended_service=lead.get("recommended_service") or "",
        budget_or_salary=lead.get("budget_or_salary"),
    )
    from leads.engine.model import Evidence

    temp.evidence = [Evidence(**e) for e in (lead.get("evidence") or []) if isinstance(e, dict)]
    draft = generate_outreach(temp)
    if not args.dry_run:
        save_outreach(args.id, draft, Path(args.store) if args.store else None)
    print(json.dumps(draft.to_dict(), indent=2, ensure_ascii=False))
    print("\n# Reminder: send_approved is false. Do not send without explicit user approval.", file=sys.stderr)
    return 0


def cmd_outcome(args: argparse.Namespace) -> int:
    try:
        row = set_status(
            args.id,
            args.status,
            notes=args.notes or "",
            outcome=args.outcome or "",
            path=Path(args.store) if args.store else None,
        )
    except KeyError:
        print(json.dumps({"error": "lead not found", "id": args.id}), file=sys.stderr)
        return 1
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps({"id": args.id, "status": row.get("status"), "ok": True}))
    return 0


def cmd_followup(args: argparse.Namespace) -> int:
    rows = due_followups(path=Path(args.store) if args.store else None)
    if args.format == "json":
        print(json.dumps(rows, indent=2, ensure_ascii=False))
        return 0
    print(f"Due follow-ups: {len(rows)}")
    for row in rows:
        print(f"- {row.get('id')}: {row.get('company')} / {row.get('title')} (due {row.get('next_followup_date')})")
        o = row.get("outreach") or {}
        if o.get("email_body"):
            print("  Draft on file (send_approved=false). Revise with: leads_cli.py outreach <id>")
        else:
            print("  No draft yet — run: python tools/leads_cli.py outreach <id>")
    return 0


def cmd_sources(_args: argparse.Namespace) -> int:
    rows = list_sources()
    if _args.format == "json":
        print(json.dumps(rows, indent=2, ensure_ascii=False))
        return 0
    print(f"Sources: {len(rows)}")
    for row in rows:
        state = "live" if row.get("implemented") else "stub"
        print(f"- {row.get('name')} [{state}] {row.get('notes')}")
    return 0


def cmd_failures(args: argparse.Namespace) -> int:
    paths = runtime_paths(Path(args.store) if args.store else None)
    rows = list_failures(paths["runs"])
    if args.format == "json":
        print(json.dumps(rows, indent=2, ensure_ascii=False))
        return 0
    print(f"Failed sources: {len(rows)}")
    for row in rows:
        print(
            f"- run {row.get('run_id')}  {row.get('source')}: {row.get('error')} "
            f"(attempts={row.get('attempts')}, transient={row.get('transient')})"
        )
    return 0


def cmd_evidence(args: argparse.Namespace) -> int:
    paths = runtime_paths(Path(args.store) if args.store else None)
    rows = read_evidence(paths["evidence"], args.id)
    print(json.dumps(rows, indent=2, ensure_ascii=False))
    return 0 if rows else 1


def cmd_parse(args: argparse.Namespace) -> int:
    criteria = parse_prompt(args.prompt or "")
    plan = plan_mission(args.prompt or "", criteria=criteria)
    print(
        json.dumps(
            {
                "criteria": criteria.to_dict(),
                "mission": plan.to_dict(),
                "clarify": needs_clarification(criteria),
            },
            indent=2,
        )
    )
    return 0


def cmd_plan(args: argparse.Namespace) -> int:
    """Show the structured research mission without fetching."""
    plan = plan_mission(args.prompt or "")
    print(json.dumps(plan.to_dict(), indent=2, ensure_ascii=False))
    return 0


def _add_store_arg(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--store",
        default=str(DEFAULT_STORE),
        help="Path to leads_store.json",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_disc = sub.add_parser("discover", help="Discover and qualify leads")
    _add_store_arg(p_disc)
    p_disc.add_argument("--prompt", default="", help="Natural-language search request")
    p_disc.add_argument(
        "--sources",
        default=None,
        help="Comma-separated sources (default: mission planner — remotive,arbeitnow,greenhouse,ashby,lever)",
    )
    p_disc.add_argument("--limit", type=int)
    p_disc.add_argument("--freshness", type=int)
    p_disc.add_argument("--fixture", help="Fixture JSON path (for --sources fixture)")
    p_disc.add_argument("--criteria-json", help="Load SearchCriteria fields from JSON")
    p_disc.add_argument("--format", choices=("summary", "json"), default="summary")
    p_disc.add_argument("--no-persist", action="store_true")
    p_disc.add_argument("--no-export", action="store_true")
    p_disc.add_argument("--no-drafts", action="store_true")
    p_disc.add_argument("--include-known", action="store_true")
    p_disc.add_argument("--full", action="store_true", help="Repeat the full search instead of incremental discovery")
    p_disc.add_argument("--resume", default="", help="Resume a run id, retrying sources that did not finish")
    p_disc.add_argument("--threshold", type=float, default=0.72, help="Confidence required to auto-qualify")
    p_disc.add_argument(
        "--mode",
        default="",
        help="Discovery modes: jobs,radar,agency (comma-separated). Also inferred from --prompt.",
    )
    p_disc.add_argument("--check-mx", action="store_true")
    p_disc.add_argument("--yes", action="store_true", help="Skip clarification gate")
    p_disc.set_defaults(func=cmd_discover)

    p_rev = sub.add_parser("review", help="Review stored leads")
    _add_store_arg(p_rev)
    p_rev.add_argument("--status")
    p_rev.add_argument("--shortlist", action="store_true")
    p_rev.add_argument("--queue", action="store_true", help="Show only needs_review leads")
    p_rev.add_argument("--limit", type=int, default=50)
    p_rev.add_argument("--format", choices=("summary", "json"), default="summary")
    p_rev.set_defaults(func=cmd_review)

    p_exp = sub.add_parser("export", help="Export selected leads")
    _add_store_arg(p_exp)
    p_exp.add_argument("--status", default="all")
    p_exp.add_argument("--ids", help="Comma-separated lead ids")
    p_exp.add_argument("--run-id")
    p_exp.set_defaults(func=cmd_export)

    p_out = sub.add_parser("outreach", help="Generate/revise outreach for one lead")
    _add_store_arg(p_out)
    p_out.add_argument("id")
    p_out.add_argument("--dry-run", action="store_true")
    p_out.set_defaults(func=cmd_outreach)

    p_oc = sub.add_parser("outcome", help="Record lead outcome/status")
    _add_store_arg(p_oc)
    p_oc.add_argument("id")
    p_oc.add_argument(
        "--status",
        required=True,
        choices=[
            "new",
            "qualified",
            "shortlisted",
            "contacted",
            "replied",
            "meeting",
            "proposal",
            "won",
            "lost",
            "disqualified",
            "expired",
            "needs_review",
        ],
    )
    p_oc.add_argument("--notes", default="")
    p_oc.add_argument("--outcome", default="")
    p_oc.set_defaults(func=cmd_outcome)

    p_fu = sub.add_parser("followup", help="List due follow-ups")
    _add_store_arg(p_fu)
    p_fu.add_argument("--format", choices=("summary", "json"), default="summary")
    p_fu.set_defaults(func=cmd_followup)

    p_parse = sub.add_parser("parse", help="Parse prompt to criteria + mission (debug)")
    p_parse.add_argument("--prompt", required=True)
    p_parse.set_defaults(func=cmd_parse)

    p_plan = sub.add_parser("plan", help="Show research mission plan without fetching")
    p_plan.add_argument("--prompt", required=True)
    p_plan.set_defaults(func=cmd_plan)

    p_src = sub.add_parser("sources", help="List live adapters and stubs")
    p_src.add_argument("--format", choices=("summary", "json"), default="summary")
    p_src.set_defaults(func=cmd_sources)

    p_fail = sub.add_parser("failures", help="List sources that failed and can be resumed")
    _add_store_arg(p_fail)
    p_fail.add_argument("--format", choices=("summary", "json"), default="summary")
    p_fail.set_defaults(func=cmd_failures)

    p_ev = sub.add_parser("evidence", help="Show stored evidence for one lead")
    _add_store_arg(p_ev)
    p_ev.add_argument("id")
    p_ev.set_defaults(func=cmd_evidence)

    args = parser.parse_args()
    if not hasattr(args, "store"):
        args.store = str(DEFAULT_STORE)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
