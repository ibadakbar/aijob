"""Generate personalized outreach drafts — never send, never fabricate familiarity."""

from __future__ import annotations

from .agency_partnership import partnership_outreach_body
from .model import Lead, OutreachDraft
from .sanitize import sanitize_text


def _facts(lead: Lead) -> list[str]:
    facts: list[str] = []
    for ev in lead.evidence[:3]:
        if ev.summary:
            facts.append(sanitize_text(ev.summary, max_len=160))
        if ev.published_date:
            facts.append(f"Evidence dated {ev.published_date}")
    if lead.budget_or_salary:
        facts.append(f"Compensation stated as {lead.budget_or_salary}")
    if lead.technical_requirements:
        facts.append("Stack mentioned: " + ", ".join(lead.technical_requirements[:6]))
    if lead.opportunity and lead.opportunity.event_type != "none":
        facts.append(f"Radar: {lead.opportunity.summary} (demand_proven={lead.opportunity.demand_proven})")
    if lead.partnership and lead.partnership.is_agency:
        facts.append(
            f"Agency partnership fit: {lead.partnership.partnership_fit}"
        )
    if lead.preferred_contact:
        pc = lead.preferred_contact
        facts.append(
            f"Preferred contact path: {pc.role}"
            + (f" via {pc.channel_type}" if pc.channel_type else "")
            + (f" ({pc.value})" if pc.value else "")
        )
    return facts


def generate_outreach(lead: Lead, *, candidate_name: str = "Ibad Akbar") -> OutreachDraft:
    """Build review-only outreach. send_approved is always False."""
    facts = _facts(lead)
    stack = ", ".join(lead.technical_requirements[:4]) or "React, Next.js, and Node.js"
    company = lead.company
    title = lead.title
    partnership_pitch = ""

    # Agency partnership pitch takes priority over generic freelance copy.
    if (
        lead.partnership
        and lead.partnership.is_agency
        and lead.partnership.partnership_fit != "none"
    ):
        partnership_pitch = partnership_outreach_body(lead, candidate_name=candidate_name)
        subject = f"White-label / overflow React–Next partnership with {company}"
        email = partnership_pitch
        networking = (
            f"Hi — I partner with agencies on React/Next.js delivery "
            f"(white-label / overflow), not competing for your clients. "
            f"Open to a short chat about capacity at {company}."
        )
        proposal = lead.partnership.pitch_angle or lead.recommended_service
        cta = "Would a short partnership intro call be useful for overflow capacity?"
        application = ""
        recruiter = ""
    elif lead.source in ("ycombinator", "yc") or (lead.raw or {}).get("founders"):
        founders = (lead.raw or {}).get("founders") or []
        first = founders[0] if founders else {}
        founder_name = (first.get("full_name") or "").split(" ")[0] or "there"
        product = (lead.raw or {}).get("product") or (lead.raw or {}).get("one_liner") or title
        batch = (lead.raw or {}).get("batch") or "YC"
        subject = f"React/Next help for {company} ({batch})"
        email = (
            f"Hi {founder_name},\n\n"
            f"I am {candidate_name}, a full-stack engineer (React/Next.js/TypeScript/Node). "
            f"I saw {company} on the YC directory"
            + (f" — “{product}”" if product else "")
            + f". I help early product teams ship SaaS UI and APIs quickly "
            f"(dashboards, performance, end-to-end features).\n\n"
            f"If you need contract or full-time product engineering capacity, "
            f"happy to share a short relevant work sample — no obligation.\n\n"
            f"Best regards,\n{candidate_name}"
        )
        networking = (
            f"Hi {founder_name} — saw {company} ({batch}) on YC. "
            f"I build React/Next/TS SaaS product work. Open to a short chat if you are "
            f"hiring or need overflow engineering."
        )
        proposal = lead.recommended_service or stack
        cta = "Open to a 15-minute intro if useful?"
        application = ""
        recruiter = ""
        partnership_pitch = ""
    elif lead.lead_type in ("client", "freelance") or (
        lead.intent == "EXPLICIT_DEMAND" and lead.lead_type != "full_time"
    ):
        subject = f"{stack.split(',')[0].strip().title()} help for {company}"
        email = (
            f"Hi {company} team,\n\n"
            f"I saw your public note about “{title}”"
            + (f" ({lead.evidence[0].published_date})" if lead.evidence and lead.evidence[0].published_date else "")
            + f". I am {candidate_name}, a full-stack engineer (React/Next.js/TypeScript/Node) "
            f"with experience shipping SaaS dashboards, APIs, and product UI.\n\n"
            f"If useful, I can help with: {lead.recommended_service or stack}. "
            f"Happy to share relevant work from my portfolio and a short plan based on your brief — "
            f"no obligation.\n\n"
            f"Best regards,\n{candidate_name}"
        )
        networking = (
            f"Hi — noticed your request for {title}. I build SaaS/product work with {stack}. "
            f"Open to a short chat if you are still looking."
        )
        proposal = lead.recommended_service or f"Scoped {lead.lead_type} delivery using {stack}."
        cta = "If this is still open, would a 15-minute call this week be useful?"
        application = ""
        recruiter = ""
    else:
        subject = f"Application interest: {title}"
        email = (
            f"Dear Hiring Manager,\n\n"
            f"I am writing about the {title} role at {company}. "
            f"I am {candidate_name}, a full-stack engineer focused on React, Next.js, TypeScript, "
            f"and Node.js, currently shipping SaaS product work remotely.\n\n"
            f"Your listing’s emphasis on {stack} aligns with work I do day to day. "
            f"I would welcome the chance to share a tailored CV and discuss the role.\n\n"
            f"Kind regards,\n{candidate_name}"
        )
        networking = (
            f"Hello — interested in the {title} opening at {company}. "
            f"Full-stack React/Next/Node background; happy to connect."
        )
        proposal = ""
        cta = "May I send a short CV tailored to this role?"
        application = (
            f"I am applying for {title} at {company}. Matching strengths: {stack}. "
            f"Evidence reviewed: {facts[0] if facts else lead.url}."
        )
        recruiter = (
            f"Hi — reaching out about {title} at {company}. "
            f"I am a full-stack engineer (React/Next.js/TypeScript/Node) open to "
            f"{'sponsored ' if 'sponsor' in (lead.intent_explanation or '').lower() else ''}"
            f"remote/international roles. Happy to share materials if helpful."
        )

    # Address the preferred contact path when known (without inventing a name).
    if lead.preferred_contact and lead.preferred_contact.role == "founder" and "Hi " in email:
        email = email.replace("Hi {company} team,".format(company=company), f"Hi {company} team,", 1)
        if lead.preferred_contact.name:
            email = email.replace(
                f"Hi {company} team,",
                f"Hi {lead.preferred_contact.name},",
                1,
            )

    banned = ("i reviewed your website", "i found a bug", "i noticed an issue on your site")
    for field in (email, networking, proposal, partnership_pitch):
        lower = field.lower()
        for b in banned:
            if b in lower:
                raise ValueError("outreach generator refused unverifiable website-audit claim")

    return OutreachDraft(
        subject=subject[:120],
        email_body=email.strip(),
        networking_message=networking.strip(),
        service_proposal=proposal,
        call_to_action=cta,
        personalization_facts=facts,
        application_message=application,
        recruiter_outreach=recruiter,
        partnership_pitch=partnership_pitch,
        send_approved=False,
    )
