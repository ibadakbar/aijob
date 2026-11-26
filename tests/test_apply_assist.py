"""Apply assist — review-only drafts, never auto-submit."""

from __future__ import annotations

from pathlib import Path

from agent.apply_assist import (
    build_apply_packet,
    is_arbeitnow,
    prepare_application,
    rank_apply_candidates,
    save_apply_draft,
)
from agent.models.opportunity import OpportunityRecord


def test_arbeitnow_detection_and_packet(tmp_path: Path):
    rec = OpportunityRecord(
        id="job_an_1",
        opportunity_type="job",
        company="Acme DE",
        role_or_title="React Engineer",
        source_name="arbeitnow",
        source_url="https://www.arbeitnow.com/jobs/react-engineer-berlin",
        contact_email="jobs@acme.example",
        grade="A",
        opportunity_score=88,
        required_skills="React Next.js TypeScript",
        status="qualified",
    )
    assert is_arbeitnow(rec) is True
    packet = build_apply_packet(rec)
    assert packet.is_arbeitnow is True
    assert "Acme DE" in packet.email_body
    assert "Ibad Akbar" in packet.email_body
    assert packet.form_answers["Email"] == "ibad_2000@hotmail.com"
    assert "auto-submit" not in packet.notes.lower() or "never" in packet.notes.lower()
    path = save_apply_draft(packet, directory=tmp_path)
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "Review before sending" in text
    assert packet.subject in text


def test_rank_prefers_arbeitnow():
    an = OpportunityRecord(
        id="1",
        opportunity_type="job",
        company="AN Co",
        role_or_title="FS",
        source_name="arbeitnow",
        source_url="https://www.arbeitnow.com/x",
        grade="B",
        opportunity_score=70,
        status="new",
    )
    other = OpportunityRecord(
        id="2",
        opportunity_type="job",
        company="Other",
        role_or_title="FS",
        source_name="remotive",
        source_url="https://example.com/y",
        grade="A",
        opportunity_score=90,
        status="new",
    )
    ranked = rank_apply_candidates([other, an])
    assert ranked[0].company == "AN Co"


def test_prepare_without_opening(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("agent.apply_assist.DRAFTS_DIR", tmp_path)
    rec = OpportunityRecord(
        id="3",
        opportunity_type="job",
        company="Kiwi",
        role_or_title="Next.js Dev",
        source_url="https://example.com/nz",
        location="Auckland, New Zealand",
        status="new",
        opportunity_score=60,
    )
    packet = prepare_application(rec, open_url=False, open_mail=False, save_draft=True)
    assert packet.draft_path
    assert Path(packet.draft_path).is_file()
