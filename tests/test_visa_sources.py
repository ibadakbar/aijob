"""Source adapter tests with mocked HTTP (no live network)."""

import json
import unittest
from pathlib import Path
from unittest.mock import patch

from job_scraper.engine.sources.arbeitnow import ArbeitnowSource
from job_scraper.engine.sources.greenhouse import GreenhouseSource
from job_scraper.engine.sources.stubs import RELOCATE_ME_STUB

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "visa"


class ArbeitnowSourceTests(unittest.TestCase):
    def test_parses_fixture_and_classifies(self):
        payload = json.loads((FIXTURES / "arbeitnow_page.json").read_text(encoding="utf-8"))

        def fake_fetch(url, **kwargs):
            return payload

        with patch("job_scraper.engine.sources.arbeitnow.fetch_json", side_effect=fake_fetch):
            result = ArbeitnowSource().fetch(pages=1, max_jobs=10)
        self.assertEqual(len(result.jobs), 2)
        by_company = {j.company: j for j in result.jobs}
        self.assertEqual(by_company["Acme GmbH"].sponsorship.classification, "verified_in_listing")
        self.assertEqual(by_company["Local Co"].sponsorship.classification, "not_available")
        self.assertEqual(by_company["Acme GmbH"].country, "DE")


class GreenhouseSourceTests(unittest.TestCase):
    def test_filters_non_engineering_and_loads_content(self):
        listing = json.loads((FIXTURES / "greenhouse_jobs.json").read_text(encoding="utf-8"))
        detail = json.loads((FIXTURES / "greenhouse_job_1001.json").read_text(encoding="utf-8"))

        def fake_fetch(url, **kwargs):
            if "/jobs/1001" in url:
                return detail
            return listing

        with patch("job_scraper.engine.sources.greenhouse.fetch_json", side_effect=fake_fetch):
            result = GreenhouseSource().fetch(
                boards=[{"token": "example", "company": "Example"}],
                max_jobs=10,
            )
        self.assertEqual(len(result.jobs), 1)
        job = result.jobs[0]
        self.assertIn("React", job.title)
        self.assertEqual(job.sponsorship.classification, "verified_in_listing")
        self.assertEqual(job.country, "GB")


class StubTests(unittest.TestCase):
    def test_stub_returns_empty_with_reason(self):
        result = RELOCATE_ME_STUB.fetch()
        self.assertEqual(result.jobs, [])
        self.assertTrue(result.meta.get("stub"))
        self.assertFalse(result.meta.get("implemented"))


class HttpFailureTests(unittest.TestCase):
    def test_arbeitnow_records_error_on_failure(self):
        with patch(
            "job_scraper.engine.sources.arbeitnow.fetch_json",
            side_effect=RuntimeError("429 rate limited"),
        ):
            result = ArbeitnowSource().fetch(pages=1)
        self.assertEqual(result.jobs, [])
        self.assertTrue(any("429" in e or "rate" in e.lower() for e in result.errors))


if __name__ == "__main__":
    unittest.main()
