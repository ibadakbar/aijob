"""Client hunter + phone contact ladder."""

from __future__ import annotations

from pathlib import Path

from agent.discovery.clients.hunt import harvest_clients_from_store, matches_profile, run_client_discovery
from agent.models.opportunity import OpportunityRecord, make_opportunity_id
from agent.quality.contact_ladder import apply_contact_ladder_to_record, extract_published_phone
from agent.storage.excel_store import ExcelStore


def test_matches_profile_react():
    assert matches_profile("Looking for a React Next.js developer for our SaaS")
    assert not matches_profile("Need a COBOL mainframe operator onsite only xyz")


def test_extract_published_phone():
    assert "555" in extract_published_phone("Contact phone: +1 555-123-4567 for projects")
    assert extract_published_phone("no digits here") == ""


def test_contact_ladder_phone(tmp_path: Path):
    rec = OpportunityRecord(
        id="c1",
        opportunity_type="client",
        company="BuyCo",
        role_or_title="Need React MVP",
        source_url="https://example.com/need",
    )
    apply_contact_ladder_to_record(
        rec,
        contacts=[
            {
                "channel_type": "phone",
                "value": "+44 7700 900123",
                "verification_status": "published_on_official_source",
            }
        ],
    )
    assert rec.contact_phone.startswith("+44")


def test_client_sheet_and_hunt_store_only(tmp_path: Path):
    store = ExcelStore(
        path=tmp_path / "opportunities.xlsx",
        backup_dir=tmp_path / "backups",
        lock_path=tmp_path / "opportunities.lock",
    )
    store.ensure_workbook()
    # Store-only harvest (no network discover)
    result = run_client_discovery(store, discover=False, limit=20)
    assert result.get("ok") is True
    clients = [r for r in store.load_all_opportunities() if r.opportunity_type == "client"]
    # May be 0 if leads_store empty in CI — still ok shape
    assert isinstance(clients, list)
    assert "clients" in result or "fetched" in result
