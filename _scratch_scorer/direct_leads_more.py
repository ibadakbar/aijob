"""Add another batch of direct-contact (email/phone) React/Next leads."""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from leads.engine.dedupe import dedupe_leads, make_lead_id
from leads.engine.export import export_run
from leads.engine.model import ContactChannel, Evidence, Lead, SearchCriteria
from leads.engine.outreach import generate_outreach
from leads.engine.persist import upsert_leads
from leads.engine.score import score_lead

today = date.today().isoformat()
crit = SearchCriteria(
    lead_types=["client", "freelance", "contract"],
    technologies=["react", "next.js", "typescript", "node.js"],
    workplace=["remote"],
    limit=20,
    freshness_days=90,
    excluded_sources=["upwork", "freelancer", "fiverr", "peopleperhour"],
    raw_prompt="More direct email/phone client leads excluding marketplaces",
)


def contacts(email: str, url: str, *, name=None, title=None, phone=None):
    out = [
        ContactChannel(
            channel_type="email",
            value=email,
            name=name,
            title=title,
            source_url=url,
            verification_status="published_on_official_source",
            verification_method="literal_email_on_official_page_or_hiring_post",
            date_checked=today,
            notes="Published publicly. Does not prove mailbox accepts mail.",
        )
    ]
    if phone:
        out.append(
            ContactChannel(
                channel_type="professional_profile",
                value=phone,
                name=name,
                title="Phone (published)",
                source_url=url,
                verification_status="published_on_official_source",
                verification_method="literal_phone_on_official_page",
                date_checked=today,
                notes="As published on official page.",
            )
        )
    out.append(
        ContactChannel(
            channel_type="application_page",
            value=url,
            source_url=url,
            verification_status="published_on_official_source",
            verification_method="listing_url",
            date_checked=today,
            notes="Original source page",
        )
    )
    return out


ROWS = [
    {
        "company": "Volito Digital",
        "title": "Senior Frontend Developer (React) — freelance for Norway client",
        "url": "https://volito.digital/jobs/senior-frontend-developer-react-16-02-2026/",
        "lead_type": "freelance",
        "desc": (
            "Long-term full-time freelance React/Redux/Next.js role, remote for Norway client. "
            "35 EUR/hour. Apply office@volito.digital. Phones +385 91 2844 288, +49 176 2558 8637."
        ),
        "email": "office@volito.digital",
        "phone": "+385 91 2844 288",
        "name": None,
        "title_role": "Hiring",
        "techs": ["react", "next.js", "typescript", "redux"],
        "salary": "35 EUR/hour",
        "risks": ["Live coding interview", "Min 12 months commitment"],
        "service": "Long-term freelance React/Next frontend for e-commerce client",
    },
    {
        "company": "ACEQES s.r.o.",
        "title": "Senior Next.js/React Developer — remote medical project",
        "url": "https://www.profesia.sk/praca/aceqes/O5174894",
        "lead_type": "freelance",
        "desc": (
            "Remote senior Next.js/React/TypeScript for medical-sector project. 25–30 EUR/hour. "
            "Send CV to hr@aceqes.com with availability, cooperation form, expected rate. "
            "Contact Ing. Stanislav Repko +421 944 130 665."
        ),
        "email": "hr@aceqes.com",
        "phone": "+421 944 130 665",
        "name": "Stanislav Repko",
        "title_role": "Contact",
        "techs": ["next.js", "react", "typescript"],
        "salary": "25–30 EUR/hour",
        "risks": ["Listing dated Mar 2026 — confirm still open", "English B2 required"],
        "service": "Senior React/Next medical web app development",
    },
    {
        "company": "ZenZ Innovation",
        "title": "Senior React Developer freelance (5–8 years)",
        "url": "https://zenzinnovation.com/Careers",
        "lead_type": "freelance",
        "desc": (
            "LinkedIn hiring post for senior React/Next.js freelance (FinTech/Real Estate/Enterprise). "
            "Apply hr@zenzinnovation.com. Company also publishes consulting@zenzinnovation.com "
            "and phones +1 279 248 7434 / +91 927 212 8181."
        ),
        "email": "hr@zenzinnovation.com",
        "phone": "+1 279 248 7434",
        "name": None,
        "title_role": "HR",
        "techs": ["next.js", "react", "typescript", "node.js"],
        "salary": "Not stated",
        "risks": ["Staffing/services firm — may be client placement", "Confirm remote from Pakistan"],
        "service": "Senior React/Next SaaS frontend freelance",
    },
    {
        "company": "Wynwood Tech",
        "title": "Senior React / Next.js Fullstack — remote US/German client",
        "url": "https://www.linkedin.com/posts/wynwoodtech_hiring-react-reactexpert-activity-7440347787273277440-9Qky",
        "lead_type": "contract",
        "desc": (
            "100% remote freelance/contract fullstack React/Next.js/Node for German tech client. "
            "Headless CMS (Sanity/Storyblok/Shopify) familiarity. Email recruiting@wynwood-tech.com "
            "with CV and earliest start date."
        ),
        "email": "recruiting@wynwood-tech.com",
        "phone": None,
        "name": None,
        "title_role": "Recruiting",
        "techs": ["react", "next.js", "typescript", "node.js"],
        "salary": "Not stated",
        "risks": ["Recruiter middleman", "Confirm contract terms and geo eligibility"],
        "service": "Remote React/Next fullstack contract",
    },
    {
        "company": "Weberspoint Agency",
        "title": "Full Stack Developer — freelance / project-based",
        "url": "https://www.linkedin.com/posts/weberspoint_fullstackdeveloper-hiring-webdeveloper-activity-7506442020089917440-xxU2",
        "lead_type": "freelance",
        "desc": (
            "Agency hiring freelance/project fullstack for client work: React, Next.js, Node.js, "
            "REST, MongoDB/MySQL/PostgreSQL. Send CV, portfolio, rate to weberspoint@gmail.com."
        ),
        "email": "weberspoint@gmail.com",
        "phone": None,
        "name": None,
        "title_role": "Hiring",
        "techs": ["react", "next.js", "node.js", "mongodb"],
        "salary": "Expected project rate (ask in email)",
        "risks": ["Gmail contact — less formal than corporate domain", "Confirm agency legitimacy"],
        "service": "Agency client projects React/Next/Node",
    },
    {
        "company": "ScaleTech",
        "title": "React Developer — 4–6 month B2B contract (client via ScaleTech)",
        "url": "https://jobs.lever.co/scale3c/07ee05b8-fae7-44e1-bd34-6b4e0855804d",
        "lead_type": "contract",
        "desc": (
            "Vilnius agency hiring React developer for identity-verification client. Fully remote, "
            "4–6 months B2B, 30–40 EUR/hour. Company contact hello@scaletech.lt / +370 611 32226. "
            "Also Lever apply form."
        ),
        "email": "hello@scaletech.lt",
        "phone": "+370 611 32226",
        "name": None,
        "title_role": "Company contact",
        "techs": ["react", "typescript"],
        "salary": "30–40 EUR/hour",
        "risks": ["macOS required", "Agency placement for end client"],
        "service": "Contract React frontend for compliance/ID product",
    },
    {
        "company": "Louco Event Media GmbH",
        "title": "Frontend Developer (React / Next.js) — remote freelance",
        "url": "https://www.arbeitnow.com/jobs/companies/louco-event-media-gmbh/frontend-developer-react-mobile-platform-remote-offenbach-437573",
        "lead_type": "freelance",
        "desc": (
            "Early-stage event platform hiring frontend with deep Next.js/React/TypeScript + Sanity. "
            "Remote freelance/contract. Company imprint publishes info@louco.app. Also JOIN apply portal."
        ),
        "email": "info@louco.app",
        "phone": None,
        "name": None,
        "title_role": "General contact",
        "techs": ["next.js", "react", "typescript"],
        "salary": "Competitive (not stated)",
        "risks": ["Prefer applying via JOIN portal too", "Startup stage"],
        "service": "Next.js frontend for event discovery SaaS",
    },
    {
        "company": "DotWorld",
        "title": "Fullstack Next.js developer — freelance long-term (Europe remote)",
        "url": "https://www.dotworld.ch/",
        "lead_type": "freelance",
        "desc": (
            "SaaS studio recruiting fullstack Next.js/TypeScript/Tailwind (AI design SaaS). "
            "Remote Europe, CDI or long-term freelance. Public emails contact@dotworld.ch and "
            "recruiter noemie.ngg@dotworld.ch. French fluency required."
        ),
        "email": "noemie.ngg@dotworld.ch",
        "phone": None,
        "name": "Noémie NGG",
        "title_role": "Talent Acquisition",
        "techs": ["next.js", "react", "typescript", "tailwind"],
        "salary": "Not stated",
        "risks": [
            "French fluency required — likely deal-breaker for current profile",
            "Europe-remote framing may exclude Pakistan",
        ],
        "service": "Next.js SaaS fullstack (only if French + EU remote OK)",
    },
]


def main() -> None:
    leads: list[Lead] = []
    for r in ROWS:
        lead = Lead(
            id=make_lead_id(
                source="websearch_direct",
                company=r["company"],
                title=r["title"],
                url=r["url"],
            ),
            name=f"{r['company']} — {r['title']}",
            lead_type=r["lead_type"],
            company=r["company"],
            title=r["title"],
            url=r["url"],
            source="websearch_direct",
            intent="EXPLICIT_DEMAND",
            intent_explanation="Public hiring/partner page or hiring post with published business email",
            evidence=[
                Evidence(
                    summary=r["desc"][:300],
                    excerpt=r["desc"][:300],
                    source_url=r["url"],
                    checked_date=today,
                )
            ],
            technical_requirements=r["techs"],
            recommended_service=r["service"],
            contacts=contacts(
                r["email"],
                r["url"],
                name=r.get("name"),
                title=r.get("title_role"),
                phone=r.get("phone"),
            ),
            budget_or_salary=r["salary"],
            location="Remote / see listing",
            workplace="remote",
            checked_date=today,
            risks=r["risks"],
            next_action=f"Email {r['email']} after approving outreach draft.",
            status="qualified",
        )
        lead.scores = score_lead(lead, crit)
        lead.outreach = generate_outreach(lead)
        lead.outreach.subject = f"React/Next.js availability for {r['company']}"
        lead.outreach.send_approved = False
        leads.append(lead)

    leads = dedupe_leads(leads)
    leads.sort(key=lambda L: -(L.scores.overall if L.scores else 0))
    info = upsert_leads(leads, ROOT / "leads" / "store" / "leads_store.json")
    paths = export_run(
        leads,
        crit,
        source_meta={
            "mode": "direct_contact_batch_2",
            "excluded": ["upwork", "freelancer", "fiverr", "peopleperhour", "white_label_competitors"],
            "note": "Buyers/recruiters with published email/phone only. No marketplace bids.",
        },
        run_id=date.today().strftime("%Y%m%d") + "-direct-more",
    )
    print(
        json.dumps(
            {
                "persist": info,
                "export": str(paths["dir"]),
                "leads": [
                    {
                        "id": L.id,
                        "fit": round(L.scores.fit_score, 2),
                        "all": round(L.scores.overall, 2),
                        "company": L.company,
                        "email": next(c.value for c in L.contacts if c.channel_type == "email"),
                        "phone": next(
                            (c.value for c in L.contacts if (c.title or "").startswith("Phone")),
                            None,
                        ),
                        "salary": L.budget_or_salary,
                        "url": L.url,
                        "risks": L.risks[:2],
                    }
                    for L in leads
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
