"""Quality tiers + world-mission planner."""

from __future__ import annotations

import unittest

from leads.engine.mission import _is_world_mission, plan_mission
from leads.engine.model import ContactChannel, Lead
from leads.engine.quality import quality_tier
from leads.engine.score import score_lead
from leads.engine.model import SearchCriteria


def _lead(**kwargs) -> Lead:
    base = dict(
        id="t1",
        name="Acme",
        lead_type="contract",
        company="Acme",
        title="React developer needed",
        url="https://example.test/job",
        source="remotive",
        intent="EXPLICIT_DEMAND",
        intent_explanation="listing",
    )
    base.update(kwargs)
    return Lead(**base)  # type: ignore[arg-type]


class QualityTierTests(unittest.TestCase):
    def test_published_email_is_tier_a(self):
        lead = _lead(
            contacts=[
                ContactChannel(
                    channel_type="email",
                    value="hello@acme.test",
                    source_url="https://acme.test/contact",
                    verification_status="published_on_official_source",
                )
            ]
        )
        self.assertEqual(quality_tier(lead), "A")

    def test_apply_only_is_tier_c(self):
        lead = _lead(
            contacts=[
                ContactChannel(
                    channel_type="application_page",
                    value="https://example.test/apply",
                    verification_status="published_on_official_source",
                )
            ]
        )
        self.assertEqual(quality_tier(lead), "C")

    def test_potential_fit_without_demand_is_tier_d(self):
        lead = _lead(intent="POTENTIAL_FIT", contacts=[])
        self.assertEqual(quality_tier(lead), "D")

    def test_score_boosts_email_over_apply_only(self):
        criteria = SearchCriteria(technologies=["react"], limit=10)
        warm = _lead(
            contacts=[
                ContactChannel(
                    channel_type="email",
                    value="hi@acme.test",
                    verification_status="published_on_official_source",
                )
            ]
        )
        cold = _lead(
            id="t2",
            contacts=[
                ContactChannel(
                    channel_type="application_page",
                    value="https://example.test/a",
                    verification_status="published_on_official_source",
                )
            ],
        )
        sw = score_lead(warm, criteria)
        sc = score_lead(cold, criteria)
        self.assertGreater(sw.overall, sc.overall)
        self.assertEqual(warm.raw.get("quality_tier"), "A")
        self.assertEqual(cold.raw.get("quality_tier"), "C")


class WorldMissionTests(unittest.TestCase):
    def test_find_leads_is_world(self):
        self.assertTrue(_is_world_mission("find leads"))
        self.assertTrue(_is_world_mission("todays leads"))
        self.assertTrue(_is_world_mission("worldwide warm leads"))

    def test_world_plan_includes_yc_and_ats(self):
        plan = plan_mission("find leads worldwide for React")
        self.assertIn("ycombinator", plan.sources)
        self.assertIn("remotive", plan.sources)
        self.assertIn("greenhouse", plan.sources)
        self.assertTrue(plan.require_published_email)
        self.assertGreaterEqual(plan.max_results, 40)


if __name__ == "__main__":
    unittest.main()
