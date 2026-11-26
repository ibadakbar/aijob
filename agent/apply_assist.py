"""Review-before-send apply assist — never auto-submits applications.

Opens the employer/Arbeitnow apply URL in the browser, writes a draft email +
application packet for the user to copy, and can mark the Excel row drafted/applied.
"""

from __future__ import annotations

import re
import webbrowser
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from urllib.parse import quote

from agent.models.opportunity import OpportunityRecord, norm_key, now_iso

ROOT = Path(__file__).resolve().parents[1]
DRAFTS_DIR = ROOT / "data" / "apply_drafts"

CANDIDATE = {
    "name": "Ibad Akbar",
    "email": "ibad_2000@hotmail.com",
    "phone": "+923131163184",
    "linkedin": "https://www.linkedin.com/in/ibad-akbar",
    "github": "https://github.com/ibadakbar",
    "portfolio": "https://ibadakbar.netlify.app",
    "location": "Karachi, Pakistan (remote-first)",
    "headline": "Senior Software Engineer | React & Next.js | Full-Stack TypeScript",
}


@dataclass
class ApplyPacket:
    opportunity_id: str
    company: str
    title: str
    apply_url: str
    contact_email: str
    source_name: str
    subject: str
    email_body: str
    short_pitch: str
    form_answers: dict[str, str]
    checklist: list[str] = field(default_factory=list)
    draft_path: str = ""
    mailto_url: str = ""
    is_arbeitnow: bool = False
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def is_arbeitnow(rec: OpportunityRecord) -> bool:
    blob = f"{rec.source_name} {rec.source_url}".casefold()
    return "arbeitnow" in blob


def apply_url_for(rec: OpportunityRecord) -> str:
    return (rec.source_url or rec.company_website or "").strip()


def _slug(company: str, title: str) -> str:
    raw = f"{norm_key(company)}_{norm_key(title)}"[:48] or "role"
    return re.sub(r"_+", "_", raw).strip("_") or "role"


def _greeting(rec: OpportunityRecord) -> str:
    name = (rec.contact_name or "").strip()
    if name:
        first = name.split()[0]
        return f"Dear {first},"
    return "Dear Hiring Manager,"


def build_apply_packet(rec: OpportunityRecord) -> ApplyPacket:
    """Build review-only drafts. Does not send email or submit forms."""
    company = (rec.company or "the team").strip()
    title = (rec.role_or_title or "the role").strip()
    url = apply_url_for(rec)
    email = (rec.contact_email or "").strip()
    arbeitnow = is_arbeitnow(rec)

    subject = f"Application: {title} — {CANDIDATE['name']}"
    stack_hint = ""
    blob = f"{rec.required_skills} {rec.description} {title}".casefold()
    bits = []
    for token, label in (
        ("next.js", "Next.js"),
        ("react", "React"),
        ("typescript", "TypeScript"),
        ("node", "Node.js"),
    ):
        if token in blob:
            bits.append(label)
    if bits:
        stack_hint = f" My recent work centers on {', '.join(bits)}."

    why = ""
    if rec.evidence:
        excerpt = str(rec.evidence)[:180].replace("\n", " ")
        why = f" I reviewed the posting ({excerpt}…) and believe my SaaS/product delivery background is a strong match."
    elif rec.description:
        why = " I reviewed the role requirements and can contribute quickly on UI, APIs, and product delivery."

    body = (
        f"{_greeting(rec)}\n\n"
        f"I am applying for the {title} role at {company}.\n\n"
        f"I am {CANDIDATE['name']}, a full-stack engineer ({CANDIDATE['headline']}) "
        f"with 5+ years building React/Next.js/TypeScript SaaS products remotely "
        f"(currently Full Stack Developer at Plai, US remote).{stack_hint}{why}\n\n"
        f"I am based in {CANDIDATE['location']} and open to remote-international "
        f"or visa-sponsored roles into your target markets.\n\n"
        f"Portfolio: {CANDIDATE['portfolio']}\n"
        f"LinkedIn: {CANDIDATE['linkedin']}\n"
        f"GitHub: {CANDIDATE['github']}\n\n"
        f"Happy to share my CV and walk through relevant work. Thank you for your time.\n\n"
        f"Best regards,\n"
        f"{CANDIDATE['name']}\n"
        f"{CANDIDATE['email']}\n"
        f"{CANDIDATE['phone']}\n"
    )

    short_pitch = (
        f"{CANDIDATE['name']} — full-stack React/Next.js/TypeScript engineer (5+ yrs). "
        f"Applying for {title} at {company}. Portfolio: {CANDIDATE['portfolio']}"
    )

    form_answers = {
        "Full name": CANDIDATE["name"],
        "Email": CANDIDATE["email"],
        "Phone": CANDIDATE["phone"],
        "Location / city": CANDIDATE["location"],
        "LinkedIn": CANDIDATE["linkedin"],
        "GitHub": CANDIDATE["github"],
        "Portfolio / website": CANDIDATE["portfolio"],
        "Current title": "Full Stack Developer",
        "Current company": "Plai (Remote, United States)",
        "Years of experience": "5+",
        "Work authorization note": (
            "Pakistan-based; seeking remote-international hire and/or visa sponsorship "
            "+ relocation into DE/NL/UK/IE/AU/NZ/CA/US/EU/UAE (not India)."
        ),
        "Notice period": "As negotiated / typically 2–4 weeks",
        "Salary expectation": "Open — happy to align with your band for the market",
        "How did you hear about us": (
            f"Arbeitnow" if arbeitnow else (rec.source_name or "Company careers / job board")
        ),
    }

    checklist = [
        "Open the apply URL and confirm the role is still open",
        "Attach latest CV (PDF) — tailor with /apply if Grade A",
        "Paste email body or form answers; review before submit",
        "Do not invent salary/visa claims beyond the note above",
        "After you submit manually, mark status Applied in the dashboard",
    ]
    if arbeitnow:
        checklist.insert(
            1,
            "Arbeitnow usually redirects to employer ATS/email — complete the apply there",
        )
    if email:
        checklist.insert(2, f"Or email {email} with subject + body below (review first)")

    mailto = ""
    if email:
        mailto = (
            f"mailto:{email}?subject={quote(subject)}&body={quote(body)}"
        )

    notes = (
        "Review-only assist. Nothing is sent automatically. "
        + ("Source: Arbeitnow. " if arbeitnow else "")
        + (f"Path={rec.path} Grade={rec.grade} Score={rec.opportunity_score}." if rec.grade else "")
    )

    return ApplyPacket(
        opportunity_id=rec.id,
        company=company,
        title=title,
        apply_url=url,
        contact_email=email,
        source_name=rec.source_name or "",
        subject=subject,
        email_body=body,
        short_pitch=short_pitch,
        form_answers=form_answers,
        checklist=checklist,
        mailto_url=mailto,
        is_arbeitnow=arbeitnow,
        notes=notes,
    )


def save_apply_draft(packet: ApplyPacket, *, directory: Path | None = None) -> Path:
    """Write a Markdown packet the user can copy from."""
    out_dir = Path(directory or DRAFTS_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = out_dir / f"apply_{_slug(packet.company, packet.title)}_{stamp}.md"
    lines = [
        f"# Apply draft — {packet.company} / {packet.title}",
        "",
        f"- Opportunity ID: `{packet.opportunity_id}`",
        f"- Source: {packet.source_name or '—'}",
        f"- Arbeitnow: {'yes' if packet.is_arbeitnow else 'no'}",
        f"- Apply URL: {packet.apply_url or '—'}",
        f"- Contact email: {packet.contact_email or '—'}",
        f"- Generated: {now_iso()}",
        "",
        "> Review before sending. This assistant never auto-submits.",
        "",
        "## Checklist",
        *[f"- [ ] {c}" for c in packet.checklist],
        "",
        "## Email subject",
        packet.subject,
        "",
        "## Email body",
        "```",
        packet.email_body.rstrip(),
        "```",
        "",
        "## Short pitch (ATS free-text)",
        packet.short_pitch,
        "",
        "## Form field answers",
    ]
    for k, v in packet.form_answers.items():
        lines.append(f"- **{k}:** {v}")
    lines.extend(["", "## Notes", packet.notes, ""])
    path.write_text("\n".join(lines), encoding="utf-8")
    packet.draft_path = str(path)
    return path


def open_apply_url(url: str) -> bool:
    """Open apply URL in the default browser. Returns False if URL missing."""
    u = (url or "").strip()
    if not u.startswith(("http://", "https://")):
        return False
    webbrowser.open(u)
    return True


def open_mailto(mailto_url: str) -> bool:
    """Open mail client with prefilled draft (user still must send)."""
    m = (mailto_url or "").strip()
    if not m.startswith("mailto:"):
        return False
    webbrowser.open(m)
    return True


def rank_apply_candidates(rows: list[OpportunityRecord]) -> list[OpportunityRecord]:
    """Prefer Arbeitnow + high grade + has URL/email; skip expired."""
    skip = {"expired", "closed", "rejected", "withdrawn", "applied"}
    scored: list[tuple[tuple, OpportunityRecord]] = []
    for r in rows:
        if (r.status or "").strip().lower() in skip:
            continue
        url = apply_url_for(r)
        email = (r.contact_email or "").strip()
        if not url and not email:
            continue
        otype = (r.opportunity_type or "").lower()
        if otype not in ("job", "contract", "freelance", "client", ""):
            continue
        key = (
            0 if is_arbeitnow(r) else 1,
            0 if (r.grade or "") == "A" else 1 if (r.grade or "") == "B" else 2,
            -float(r.opportunity_score or 0),
            0 if email else 1,
            0 if url else 1,
        )
        scored.append((key, r))
    scored.sort(key=lambda x: x[0])
    return [r for _, r in scored]


def prepare_application(
    rec: OpportunityRecord,
    *,
    open_url: bool = True,
    open_mail: bool = False,
    save_draft: bool = True,
) -> ApplyPacket:
    """Build packet, optionally open browser/mail, save markdown draft."""
    packet = build_apply_packet(rec)
    if save_draft:
        save_apply_draft(packet)
    if open_url and packet.apply_url:
        open_apply_url(packet.apply_url)
    if open_mail and packet.mailto_url:
        open_mailto(packet.mailto_url)
    return packet
