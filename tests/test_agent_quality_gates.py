"""Tests for freshness, Path A/B gate, contact ladder, Grade A hireability."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent.models.opportunity import OpportunityRecord, make_opportunity_id
from agent.quality.contact_ladder import classify_email, ladder_from_contacts
from agent.quality.freshness import fingerprint, is_repeat, index_from_excel_rows
from agent.quality.path_gate import path_gate
from agent.quality.pipeline import apply_quality_gates
from agent.scoring.scores import score_job
from agent.storage.excel_store import ExcelStore


def test_fingerprint_stable():
    a = fingerprint("Acme Inc", "Senior React", "https://jobs.ashbyhq.com/acme/1?x=1")
    b = fingerprint("Acme Inc", "Senior React", "https://jobs.ashbyhq.com/acme/1")
    assert a == b


def test_path_gate_drops_fake_remote():
    rec = OpportunityRecord(
        id="t1",
        opportunity_type="job",
        company="LockCo",
        role_or_title="Remote React Engineer",
        description="Fully remote within the U.S. only. Must be authorized to work in the US.",
        remote_type="remote",
        source_url="https://example.com/j",
    )
    keep, reason, path = path_gate(rec)
    assert keep is False
    assert "fake-remote" in reason or "country-only" in reason
    assert path is None


def test_path_gate_keeps_path_a_worldwide():
    rec = OpportunityRecord(
        id="t2",
        opportunity_type="job",
        company="GlobalCo",
        role_or_title="Senior Next.js Engineer",
        description="Remote worldwide. We hire from anywhere. EOR available.",
        remote_type="remote",
        source_url="https://example.com/g",
        sponsorship_class="possible",
    )
    keep, reason, path = path_gate(rec)
    assert keep is True
    assert path == "A"


def test_path_gate_drops_onsite_without_visa():
    rec = OpportunityRecord(
        id="t3",
        opportunity_type="job",
        company="BerlinCo",
        role_or_title="Frontend Engineer",
        description="Onsite in Berlin office. German fluency required.",
        remote_type="onsite",
        country="DE",
        source_url="https://example.com/b",
    )
    keep, reason, _ = path_gate(rec)
    assert keep is False
    assert "sponsorship" in reason


def test_contact_ladder_rejects_inferred():
    st, prov = classify_email(
        "john@acme.com",
        verification_status="inferred",
        notes="guessed pattern",
        check_mx=False,
    )
    assert st == "INFERRED"

    v = ladder_from_contacts(
        [
            {
                "channel_type": "email",
                "value": "careers@acme.com",
                "verification_status": "published_on_official_source",
            }
        ],
        source_url="https://acme.com/jobs/1",
        check_mx=False,
    )
    assert v.tier == "A"
    assert v.email == "careers@acme.com"


def test_grade_a_requires_demand_and_contact():
    rec = OpportunityRecord(
        id="t4",
        opportunity_type="job",
        company="ScoreCo",
        role_or_title="Senior React TypeScript Next.js Full Stack SaaS Engineer Lead",
        description="Hiring senior React Next.js TypeScript full stack SaaS AWS",
        source_url="https://example.com/s",
        remote_type="remote",
        path="A",
        international_eligibility="worldwide",
        visa_sponsorship="yes",
        sponsorship_class="verified_in_listing",
        posted_date="2026-11-24",
        # no email / linkedin
    )
    score_job(rec)
    assert rec.grade != "A"  # demoted — no reachable contact


def test_grade_a_with_email_and_demand():
    rec = OpportunityRecord(
        id="t5",
        opportunity_type="job",
        company="WarmCo",
        role_or_title="Senior React TypeScript Next.js Full Stack Engineer",
        description="We're hiring a senior React Next.js TypeScript full stack SaaS engineer. Remote worldwide.",
        source_url="https://example.com/w",
        remote_type="remote",
        path="A",
        international_eligibility="worldwide",
        visa_sponsorship="yes",
        sponsorship_class="verified_in_listing",
        contact_email="careers@warmco.com",
        email_status="PUBLIC_UNVERIFIED",
        posted_date="2026-11-24",
        required_skills="React, Next.js, TypeScript, Node.js, SaaS",
    )
    score_job(rec)
    assert rec.grade == "A"
    assert rec.opportunity_score >= 85


def test_pipeline_zero_repeat(tmp_path: Path):
    store = ExcelStore(
        path=tmp_path / "opportunities.xlsx",
        backup_dir=tmp_path / "backups",
        lock_path=tmp_path / "opportunities.lock",
    )
    store.ensure_workbook()
    existing = OpportunityRecord(
        id=make_opportunity_id("job", "DupCo", "React Dev", "https://example.com/dup"),
        opportunity_type="job",
        company="DupCo",
        role_or_title="React Dev",
        source_url="https://example.com/dup",
        description="Remote worldwide hire from anywhere",
        remote_type="remote",
        path="A",
        status="applied",
    )
    store.upsert_opportunities([existing], backup=False)

    newbie = OpportunityRecord(
        id=make_opportunity_id("job", "DupCo", "Other Title", "https://example.com/other"),
        opportunity_type="job",
        company="DupCo",
        role_or_title="Other Title — Remote worldwide from anywhere",
        description="Remote worldwide. We hire from anywhere.",
        remote_type="remote",
        source_url="https://example.com/other",
        sponsorship_class="possible",
    )
    rows = store.load_all_opportunities()
    gated = apply_quality_gates([newbie], existing_rows=rows, enforce_path=True)
    # Company blocked because status=applied
    assert gated.stats["drop_repeat"] >= 1 or any(
        d.get("reason") == "blocked_company_applied_or_list" for d in gated.dropped
    )


def test_is_repeat_index():
    rec = OpportunityRecord(
        id="x",
        opportunity_type="job",
        company="SeenCo",
        role_or_title="Eng",
        source_url="https://example.com/seen",
    )
    idx = index_from_excel_rows([rec])
    drop, why = is_repeat(rec, idx, kill_days=14)
    assert drop is True
    assert why


def test_block_india_listings():
    from agent.quality.geo_gate import is_india_listing

    india = OpportunityRecord(
        id="in1",
        opportunity_type="job",
        company="PingAura AI",
        role_or_title="Frontend Engineer",
        location="Remote / Mumbai preference (India)",
        source_url="https://example.com/in",
    )
    assert is_india_listing(india) is True
    bangalore = OpportunityRecord(
        id="in2",
        opportunity_type="job",
        company="GitLab",
        role_or_title="Backend",
        location="Bangalore, India",
        country="IN",
        source_url="https://example.com/blr",
    )
    assert is_india_listing(bangalore) is True
    # Indonesia must not false-positive
    indo = OpportunityRecord(
        id="id1",
        opportunity_type="job",
        company="RemoteCo",
        role_or_title="React Eng",
        location="Remote, Indonesia welcome",
        source_url="https://example.com/id",
        description="Hiring worldwide including Indonesia",
    )
    assert is_india_listing(indo) is False
    nz = OpportunityRecord(
        id="nz1",
        opportunity_type="job",
        company="KiwiSoft",
        role_or_title="Full Stack",
        location="Auckland, New Zealand",
        country="NZ",
        source_url="https://example.com/nz",
        remote_type="remote",
        visa_sponsorship="yes",
        sponsorship_class="verified_in_listing",
    )
    assert is_india_listing(nz) is False

    gated = apply_quality_gates([india, bangalore, nz], existing_rows=[], enforce_path=False)
    assert gated.stats.get("drop_geo", 0) == 2
    assert all(d.get("reason") == "blocked_geo_india" for d in gated.dropped)
    assert not any(r.company in ("PingAura AI", "GitLab") for r in gated.kept)


def test_drop_listings_older_than_3_months():
    from datetime import date, timedelta

    from agent.quality.freshness import (
        is_too_old,
        linkedin_activity_posted_date,
        relative_age_to_date,
    )

    old = OpportunityRecord(
        id="old",
        opportunity_type="client",
        company="PrithviTek",
        role_or_title="Senior Full-Stack Engineer",
        source_url="https://example.com/old",
        posted_date=(date.today() - timedelta(days=120)).isoformat(),
    )
    drop, why = is_too_old(old)
    assert drop is True
    assert "stale_older_than_90d" in why

    fresh = OpportunityRecord(
        id="fresh",
        opportunity_type="job",
        company="NewCo",
        role_or_title="React Eng",
        source_url="https://example.com/new",
        posted_date=(date.today() - timedelta(days=20)).isoformat(),
    )
    assert is_too_old(fresh)[0] is False

    # LinkedIn activity snowflake ≈ 2026-07-07 → older than 90d as of 2026-11-25
    li_url = (
        "https://www.linkedin.com/posts/nirvi-k-a6838518_hello-all-"
        "interested-candidates-please-activity-7480125856808558593-nPwH"
    )
    li_day = linkedin_activity_posted_date(li_url)
    assert li_day is not None
    assert (date.today() - li_day).days > 90
    li_rec = OpportunityRecord(
        id="li",
        opportunity_type="client",
        company="PrithviTek",
        role_or_title="Senior Full-Stack",
        source_url=li_url,
    )
    assert is_too_old(li_rec)[0] is True

    assert relative_age_to_date("posted 4mo ago") is not None
    assert (date.today() - relative_age_to_date("4mo")).days >= 90

    gated = apply_quality_gates([li_rec, fresh], existing_rows=[], enforce_path=False)
    assert any(d.get("reason", "").startswith("stale_") for d in gated.dropped)
    assert gated.stats.get("drop_stale", 0) >= 1
