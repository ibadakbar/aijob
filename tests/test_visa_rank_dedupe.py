"""Ranking and dedupe unit tests (no network)."""

import unittest

from job_scraper.engine.dedupe import company_title_key, dedupe_jobs, normalize_url
from job_scraper.engine.model import NormalizedJob, SponsorshipResult
from job_scraper.engine.rank import rank_job, rank_jobs


def _job(**kwargs):
    base = dict(
        title="Senior React Engineer",
        company="Acme",
        url="https://example.com/jobs/1",
        source="greenhouse",
        location="Berlin, Germany",
        country="DE",
        description="React TypeScript Node",
        published_date="2026-10-20",
        sponsorship=SponsorshipResult("verified_in_listing", 0.9),
    )
    base.update(kwargs)
    return NormalizedJob(**base)


class DedupeTests(unittest.TestCase):
    def test_normalize_url_strips_tracking(self):
        a = normalize_url("https://WWW.Example.com/jobs/1/?utm_source=x#frag")
        b = normalize_url("https://example.com/jobs/1")
        self.assertEqual(a, b)

    def test_dedupe_same_company_title(self):
        a = _job(url="https://boards.greenhouse.io/acme/jobs/1", source="greenhouse", description="long " * 50)
        b = _job(url="https://www.arbeitnow.com/jobs/acme-react", source="arbeitnow", description="short")
        out = dedupe_jobs([a, b])
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].source, "greenhouse")

    def test_company_title_key_stable(self):
        self.assertEqual(
            company_title_key("Acme GmbH", "Senior React Engineer"),
            company_title_key("acme gmbh", "Senior React Engineer"),
        )


class RankTests(unittest.TestCase):
    def test_not_available_sponsorship_score_zero(self):
        job = _job(sponsorship=SponsorshipResult("not_available", 0.9))
        scores = rank_job(job)
        self.assertEqual(scores.sponsorship_score, 0.0)
        self.assertLessEqual(scores.overall, 0.45)

    def test_verified_outranks_unknown(self):
        good = _job(sponsorship=SponsorshipResult("verified_in_listing", 0.9))
        weak = _job(
            title="Senior React Engineer",
            company="Other",
            url="https://example.com/jobs/2",
            sponsorship=SponsorshipResult("unknown", 0.1),
        )
        ranked = rank_jobs([weak, good])
        self.assertEqual(ranked[0][0].company, "Acme")
        self.assertGreater(ranked[0][1].sponsorship_score, ranked[1][1].sponsorship_score)

    def test_separate_scores_present(self):
        scores = rank_job(_job())
        self.assertGreater(scores.skill_score, 0)
        self.assertGreater(scores.sponsorship_score, 0)
        self.assertTrue(scores.reasons)


if __name__ == "__main__":
    unittest.main()
