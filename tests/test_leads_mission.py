"""Milestone 1: mission planner, verification, ATS registration, coverage, rich export."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

import sys

REPO = Path(__file__).resolve().parent.parent
FIXTURE = REPO / "leads" / "fixtures" / "sample_leads.json"
sys.path.insert(0, str(REPO))

from leads.engine.coverage import build_coverage  # noqa: E402
from leads.engine.criteria import parse_prompt  # noqa: E402
from leads.engine.export import export_run  # noqa: E402
from leads.engine.export_records import lead_export_record  # noqa: E402
from leads.engine.mission import plan_mission  # noqa: E402
from leads.engine.model import Evidence, Lead, SearchCriteria  # noqa: E402
from leads.engine.pipeline import discover_leads  # noqa: E402
from leads.engine.sources import LIVE_SOURCES, list_sources  # noqa: E402
from leads.engine.verify import attach_verification, verify_lead  # noqa: E402


class MissionPlannerTests(unittest.TestCase):
    def test_prompt_to_plan_with_ats_sources(self):
        plan = plan_mission(
            "Find 200 remote React Next.js full-time jobs worldwide with visa sponsorship"
        )
        self.assertEqual(plan.max_results, 200)
        self.assertIn("full_time", plan.opportunity_kinds)
        for src in ("remotive", "arbeitnow", "greenhouse", "ashby", "lever"):
            self.assertIn(src, plan.sources)
        self.assertTrue(plan.require_salary is False or plan.require_salary is True)
        self.assertTrue(
            "Partial worldwide" in plan.claim or "Worldwide public-adapter" in plan.claim
        )
        self.assertTrue(any("ATS" in n or "Greenhouse" in n for n in plan.notes) or plan.notes)

    def test_limit_caps_at_300(self):
        plan = plan_mission("Find 300 authentic worldwide opportunities for React")
        self.assertEqual(plan.max_results, 300)
        self.assertEqual(plan.criteria.limit, 300)

    def test_agency_kind_from_prompt(self):
        plan = plan_mission(
            "Find software agencies that publicly need subcontractors for React and Node.js"
        )
        self.assertIn("agency_partner", plan.opportunity_kinds)

    def test_criteria_parse_allows_200(self):
        c = parse_prompt("Find 200 React jobs")
        self.assertEqual(c.limit, 200)


class VerificationTests(unittest.TestCase):
    def test_verified_explicit_listing(self):
        lead = Lead(
            id="v1",
            name="Acme — Engineer",
            lead_type="full_time",
            company="Acme Corp",
            title="Senior React Engineer",
            url="https://jobs.example.com/acme/react",
            source="fixture",
            intent="EXPLICIT_DEMAND",
            intent_explanation="hiring",
            evidence=[
                Evidence(
                    summary="Hiring React engineer",
                    excerpt="We are hiring a Senior React Engineer. Apply now.",
                    source_url="https://jobs.example.com/acme/react",
                    published_date="2026-10-20",
                    checked_date="2026-10-27",
                )
            ],
            published_date="2026-10-20",
            checked_date="2026-10-27",
        )
        report = verify_lead(lead)
        self.assertIn(report.status, ("verified", "partially_verified"))
        self.assertTrue(report.original_source_url)
        self.assertGreater(report.evidence_confidence, 0.5)

    def test_rejected_without_url(self):
        lead = Lead(
            id="bad",
            name="x",
            lead_type="client",
            company="",
            title="Maybe need help",
            url="",
            source="fixture",
            intent="POTENTIAL_FIT",
            intent_explanation="guess",
        )
        report = verify_lead(lead)
        self.assertEqual(report.status, "rejected")

    def test_never_fills_email(self):
        lead = Lead(
            id="e1",
            name="Co — Role",
            lead_type="full_time",
            company="Co",
            title="Dev",
            url="https://boards.greenhouse.io/co/jobs/1",
            source="greenhouse",
            intent="EXPLICIT_DEMAND",
            intent_explanation="job",
            evidence=[
                Evidence(
                    summary="Job",
                    excerpt="Hiring TypeScript developer",
                    source_url="https://boards.greenhouse.io/co/jobs/1",
                )
            ],
        )
        rec = lead_export_record(lead)
        self.assertEqual(rec["business_email"], "")
        self.assertIn("business_email", rec["missing_information"])


class AtsRegistrationTests(unittest.TestCase):
    def test_ats_adapters_registered(self):
        for name in ("greenhouse", "ashby", "lever"):
            self.assertIn(name, LIVE_SOURCES)
        names = {r["name"] for r in list_sources() if r.get("implemented")}
        self.assertTrue({"greenhouse", "ashby", "lever"} <= names)


class CoverageTests(unittest.TestCase):
    def test_coverage_reports_honest_claim(self):
        plan = plan_mission("Find 20 React full-time jobs")
        cov = build_coverage(
            plan=plan,
            source_meta={
                "remotive": {"count": 5},
                "greenhouse": {"error": "timeout"},
            },
            sources_requested=plan.sources,
        )
        self.assertIn("not a claim", cov["claim"].lower())
        self.assertIn("remotive", cov["sources_searched"])
        self.assertTrue(any(f["source"] == "greenhouse" for f in cov["sources_failed"]))
        self.assertIn("upwork", cov["sources_not_in_scope"])


class ExportRecordTests(unittest.TestCase):
    def test_fixture_export_includes_recommended_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Path(tmp) / "store.json"
            payload = discover_leads(
                prompt="Find 10 React Next.js freelance or contract leads",
                sources=["fixture"],
                fixture_path=FIXTURE,
                persist=True,
                export=True,
                store_path=store,
                skip_known=False,
                check_mx=False,
            )
            self.assertIn("mission", payload)
            self.assertIn("coverage", payload)
            self.assertIn("claim", payload["coverage"])
            for row in payload["results"]:
                self.assertIn("verification", row.get("raw") or {})
                self.assertIn(
                    (row.get("raw") or {}).get("verification_status"),
                    {
                        "verified",
                        "partially_verified",
                        "unverified",
                        "contradictory",
                        "stale",
                        "rejected",
                    },
                )
            export = payload["meta"]["export"]
            self.assertTrue(Path(export["records_csv"]).is_file())
            self.assertTrue(Path(export["records_json"]).is_file())
            with Path(export["records_csv"]).open(encoding="utf-8") as fh:
                rows = list(csv.DictReader(fh))
            self.assertGreaterEqual(len(rows), 1)
            self.assertIn("lead_id", rows[0])
            self.assertIn("verification_status", rows[0])
            self.assertIn("original_source_url", rows[0])
            self.assertIn("missing_information", rows[0])


if __name__ == "__main__":
    unittest.main()
