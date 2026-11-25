"""Tests for Excel-only agent storage (no network, no DB)."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent.models.opportunity import OpportunityRecord, make_opportunity_id, norm_key
from agent.scoring.scores import score_client, score_job
from agent.storage.excel_store import ExcelStore


@pytest.fixture()
def store(tmp_path: Path) -> ExcelStore:
    return ExcelStore(
        path=tmp_path / "opportunities.xlsx",
        backup_dir=tmp_path / "backups",
        lock_path=tmp_path / "opportunities.lock",
    )


def test_norm_and_id():
    assert norm_key("Acme Corp!") == "acmecorp"
    a = make_opportunity_id("job", "Acme", "Frontend", "https://x.com/1")
    b = make_opportunity_id("job", "Acme", "Frontend", "https://x.com/1")
    assert a == b


def test_ensure_workbook_sheets(store: ExcelStore):
    path = store.ensure_workbook()
    assert path.is_file()
    rows = store.load_all_opportunities()
    assert rows == []
    stats = store.get_statistics()
    assert "total_opportunities" in stats


def test_upsert_preserves_manual_notes_and_status(store: ExcelStore):
    store.ensure_workbook()
    rec = OpportunityRecord(
        id=make_opportunity_id("job", "Acme", "React Engineer", "https://example.com/j1"),
        opportunity_type="job",
        company="Acme",
        role_or_title="React Engineer",
        source_url="https://example.com/j1",
        source_name="test",
        status="new",
        notes="",
    )
    score_job(rec)
    r1 = store.upsert_opportunities([rec], backup=False)
    assert r1["added"] == 1

    # Simulate manual Excel edit by upserting with different status/notes then
    # ensuring second agent upsert keeps manual values when already set.
    from openpyxl import load_workbook

    wb = load_workbook(store.path)
    ws = wb["All Opportunities"]
    # Status col 30, Notes col 32 in ALL_OPPORTUNITIES_COLUMNS (1-indexed)
    headers = [c.value for c in ws[1]]
    status_i = headers.index("Status") + 1
    notes_i = headers.index("Notes") + 1
    ws.cell(2, status_i).value = "shortlisted"
    ws.cell(2, notes_i).value = "manual note keep me"
    wb.save(store.path)

    rec2 = OpportunityRecord(
        id=rec.id,
        opportunity_type="job",
        company="Acme",
        role_or_title="React Engineer",
        source_url="https://example.com/j1",
        source_name="test",
        description="updated description",
        status="new",
        notes="agent overwrite attempt",
        opportunity_score=80,
        grade="B",
    )
    r2 = store.upsert_opportunities([rec2], backup=False)
    assert r2["updated"] == 1
    loaded = store.load_all_opportunities()
    assert len(loaded) == 1
    assert loaded[0].status == "shortlisted"
    assert loaded[0].notes == "manual note keep me"
    assert "updated description" in (loaded[0].description or "")


def test_dedupe_by_url(store: ExcelStore):
    store.ensure_workbook()
    a = OpportunityRecord(
        id="job_a",
        opportunity_type="job",
        company="Beta",
        role_or_title="Full Stack",
        source_url="https://example.com/same",
        source_name="t",
    )
    b = OpportunityRecord(
        id="job_b_different_id",
        opportunity_type="job",
        company="Beta Inc",
        role_or_title="Full Stack Engineer",
        source_url="https://example.com/same",
        source_name="t",
    )
    store.upsert_opportunities([a], backup=False)
    store.upsert_opportunities([b], backup=False)
    assert len(store.load_all_opportunities()) == 1


def test_job_and_client_scoring():
    job = OpportunityRecord(
        id="1",
        opportunity_type="job",
        company="X",
        role_or_title="Senior React Next.js TypeScript Engineer",
        description="Remote worldwide visa sponsorship Next.js SaaS",
        remote_type="remote",
        visa_sponsorship="yes",
        source_url="https://example.com/1",
        sponsorship_class="verified_in_listing",
        posted_date="2099-01-01",
        contact_email="jobs@example.com",
    )
    # freshness uses today — use empty posted for stable mid score or recent
    from datetime import date

    job.posted_date = date.today().isoformat()
    score_job(job)
    assert job.opportunity_score >= 50
    assert job.grade in ("A", "B", "C", "Low")

    client = OpportunityRecord(
        id="2",
        opportunity_type="client",
        company="Y",
        role_or_title="Need React developer for MVP",
        description="Looking for a full-stack React developer to build our SaaS MVP this month with budget",
        intent_classification="EXPLICIT_DEMAND",
        salary_or_budget="$5k",
        contact_email="founder@example.com",
        posted_date=date.today().isoformat(),
    )
    score_client(client)
    assert client.opportunity_score >= 50


def test_new_rows_store_discovered_clock_time(store: ExcelStore):
    store.ensure_workbook()
    rec = OpportunityRecord(
        id=make_opportunity_id("client", "ClockCo", "Need React", "https://example.com/clock"),
        opportunity_type="client",
        company="ClockCo",
        role_or_title="Need React",
        source_url="https://example.com/clock",
        source_name="test",
        discovered_date="2026-11-25",  # date-only must be upgraded on create
    )
    store.upsert_opportunities([rec], backup=False)
    loaded = store.load_all_opportunities()
    assert len(loaded) == 1
    disc = loaded[0].discovered_date
    assert len(disc) > 10
    assert disc.upper().endswith("AM") or disc.upper().endswith("PM")


def test_backfill_discovered_from_history(store: ExcelStore):
    from openpyxl import load_workbook

    from agent.models.opportunity import is_date_only_timestamp

    store.ensure_workbook()
    rec = OpportunityRecord(
        id="client_backfill_1",
        opportunity_type="client",
        company="HistCo",
        role_or_title="Need Next.js",
        source_url="https://example.com/hist",
        source_name="test",
        discovered_date="2026-11-25 03:15:00 PM",
    )
    store.upsert_opportunities([rec], backup=False)

    wb = load_workbook(store.path)
    ws = wb["All Opportunities"]
    headers = [c.value for c in ws[1]]
    disc_col = headers.index("Discovered Date") + 1
    ws.cell(2, disc_col).value = "2026-11-25"  # simulate legacy date-only
    wb.save(store.path)

    wb2 = load_workbook(store.path)
    assert store._backfill_discovered_times(wb2) is True
    store._atomic_save(wb2)
    loaded = store.load_all_opportunities()
    assert not is_date_only_timestamp(loaded[0].discovered_date)


def test_backup(store: ExcelStore):
    store.ensure_workbook()
    path = store.backup("test")
    assert path.is_file()


def test_source_performance(store: ExcelStore):
    store.ensure_workbook()
    store.record_source_run("unit_source", success=True, new_records=2)
    store.record_source_run("unit_source", success=False, error="boom")
    # no exception = pass
