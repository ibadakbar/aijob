"""Tests for ATS-id dedupe and Path A/B filtering."""

from __future__ import annotations

from job_scraper.engine.dedupe import ats_job_key, dedupe_jobs
from job_scraper.engine.model import NormalizedJob, SponsorshipResult
from job_scraper.engine.path_filter import filter_path_ab, path_ab_verdict


def _job(**kwargs) -> NormalizedJob:
    base = dict(
        title="Senior Frontend Engineer",
        company="Acme",
        url="https://example.com/jobs/1",
        source="greenhouse",
        location="Remote",
        workplace="remote",
        description="Build React apps.",
        sponsorship=SponsorshipResult(classification="unknown", confidence=0.1),
        source_job_id="111",
    )
    base.update(kwargs)
    return NormalizedJob(**base)


def test_ats_job_key_dedupes_same_id_different_urls():
    a = _job(url="https://boards.greenhouse.io/acme/jobs/111", source_job_id="111")
    b = _job(
        url="https://boards.greenhouse.io/acme/jobs/111?gh_jid=111",
        source_job_id="111",
        description="Build React apps. Longer description wins.",
    )
    out = dedupe_jobs([a, b])
    assert len(out) == 1
    assert "Longer" in (out[0].description or "")
    assert ats_job_key(out[0]) == "greenhouse::111"


def test_path_a_remote_worldwide():
    job = _job(description="Fully remote, hire from anywhere worldwide. React + TypeScript.")
    path, _ = path_ab_verdict(job)
    assert path == "A"


def test_path_a_rejects_country_only_remote():
    job = _job(
        location="Remote - US",
        description="Remote US only. Must be based in the United States. React.",
    )
    path, reason = path_ab_verdict(job)
    assert path is None
    assert "country-only" in reason or "fake-remote" in reason


def test_fake_remote_drops_within_the_us_even_with_possible_sponsorship():
    job = _job(
        location="Worldwide Remote",
        description="You'll enjoy the flexibility to work remotely from anywhere within the U.S.",
        sponsorship=SponsorshipResult(classification="possible", confidence=0.5),
    )
    path, reason = path_ab_verdict(job)
    assert path is None
    assert "fake-remote" in reason


def test_fake_remote_drops_wwr_us_headquarters_label():
    job = _job(
        location="Worldwide Remote",
        description="Headquarters: Remote - United States. Frontend Engineer. React TypeScript.",
    )
    path, reason = path_ab_verdict(job)
    assert path is None
    assert "fake-remote" in reason


def test_path_a_hire_globally_and_eor():
    job = _job(
        description="Fully remote. We hire globally via EOR. React + Next.js + TypeScript.",
    )
    path, _ = path_ab_verdict(job)
    assert path == "A"


def test_path_b_onsite_with_sponsorship():
    job = _job(
        workplace="onsite",
        location="Berlin, Germany",
        country="DE",
        description="We offer visa sponsorship and relocation support for this role.",
        sponsorship=SponsorshipResult(
            classification="verified_in_listing",
            confidence=0.9,
            relocation_support=True,
        ),
    )
    path, _ = path_ab_verdict(job)
    assert path == "B"


def test_path_pk_onsite_without_sponsorship():
    job = _job(
        workplace="onsite",
        location="Karachi, Pakistan",
        country="PK",
        description="React developer for a local SaaS team. Office in Karachi.",
        sponsorship=SponsorshipResult(classification="unknown", confidence=0.1),
    )
    path, reason = path_ab_verdict(job)
    assert path == "PK"
    assert "pakistan" in reason.lower()


def test_path_pk_hybrid_from_sweep_tag():
    job = _job(
        workplace="hybrid",
        location="Lahore",
        country=None,
        description="Full stack MERN role. Hybrid office days.",
        raw={"sweep": "pakistan_any_mode"},
        sponsorship=SponsorshipResult(classification="not_available", confidence=0.5),
    )
    path, _ = path_ab_verdict(job)
    assert path == "PK"


def test_filter_path_ab_keeps_and_reports_near_miss():
    good = _job(
        url="https://example.com/a",
        source_job_id="a",
        description="Remote worldwide. React.",
    )
    bad = _job(
        url="https://example.com/b",
        source_job_id="b",
        workplace="onsite",
        location="Austin, TX",
        country="US",
        description="Must already have US work authorization. No sponsorship.",
        sponsorship=SponsorshipResult(classification="not_available", confidence=0.9),
    )
    kept, near = filter_path_ab([good, bad])
    assert len(kept) == 1
    assert kept[0].raw.get("path") == "A"
    assert len(near) == 1
