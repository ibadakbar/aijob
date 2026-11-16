"""Unit tests for sponsorship classification (no network)."""

import unittest

from job_scraper.engine.sponsorship import classify_sponsorship


class SponsorshipClassifyTests(unittest.TestCase):
    def test_verified_positive(self):
        text = "We offer visa sponsorship and a relocation package for this role."
        r = classify_sponsorship(text, source_url="https://example.com/job/1")
        self.assertEqual(r.classification, "verified_in_listing")
        self.assertGreaterEqual(r.confidence, 0.8)
        self.assertTrue(r.evidence)
        self.assertIn("visa", r.evidence[0].excerpt.lower())
        self.assertTrue(r.relocation_support)

    def test_not_available(self):
        text = "Applicants must have existing work authorization. No visa sponsorship."
        r = classify_sponsorship(text, source_url="https://example.com/job/2")
        self.assertEqual(r.classification, "not_available")
        self.assertGreaterEqual(r.confidence, 0.85)

    def test_contradiction_prefers_negative(self):
        text = (
            "Visa sponsorship is available for some teams. "
            "This role: must have existing work authorization; no sponsorship."
        )
        r = classify_sponsorship(text, source_url="https://example.com/job/3")
        self.assertEqual(r.classification, "not_available")

    def test_arbeitnow_hint_is_possible_not_verified(self):
        text = "Build great products with React."
        r = classify_sponsorship(
            text,
            source_url="https://www.arbeitnow.com/jobs/x",
            source_hint="arbeitnow_visa_filter",
        )
        self.assertEqual(r.classification, "possible")
        self.assertLess(r.confidence, 0.8)

    def test_registry_alone_is_sponsor_company_only(self):
        text = "Join our London engineering team."
        r = classify_sponsorship(
            text,
            source_url="https://example.com/job/4",
            company_on_sponsor_registry=True,
            registry_name="UK licensed sponsors",
        )
        self.assertEqual(r.classification, "sponsor_company_only")
        self.assertTrue(any("registry" in e.pattern for e in r.evidence))

    def test_unknown_when_empty(self):
        r = classify_sponsorship("", source_url="https://example.com/job/5")
        self.assertEqual(r.classification, "unknown")


if __name__ == "__main__":
    unittest.main()
