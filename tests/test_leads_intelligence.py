"""Opportunity radar, agency partnership, and contact-path intelligence."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FIXTURE = REPO / "leads" / "fixtures" / "sample_leads.json"
sys.path.insert(0, str(REPO))

from leads.engine.agency_partnership import classify_agency_partnership  # noqa: E402
from leads.engine.contact_path import choose_contact_path  # noqa: E402
from leads.engine.criteria import parse_prompt  # noqa: E402
from leads.engine.model import ContactChannel, Evidence, Lead  # noqa: E402
from leads.engine.opportunity_radar import detect_opportunity  # noqa: E402
from leads.engine.outreach import generate_outreach  # noqa: E402
from leads.engine.pipeline import discover_leads  # noqa: E402


class OpportunityRadarTests(unittest.TestCase):
    def test_funding_alone_is_not_demand(self):
        event = detect_opportunity(
            title="Series A fintech",
            description="PayNest recently raised a Series A and is launching its product.",
            source_kind="funding_news",
        )
        self.assertEqual(event.event_type, "funding")
        self.assertFalse(event.demand_proven)

    def test_funding_plus_hiring_proves_demand(self):
        event = detect_opportunity(
            title="Seed-funded company hiring React",
            description=(
                "Ledgerly recently raised a seed round and is now hiring a React engineer. "
                "Apply now. Salary £60k."
            ),
            technologies=["react"],
        )
        self.assertEqual(event.event_type, "funding")
        self.assertTrue(event.demand_proven)
        self.assertIn("explicit_hiring_or_project_request", event.corroborating_signals)

    def test_tech_hiring_event(self):
        event = detect_opportunity(
            title="Frontend Engineer (React)",
            description="We are hiring a React engineer. Apply now.",
            technologies=["react"],
        )
        self.assertEqual(event.event_type, "tech_hiring")
        self.assertTrue(event.demand_proven)


class AgencyPartnershipTests(unittest.TestCase):
    def test_white_label_agency(self):
        p = classify_agency_partnership(
            title="Seeking white-label React partner",
            description=(
                "Design-led creative agency publicly seeking a white-label React "
                "and Next.js development partner for overflow client builds."
            ),
            company="Harbor & Pine Digital",
        )
        self.assertTrue(p.is_agency)
        self.assertEqual(p.partnership_fit, "white_label")
        self.assertIn("white-label", p.pitch_angle.lower())

    def test_directory_agency_without_ask(self):
        p = classify_agency_partnership(
            title="Generic digital agency website",
            description="PixelSmith Studio builds websites for local businesses.",
            company="PixelSmith Studio",
        )
        self.assertTrue(p.is_agency)
        self.assertEqual(p.partnership_fit, "none")

    def test_partnership_pitch_not_generic_freelance(self):
        lead = Lead(
            id="a1",
            name="Harbor",
            lead_type="client",
            company="Harbor & Pine Digital",
            title="Seeking white-label React partner",
            url="https://example-agency.test/partners/1",
            source="fixture",
            intent="EXPLICIT_DEMAND",
            intent_explanation="white-label ask",
            technical_requirements=["react", "next.js"],
            evidence=[
                Evidence(
                    summary="Agency seeking white-label React partner",
                    excerpt="white-label React and Next.js development partner",
                    source_url="https://example-agency.test/partners/1",
                )
            ],
        )
        from leads.engine.agency_partnership import attach_partnership
        from leads.engine.contact_path import attach_contact_path

        attach_partnership(lead)
        attach_contact_path(lead)
        draft = generate_outreach(lead)
        self.assertTrue(draft.partnership_pitch)
        self.assertIn("partner", draft.partnership_pitch.lower())
        self.assertNotIn("i found a bug", draft.email_body.lower())
        self.assertIn("white-label", draft.subject.lower() + draft.email_body.lower())


class ContactPathTests(unittest.TestCase):
    def test_prefers_application_form_when_no_named_contact(self):
        lead = Lead(
            id="b1",
            name="Co",
            lead_type="full_time",
            company="BrightLedger",
            title="Frontend Engineer",
            url="https://example-jobs.test/jobs/1",
            source="fixture",
            intent="EXPLICIT_DEMAND",
            intent_explanation="job",
            contacts=[
                ContactChannel(
                    channel_type="application_page",
                    value="https://example-jobs.test/jobs/1",
                    verification_status="published_on_official_source",
                )
            ],
        )
        path = choose_contact_path(lead)
        self.assertEqual(path.role, "application_form")
        self.assertTrue(path.value)

    def test_recruiter_email_for_vacancy(self):
        lead = Lead(
            id="b2",
            name="Co",
            lead_type="full_time",
            company="Ledgerly Hire",
            title="React engineer",
            url="https://example-jobs.test/jobs/2",
            source="fixture",
            intent="EXPLICIT_DEMAND",
            intent_explanation="job",
            contacts=[
                ContactChannel(
                    channel_type="email",
                    value="talent@ledgerly-hire.test",
                    verification_status="published_on_official_source",
                ),
                ContactChannel(
                    channel_type="application_page",
                    value="https://example-jobs.test/jobs/2",
                    verification_status="published_on_official_source",
                ),
            ],
        )
        path = choose_contact_path(lead)
        self.assertEqual(path.role, "recruiter")
        self.assertEqual(path.value, "talent@ledgerly-hire.test")
        self.assertIn("recruiter", path.relevance.lower())

    def test_founder_path_for_agency_partnership(self):
        lead = Lead(
            id="b3",
            name="Harbor",
            lead_type="client",
            company="Harbor & Pine Digital",
            title="White-label partner",
            url="https://example-agency.test/partners/1",
            source="fixture",
            intent="EXPLICIT_DEMAND",
            intent_explanation="partner",
            raw={
                "description": "Founder Maya Chen listed on the partner page. Seeking white-label React partner."
            },
            contacts=[
                ContactChannel(
                    channel_type="contact_form",
                    value="https://example-agency.test/partners/1#apply",
                    verification_status="published_on_official_source",
                )
            ],
        )
        from leads.engine.agency_partnership import attach_partnership

        attach_partnership(lead)
        path = choose_contact_path(lead)
        self.assertEqual(path.role, "founder")
        self.assertEqual(path.name, "Maya Chen")


class CriteriaModeTests(unittest.TestCase):
    def test_prompt_enables_radar_and_agency_modes(self):
        c = parse_prompt(
            "Find funded startups and digital agencies seeking white-label React partners"
        )
        self.assertIn("radar", c.discovery_modes)
        self.assertIn("agency", c.discovery_modes)


class PipelineIntelligenceTests(unittest.TestCase):
    def test_fixture_run_attaches_radar_agency_and_contact(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Path(tmp) / "store.json"
            payload = discover_leads(
                prompt="Find React Next.js freelance contracts agencies and funded hiring",
                sources=["fixture"],
                fixture_path=FIXTURE,
                store_path=store,
                export=False,
                incremental=False,
                skip_known=False,
            )
            by_company = {row["company"]: row for row in payload["results"]}

            ledgerly = by_company["Ledgerly"]
            self.assertFalse((ledgerly.get("opportunity") or {}).get("demand_proven"))
            self.assertEqual(ledgerly.get("status"), "needs_review")

            harbor = by_company["Harbor & Pine Digital"]
            self.assertEqual((harbor.get("partnership") or {}).get("partnership_fit"), "white_label")
            self.assertTrue((harbor.get("outreach") or {}).get("partnership_pitch"))
            self.assertEqual((harbor.get("preferred_contact") or {}).get("role"), "founder")

            hire = by_company["Ledgerly Hire"]
            self.assertTrue((hire.get("opportunity") or {}).get("demand_proven"))
            self.assertEqual(hire.get("status"), "qualified")
            self.assertEqual((hire.get("preferred_contact") or {}).get("role"), "recruiter")


class CommandDocsTests(unittest.TestCase):
    def test_leads_command_documents_intelligence(self):
        text = (REPO / ".claude" / "commands" / "leads.md").read_text(encoding="utf-8")
        self.assertIn("demand_proven", text)
        self.assertIn("white-label", text)
        self.assertIn("Email?", text)
        self.assertIn("leads/preferences.md", text)
        self.assertIn("--mode", text)
        self.assertIn("Easy mode", text)


if __name__ == "__main__":
    unittest.main()
