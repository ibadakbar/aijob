"""Target geos: Europe, USA, UK, Australia, NZ, Canada — authentic contacts only."""
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
    lead_types=["freelance", "contract", "full_time"],
    technologies=["react", "next.js", "typescript", "node.js", "full-stack"],
    geographies=["Europe", "United States", "United Kingdom", "Australia", "New Zealand", "Canada"],
    workplace=["remote", "hybrid", "onsite"],
    require_sponsorship=True,
    limit=25,
    freshness_days=120,
    excluded_sources=["upwork", "freelancer", "fiverr"],
    raw_prompt="Target EU/US/UK/AU/NZ/CA authentic developer hiring",
)


def contacts(email: str, url: str, *, phone=None, name=None):
    out = [
        ContactChannel(
            channel_type="email",
            value=email,
            name=name,
            source_url=url,
            verification_status="published_on_official_source",
            verification_method="literal_email_on_official_page_or_hiring_post",
            date_checked=today,
            notes="Published publicly. Mailbox existence not proven.",
        )
    ]
    if phone:
        out.append(
            ContactChannel(
                channel_type="professional_profile",
                value=phone,
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
        "company": "UntilNow",
        "title": "Senior Full-Stack Developer (3–6 mo contract)",
        "url": "https://www.untilnow.com.au/careers/senior-full-stack-developer",
        "geo": "Australia (remote; overseas OK)",
        "lead_type": "contract",
        "desc": (
            "Sydney studio building Rally: React/TS + NestJS/TS remote contract "
            "3–6 months, open to Australia and overseas. AU hours. "
            "hello@untilnow.com.au / +61 280 745 406."
        ),
        "email": "hello@untilnow.com.au",
        "phone": "+61 280 745 406",
        "techs": ["react", "typescript", "nestjs", "postgresql", "aws"],
        "salary": "Contract (not published)",
        "risks": ["AU business hours from PK", "NestJS depth"],
        "fit": "React/TS strong; overseas explicitly allowed",
        "platform": "Company careers (AU)",
    },
    {
        "company": "Stat Sniper",
        "title": "Full Stack TypeScript Engineer",
        "url": "https://statsniper.com/careers/full-stack-typescript-engineer/",
        "geo": "USA company — remote worldwide",
        "lead_type": "full_time",
        "desc": (
            "Newport Beach CA sports AI app. Next.js App Router / React 19 / "
            "Tailwind / Postgres / Cloud Run. Worldwide remote. "
            "careers@statsniper.com."
        ),
        "email": "careers@statsniper.com",
        "phone": None,
        "techs": ["typescript", "next.js", "react", "postgresql"],
        "salary": "Not stated",
        "risks": ["Betting/gaming domain", "No phone on careers"],
        "fit": "Excellent Next/React/TS match; worldwide remote",
        "platform": "Company careers (US)",
    },
    {
        "company": "10ML",
        "title": "Senior Full-Stack Engineer, E-commerce (TS/Next.js)",
        "url": "https://10ml.com/careers",
        "geo": "Germany / remote within EU",
        "lead_type": "full_time",
        "desc": (
            "Dortmund EU perfume e-commerce hiring Senior FS TypeScript/Next.js "
            "€110–155k + bonus, remote within EU. jobs@10ml.com."
        ),
        "email": "jobs@10ml.com",
        "phone": None,
        "techs": ["typescript", "next.js", "react", "e-commerce"],
        "salary": "€110,000 – €155,000 + bonus",
        "risks": ["EU-only remote — PK may need relocation/visa", "No phone"],
        "fit": "Strong stack + pay; eligibility risk outside EU",
        "platform": "Company careers (DE/EU)",
    },
    {
        "company": "Expatfile.tax",
        "title": "Senior Front-end Developer (freelance, 32h)",
        "url": "https://usemimi.com/jobs/remote-senior-front-end-developer-75k-at-expatfiletax-at-expatfile-tax-mnqe4f9k",
        "geo": "Netherlands / remote worldwide (CET)",
        "lead_type": "freelance",
        "desc": (
            "Amsterdam-linked FinTech: Senior FE Next.js/React/TS/GraphQL, "
            "freelance 4 days/week $70–90k. Apply hank@expatfile.tax."
        ),
        "email": "hank@expatfile.tax",
        "phone": None,
        "name": "Hank",
        "techs": ["next.js", "react", "typescript", "graphql"],
        "salary": "$70,000 – $90,000 / year (32h)",
        "risks": ["7+ yrs FE asked on some posts", "CET hours", "No phone"],
        "fit": "Next/React/TS core; remote freelance",
        "platform": "Job board + company (NL/EU)",
    },
    {
        "company": "Bidaya AI",
        "title": "Senior Full Stack Engineer",
        "url": "https://hnhiring.com/technologies/nextjs/months/february-2026",
        "geo": "Canada (Calgary) / HN",
        "lead_type": "full_time",
        "desc": (
            "HN Who's Hiring Feb 2026: Bidaya AI Calgary Senior Full Stack "
            "(Next.js, React, FastAPI, Temporal). Email majd@bidaya.ai."
        ),
        "email": "majd@bidaya.ai",
        "phone": None,
        "name": "Majd",
        "techs": ["next.js", "react", "python", "fastapi"],
        "salary": "Not stated",
        "risks": ["May expect CA presence", "Python/FastAPI backend", "No phone"],
        "fit": "Next/React match; Canada target geo",
        "platform": "Hacker News Who's Hiring",
    },
    {
        "company": "Silkline",
        "title": "Frontend / Full-stack (HN)",
        "url": "https://hnhiring.com/technologies/nextjs/months/february-2026",
        "geo": "US / remote (HN)",
        "lead_type": "full_time",
        "desc": (
            "HN Feb 2026 Silkline listing: questions to brent@silkline.ai "
            "(mention HN). Apply also via Gem jobs link on HN post."
        ),
        "email": "brent@silkline.ai",
        "phone": None,
        "name": "Brent",
        "techs": ["react", "next.js", "typescript"],
        "salary": "Not stated",
        "risks": ["Confirm role still open", "No phone"],
        "fit": "HN founder email for US remote stack roles",
        "platform": "Hacker News Who's Hiring",
    },
    {
        "company": "VyrroTech",
        "title": "Senior Full-Stack Engineer",
        "url": "https://vyrrotech.com/careers/senior-full-stack-engineer",
        "geo": "UAE HQ — markets US/UK/UAE/KSA",
        "lead_type": "full_time",
        "desc": (
            "Already verified: hello@vyrrotech.com; UAE +971 58 570 7287; "
            "UK +44 7368 408232. Serves UK/US markets."
        ),
        "email": "hello@vyrrotech.com",
        "phone": "+44 7368 408232",
        "techs": ["typescript", "react", "next.js", "node.js"],
        "salary": "Not stated",
        "risks": ["Remote-hybrid — confirm PK remote"],
        "fit": "UK phone + US/UK client markets",
        "platform": "Company careers (UK/UAE)",
    },
    {
        "company": "8Byte Digital",
        "title": "Full-Stack Entwickler (React/Next/TS)",
        "url": "https://8byte.de/jobs/",
        "geo": "Germany remote/hybrid",
        "lead_type": "full_time",
        "desc": "DE agency: hallo@8byte.de / +49 2592 9786601. React Next TS.",
        "email": "hallo@8byte.de",
        "phone": "+49 2592 9786601",
        "techs": ["react", "next.js", "typescript", "node.js"],
        "salary": "Not stated",
        "risks": ["Hybrid may prefer EU", "German context"],
        "fit": "Europe target; core stack",
        "platform": "Company careers (DE)",
    },
    {
        "company": "EaseControl",
        "title": "Full-Stack Developer Node+React (FT/Freelance)",
        "url": "https://www.easecontrol.de/karriere",
        "geo": "Germany remote",
        "lead_type": "freelance",
        "desc": "DE ERP startup FT/freelance 20–40h. jobs@easecontrol.de.",
        "email": "jobs@easecontrol.de",
        "phone": None,
        "techs": ["node.js", "react", "postgresql"],
        "salary": "Not stated",
        "risks": ["German product", "No phone"],
        "fit": "Europe freelance option",
        "platform": "Company careers (DE)",
    },
    {
        "company": "Numbered Agency",
        "title": "Full Stack Developer (React/Next + Shopify)",
        "url": "https://numbered.com/career/full-stack-developer",
        "geo": "Netherlands / France remote",
        "lead_type": "full_time",
        "desc": "Amsterdam/Lyon studio. jobs@numbered.com. Shopify+Next.",
        "email": "jobs@numbered.com",
        "phone": None,
        "techs": ["react", "next.js", "typescript", "shopify"],
        "salary": "Based on experience",
        "risks": ["EU preference possible", "No phone"],
        "fit": "EU + Shopify differentiator",
        "platform": "Company careers (NL/FR)",
    },
    {
        "company": "Babou",
        "title": "Agent-Native Software Engineer",
        "url": "https://babou.ai/careers",
        "geo": "Remote worldwide (HN + careers)",
        "lead_type": "full_time",
        "desc": "TS/Next/Node/Postgres. careers@babou.ai. Worldwide.",
        "email": "careers@babou.ai",
        "phone": None,
        "techs": ["typescript", "next.js", "node.js", "postgresql"],
        "salary": "Not stated",
        "risks": ["High agent-native bar", "No phone"],
        "fit": "US/EU-friendly remote product startup",
        "platform": "Company + HN",
    },
    {
        "company": "entrecode",
        "title": "Senior Frontend React/TypeScript",
        "url": "https://entrecode.de/jobs",
        "geo": "Germany Stuttgart / Remote",
        "lead_type": "full_time",
        "desc": "jobs@entrecode.de Senior Frontend React/TS remote.",
        "email": "jobs@entrecode.de",
        "phone": None,
        "techs": ["react", "typescript", "node.js"],
        "salary": "Not stated",
        "risks": ["May prefer DE employment", "No phone"],
        "fit": "Europe React/TS",
        "platform": "Company careers (DE)",
    },
]


def main() -> None:
    leads: list[Lead] = []
    for r in ROWS:
        lead = Lead(
            id=make_lead_id(
                source="websearch_target_geo",
                company=r["company"],
                title=r["title"],
                url=r["url"],
            ),
            name=f"{r['company']} — {r['title']}",
            lead_type=r["lead_type"],
            company=r["company"],
            title=r["title"],
            url=r["url"],
            source="websearch_target_geo",
            intent="EXPLICIT_DEMAND",
            intent_explanation=(
                f"Public hiring targeting {r['geo']} via {r['platform']}"
            ),
            evidence=[
                Evidence(
                    summary=r["desc"][:320],
                    excerpt=r["desc"][:320],
                    source_url=r["url"],
                    checked_date=today,
                )
            ],
            technical_requirements=r["techs"],
            profile_match_reasons=[r["fit"], f"Target geo: {r['geo']}"],
            recommended_service=r["title"],
            contacts=contacts(
                r["email"], r["url"], phone=r.get("phone"), name=r.get("name")
            ),
            budget_or_salary=r["salary"],
            location=r["geo"],
            workplace="remote",
            checked_date=today,
            risks=r["risks"],
            next_action=f"Email {r['email']} with CV + portfolio.",
            status="qualified",
            notes=f"target_geo={r['geo']}; platform={r['platform']}",
        )
        lead.scores = score_lead(lead, crit)
        lead.outreach = generate_outreach(lead)
        lead.outreach.subject = f"Application — {r['title']} @ {r['company']}"
        lead.outreach.send_approved = False
        leads.append(lead)

    leads = dedupe_leads(leads)
    leads.sort(
        key=lambda L: (
            0 if any((c.title or "").startswith("Phone") for c in L.contacts) else 1,
            -(L.scores.overall if L.scores else 0),
        )
    )
    info = upsert_leads(leads, ROOT / "leads" / "store" / "leads_store.json")
    paths = export_run(
        leads,
        crit,
        source_meta={
            "mode": "target_geo_eu_us_uk_au_nz_ca",
            "geographies": [
                "Europe",
                "USA",
                "UK",
                "Australia",
                "New Zealand",
                "Canada",
            ],
            "apis": "remotive+arbeitnow export 20261027-162732; visa_discover 40 hits",
            "linkedin": "bun unavailable — WebSearch fallback only (low volume)",
            "note": "Only published emails/phones. No Upwork.",
        },
        run_id=date.today().strftime("%Y%m%d") + "-target-geo",
    )
    print(
        json.dumps(
            {
                "persist": info,
                "export": str(paths["dir"]),
                "leads": [
                    {
                        "id": L.id,
                        "company": L.company,
                        "geo": L.location,
                        "type": L.lead_type,
                        "email": next(
                            (c.value for c in L.contacts if c.channel_type == "email"),
                            None,
                        ),
                        "phone": next(
                            (
                                c.value
                                for c in L.contacts
                                if (c.title or "").startswith("Phone")
                            ),
                            None,
                        ),
                        "fit": round(L.scores.fit_score, 2) if L.scores else None,
                        "url": L.url,
                    }
                    for L in leads
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
