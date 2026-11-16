"""Incremental discovery, review queue, cache, and failure recovery."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FIXTURE = REPO / "leads" / "fixtures" / "sample_leads.json"
sys.path.insert(0, str(REPO))

from leads.engine.confidence import decide_status  # noqa: E402
from leads.engine.evidence_log import read_evidence  # noqa: E402
from leads.engine.incremental import runtime_paths, select_records  # noqa: E402
from leads.engine.model import Evidence, Lead, SearchCriteria  # noqa: E402
from leads.engine.persist import list_leads  # noqa: E402
from leads.engine.pipeline import discover_leads  # noqa: E402
from leads.engine.recovery import list_failures  # noqa: E402
from leads.engine.research_cache import ResearchCache, model_tier_for  # noqa: E402
from leads.engine.sources import (  # noqa: E402
    FetchResult,
    LeadSourceAdapter,
    SourceMeta,
    register_source,
    unregister_source,
)
from leads.engine.sources.base import LeadSourceAdapter as _Adapter  # noqa: E402


def _lead(
    *,
    company: str,
    title: str,
    url: str,
    intent: str = "EXPLICIT_DEMAND",
    excerpt: str = "Hiring a React engineer. Apply now.",
) -> Lead:
    return Lead(
        id=f"id-{company}-{title}".lower().replace(" ", "-"),
        name=f"{company} — {title}",
        lead_type="full_time",
        company=company,
        title=title,
        url=url,
        source="fake",
        intent=intent,  # type: ignore[arg-type]
        intent_explanation="test",
        evidence=[
            Evidence(
                summary=excerpt,
                excerpt=excerpt,
                source_url=url,
                published_date="2026-10-20",
                checked_date="2026-10-27",
            )
        ],
        technical_requirements=["react", "typescript"],
        published_date="2026-10-20",
    )


class _Flaky(LeadSourceAdapter):
    meta = SourceMeta(name="flaky", official_api=False, notes="test flaky")
    calls = 0

    def fetch(self, criteria: SearchCriteria, **kwargs: object) -> FetchResult:
        type(self).calls += 1
        if type(self).calls < 3:
            raise TimeoutError("timed out")
        return FetchResult(leads=[_lead(company="Flaky Co", title="React role", url="https://flaky.example/jobs/1")])


class _Down(LeadSourceAdapter):
    meta = SourceMeta(name="down", official_api=False, notes="test down")
    calls = 0

    def fetch(self, criteria: SearchCriteria, **kwargs: object) -> FetchResult:
        type(self).calls += 1
        raise ConnectionError("connection reset by peer")


class _Boom(LeadSourceAdapter):
    meta = SourceMeta(name="boom", official_api=False, notes="test boom")
    calls = 0

    def fetch(self, criteria: SearchCriteria, **kwargs: object) -> FetchResult:
        type(self).calls += 1
        raise ValueError("bad request")


class _Ok(LeadSourceAdapter):
    meta = SourceMeta(name="oksrc", official_api=False, notes="test ok")
    calls = 0

    def fetch(self, criteria: SearchCriteria, **kwargs: object) -> FetchResult:
        type(self).calls += 1
        return FetchResult(
            leads=[_lead(company="Ok Co", title="React engineer", url="https://ok.example/jobs/1")]
        )


class _Maybe(LeadSourceAdapter):
    meta = SourceMeta(name="maybesrc", official_api=False, notes="test maybe")
    calls = 0
    fail = True

    def fetch(self, criteria: SearchCriteria, **kwargs: object) -> FetchResult:
        type(self).calls += 1
        if type(self).fail:
            raise TimeoutError("timed out")
        return FetchResult(
            leads=[_lead(company="Maybe Co", title="React contract", url="https://maybe.example/jobs/1")]
        )


class _Pair(LeadSourceAdapter):
    meta = SourceMeta(name="pairsrc", official_api=False, notes="test pair")

    def fetch(self, criteria: SearchCriteria, **kwargs: object) -> FetchResult:
        return FetchResult(
            leads=[
                _lead(
                    company="Northwind Analytics",
                    title="Need React developer",
                    url="https://northwind.example/jobs/1",
                    excerpt="We are hiring a React developer now.",
                ),
                _lead(
                    company="Northwind Analytics",
                    title="Might expand the team",
                    url="https://northwind.example/news/2",
                    intent="STRONG_SIGNAL",
                    excerpt="Series A, no open role listed.",
                ),
            ]
        )


class EfficiencyTests(unittest.TestCase):
    def setUp(self) -> None:
        self._registered: list[str] = []

    def tearDown(self) -> None:
        for name in self._registered:
            unregister_source(name)

    def _use(self, name: str, cls: type[_Adapter]) -> None:
        register_source(name, cls)
        self._registered.append(name)

    def test_second_search_skips_the_fetch(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Path(tmp) / "store.json"
            prompt = "Find 10 React Next.js freelance or contract leads"
            first = discover_leads(
                prompt=prompt,
                sources=["fixture"],
                fixture_path=FIXTURE,
                store_path=store,
                export=False,
            )
            self.assertGreaterEqual(first["meta"]["returned"], 3)
            second = discover_leads(
                prompt=prompt,
                sources=["fixture"],
                fixture_path=FIXTURE,
                store_path=store,
                export=False,
            )
            self.assertEqual(second["meta"]["returned"], 0)
            self.assertIn("fixture", second["meta"]["incremental"]["fetch_skipped"])

    def test_changed_listing_is_returned_after_the_cache_expires(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = root / "store.json"
            fixture = root / "fixture.json"
            shutil.copyfile(FIXTURE, fixture)
            prompt = "Find 10 React Next.js freelance or contract leads"
            discover_leads(
                prompt=prompt,
                sources=["fixture"],
                fixture_path=fixture,
                store_path=store,
                export=False,
            )
            state_path = runtime_paths(store)["state"]
            state = json.loads(state_path.read_text(encoding="utf-8"))
            for entry in state["sources"].values():
                entry["fetched_at"] = "2020-01-01T00:00:00+00:00"
            state_path.write_text(json.dumps(state), encoding="utf-8")

            data = json.loads(fixture.read_text(encoding="utf-8"))
            data["leads"][0]["description"] = (
                "Updated brief: we are hiring a React and Next.js freelancer this week "
                "for a new SaaS dashboard. Apply at the project page."
            )
            fixture.write_text(json.dumps(data), encoding="utf-8")

            again = discover_leads(
                prompt=prompt,
                sources=["fixture"],
                fixture_path=fixture,
                store_path=store,
                export=False,
            )
            companies = [row["company"] for row in again["results"]]
            self.assertIn("Northwind Analytics", companies)
            self.assertNotIn("PixelSmith Studio", companies)
            self.assertGreaterEqual(again["meta"]["incremental"]["changed"], 1)

    def test_full_search_reuses_cached_extraction(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Path(tmp) / "store.json"
            prompt = "Find 10 React Next.js freelance or contract leads"
            discover_leads(
                prompt=prompt,
                sources=["fixture"],
                fixture_path=FIXTURE,
                store_path=store,
                export=False,
                incremental=False,
            )
            second = discover_leads(
                prompt=prompt,
                sources=["fixture"],
                fixture_path=FIXTURE,
                store_path=store,
                export=False,
                incremental=False,
            )
            self.assertGreaterEqual(second["meta"]["returned"], 1)
            self.assertGreaterEqual(second["meta"]["cache"]["vacancy_hits"], 1)
            cached = json.loads(runtime_paths(store)["cache"].read_text(encoding="utf-8"))
            self.assertTrue(any(str(key).startswith("extract:score:") for key in cached["ai"]))

    def test_uncertain_leads_go_to_the_review_queue(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Path(tmp) / "store.json"
            payload = discover_leads(
                prompt="Find 10 React Next.js freelance or contract leads",
                sources=["fixture"],
                fixture_path=FIXTURE,
                store_path=store,
                export=False,
            )
            by_company = {row["company"]: row for row in payload["results"]}
            self.assertEqual(by_company["Northwind Analytics"]["status"], "qualified")
            self.assertEqual(by_company["PixelSmith Studio"]["status"], "needs_review")
            self.assertTrue(by_company["PixelSmith Studio"]["raw"]["research_deferred"])
            self.assertGreaterEqual(payload["meta"]["qualified"], 1)
            self.assertGreaterEqual(payload["meta"]["review_queue"], 1)

            queued = list_leads(review_queue=True, path=store)
            self.assertTrue(queued)
            self.assertTrue(all(row["status"] == "needs_review" for row in queued))
            short = list_leads(shortlist_only=True, path=store)
            self.assertTrue(all(row["status"] != "needs_review" for row in short))

            rows = read_evidence(runtime_paths(store)["evidence"])
            self.assertTrue(rows)
            self.assertTrue(all(row.get("source_url") and row.get("recorded_at") for row in rows))
            self.assertTrue(any(row.get("excerpt") for row in rows))

    def test_same_company_is_not_researched_twice(self):
        self._use("pairsrc", _Pair)
        with tempfile.TemporaryDirectory() as tmp:
            store = Path(tmp) / "store.json"
            payload = discover_leads(
                prompt="Find React engineers",
                sources=["pairsrc"],
                store_path=store,
                export=False,
            )
            self.assertGreaterEqual(payload["meta"]["cache"]["company_hits"], 1)
            second = next(row for row in payload["results"] if row["title"] == "Might expand the team")
            self.assertEqual(second["raw"]["model_tier"], "extract")
            self.assertFalse(second["raw"]["research_deferred"])
            self.assertIn("reused from cache", second["review_reason"])

    def test_transient_errors_retry_and_record(self):
        _Flaky.calls = 0
        _Down.calls = 0
        self._use("flaky", _Flaky)
        self._use("down", _Down)
        with tempfile.TemporaryDirectory() as tmp:
            store = Path(tmp) / "store.json"
            ok = discover_leads(
                prompt="Find React engineers",
                sources=["flaky"],
                store_path=store,
                export=False,
            )
            self.assertEqual(_Flaky.calls, 3)
            self.assertEqual(ok["meta"]["returned"], 1)
            self.assertEqual(ok["meta"]["sources"]["flaky"]["attempts"], 3)

            failed = discover_leads(
                prompt="Find React engineers",
                sources=["down"],
                store_path=store,
                export=False,
            )
            self.assertEqual(_Down.calls, 3)
            self.assertEqual(failed["meta"]["returned"], 0)
            self.assertIn("down", failed["meta"]["failed_sources"])
            self.assertTrue(failed["meta"]["failed_sources"]["down"]["transient"])
            listed = list_failures(runtime_paths(store)["runs"])
            self.assertTrue(any(row["source"] == "down" for row in listed))

    def test_permanent_errors_are_not_retried(self):
        _Boom.calls = 0
        self._use("boom", _Boom)
        with tempfile.TemporaryDirectory() as tmp:
            store = Path(tmp) / "store.json"
            payload = discover_leads(
                prompt="Find React engineers",
                sources=["boom"],
                store_path=store,
                export=False,
            )
            self.assertEqual(_Boom.calls, 1)
            self.assertEqual(payload["meta"]["failed_sources"]["boom"]["attempts"], 1)
            self.assertFalse(payload["meta"]["failed_sources"]["boom"]["transient"])

    def test_resume_retries_only_failed_sources(self):
        _Ok.calls = 0
        _Maybe.calls = 0
        _Maybe.fail = True
        self._use("oksrc", _Ok)
        self._use("maybesrc", _Maybe)
        with tempfile.TemporaryDirectory() as tmp:
            store = Path(tmp) / "store.json"
            first = discover_leads(
                prompt="Find React engineers",
                sources=["oksrc", "maybesrc"],
                store_path=store,
                export=False,
            )
            self.assertEqual(_Ok.calls, 1)
            self.assertEqual(_Maybe.calls, 3)
            self.assertEqual(first["meta"]["run_status"], "partial")
            self.assertIn("maybesrc", first["meta"]["failed_sources"])

            _Maybe.fail = False
            second = discover_leads(
                prompt="Find React engineers",
                sources=None,
                store_path=store,
                export=False,
                resume_run=first["meta"]["run_id"],
            )
            self.assertEqual(_Ok.calls, 1)
            self.assertGreaterEqual(_Maybe.calls, 4)
            companies = [row["company"] for row in second["results"]]
            self.assertIn("Maybe Co", companies)
            self.assertNotIn("Ok Co", companies)
            self.assertEqual(second["meta"]["run_status"], "complete")

    def test_cached_compute_runs_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = ResearchCache(Path(tmp) / "cache.json")
            calls = {"n": 0}

            def compute() -> dict[str, int]:
                calls["n"] += 1
                return {"ok": 1}

            first, hit = cache.cached_compute(
                task="score", tier="extract", content_hash="abc", compute=compute
            )
            second, hit_again = cache.cached_compute(
                task="score", tier="extract", content_hash="abc", compute=compute
            )
            self.assertEqual(first, {"ok": 1})
            self.assertFalse(hit)
            self.assertTrue(hit_again)
            self.assertEqual(second, first)
            self.assertEqual(calls["n"], 1)

    def test_model_tier_reserves_research_for_ambiguous_leads(self):
        clear = _lead(company="Acme", title="React", url="https://acme.example/jobs/1")
        vague = _lead(
            company="Acme",
            title="News",
            url="https://acme.example/news",
            intent="POTENTIAL_FIT",
        )
        self.assertEqual(model_tier_for(clear, company_cached=False), "extract")
        self.assertEqual(model_tier_for(vague, company_cached=False), "research")
        self.assertEqual(model_tier_for(vague, company_cached=True), "extract")
        status, _reason = decide_status(vague, 0.9)
        self.assertEqual(status, "needs_review")

    def test_select_records_splits_new_and_changed(self):
        original = _lead(company="Acme", title="React", url="https://acme.example/jobs/1")
        fresh, changed, unchanged = select_records(
            [original], previous_records={}, store_index={}
        )
        self.assertEqual(len(fresh), 1)
        edited = _lead(
            company="Acme",
            title="React",
            url="https://acme.example/jobs/1",
            excerpt="Updated: still hiring a React engineer this week.",
        )
        fresh, changed, unchanged = select_records(
            [edited],
            previous_records={"https://acme.example/jobs/1": {"hash": original.content_hash}},
            store_index={},
        )
        self.assertEqual(len(changed), 1)
        self.assertEqual(unchanged, [])

    def test_command_documents_the_queue_and_resume(self):
        text = (REPO / ".claude" / "commands" / "leads.md").read_text(encoding="utf-8")
        self.assertIn("needs_review", text)
        self.assertIn("--resume", text)
        self.assertIn("--full", text)
        self.assertIn("review --queue", text)


if __name__ == "__main__":
    unittest.main()
