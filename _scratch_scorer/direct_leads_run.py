"""One-off: persist direct-contact client leads (no marketplaces)."""
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
from leads.engine.persist import load_store, save_store, upsert_leads
from leads.engine.score import score_lead

today = date.today().isoformat()
crit = SearchCriteria(
    lead_types=["client", "freelance", "contract"],
    technologies=["react", "next.js", "typescript", "node.js"],
    geographies=["Remote", "Europe", "Netherlands", "Germany", "Sweden", "France"],
    workplace=["remote"],
    limit=20,
    freshness_days=60,
    excluded_sources=["upwork", "freelancer", "fiverr"],
    raw_prompt="Direct clients with public email/phone; exclude marketplaces",
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
            verification_method="literal_email_on_official_page",
            date_checked=today,
            notes="Published on official page. Does not prove mailbox accepts mail.",
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
        "company": "Innoworks",
        "title": "Full-Stack Developer (Freelance / project)",
        "url": "https://innoworks.ai/en/careers/full-stack",
        "lead_type": "freelance",
        "desc": (
            "NL AI consultancy hiring freelance/project full-stack: Next.js, React, "
            "TypeScript, PostgreSQL, Supabase, OpenAI/Anthropic. Apply info@innoworks.ai. "
            "Phone +31 85 760 0888 on careers page."
        ),
        "email": "info@innoworks.ai",
        "phone": "+31 85 760 0888",
        "name": None,
        "title_role": "Careers / general",
        "techs": ["next.js", "react", "typescript", "postgresql", "supabase"],
        "salary": "Market rate per project",
        "risks": ["Trial assignment expected", "Reply within a few days"],
        "service": "Freelance Next.js/React SaaS and AI web apps for B2B clients",
    },
    {
        "company": "WeTal Lab AB",
        "title": "Fullstack TypeScript Developer — AI B2B SaaS MVP (3–6 mo)",
        "url": "https://wetal.com/jobs/68eccc890f788c3af6f449b0",
        "lead_type": "contract",
        "desc": (
            "Remote 3–6 month React/TypeScript fullstack MVP contract. Email info@wetal.com. "
            "WeTal is a Swedish consultancy broker that mainly contracts European engineers."
        ),
        "email": "info@wetal.com",
        "phone": None,
        "name": None,
        "title_role": "Hiring contact",
        "techs": ["typescript", "react", "supabase", "firebase"],
        "salary": "Competitive (broker rates from ~29 EUR/h framed on site)",
        "risks": [
            "Broker prefers Central/Eastern Europe — confirm eligibility from Pakistan",
            "Listing dated 2025-10-13 — confirm still open",
        ],
        "service": "Contract React/TypeScript MVP for AI B2B SaaS",
    },
    {
        "company": "nemensis AG",
        "title": "Senior Frontend Developer (React, Next.js, TypeScript) – Freelance",
        "url": "https://www.nemensis.de/jobs-und-projekte/detail/HQzVy-senior-frontend-developer-react-nextjs-typescript-freelance/",
        "lead_type": "freelance",
        "desc": (
            "Freelance senior frontend for energy client. React, Next.js, TypeScript, Nest BFF. "
            "Start 2026-11-02 to 2027-04-30. Contact Shweta.Patil@nemensis.de / +49 40 85537032. "
            "German C1 required."
        ),
        "email": "Shweta.Patil@nemensis.de",
        "phone": "+49 40 85537032",
        "name": "Shweta Patil",
        "title_role": "Recruiter",
        "techs": ["react", "next.js", "typescript", "nest.js", "tailwind"],
        "salary": "Not stated",
        "risks": [
            "German C1 required — likely deal-breaker for current profile",
            "5% onsite Berlin",
        ],
        "service": "Senior React/Next freelance (only if German C1 met)",
    },
    {
        "company": "Lemrock",
        "title": "Engineering hiring (jobs@ + Ashby board)",
        "url": "https://jobs.ashbyhq.com/lemrock",
        "lead_type": "contract",
        "desc": (
            "AI media startup hiring engineers (React/TypeScript). LinkedIn hiring post "
            "published jobs@lemrock.com. Ashby board lists founding full-stack and related roles."
        ),
        "email": "jobs@lemrock.com",
        "phone": None,
        "name": None,
        "title_role": "Hiring",
        "techs": ["react", "typescript", "nestjs"],
        "salary": "Not stated / equity on some FT roles",
        "risks": [
            "Many roles Paris hybrid/onsite",
            "French often required for FT",
            "Confirm freelance vs FT fit before emailing",
        ],
        "service": "React product engineering via jobs@lemrock.com",
    },
    {
        "company": "WordPress Services",
        "title": "Frontend Developer React + Next.js (hiring on hold)",
        "url": "https://wordpress-services.net/frontend-ui-developer/",
        "lead_type": "freelance",
        "desc": (
            "Project-based React+Next.js+TypeScript SaaS PWA role. Page says hiring on hold "
            "but still accepts resumes at hello@wordpress-services.net; phone +63 999 792 2737."
        ),
        "email": "hello@wordpress-services.net",
        "phone": "+63 999 792 2737",
        "name": "Gabriel Mercado",
        "title_role": "Hiring",
        "techs": ["react", "next.js", "typescript"],
        "salary": "Negotiable",
        "risks": ["Hiring on hold", "Philippines-based preferred"],
        "service": "React/Next SaaS UI when hiring reopens",
        "intent_override": "STRONG_SIGNAL",
    },
    {
        "company": "NextEnvision",
        "title": "Delivery Partner Network (React/Next overflow)",
        "url": "https://nextenvision.com/become-a-delivery-partner/",
        "lead_type": "client",
        "desc": (
            "Routes overflow React/Next.js briefs from UK/Australia/Singapore agencies to "
            "vetted delivery partners. Email connect@nextenvision.com with website + portfolio."
        ),
        "email": "connect@nextenvision.com",
        "phone": None,
        "name": None,
        "title_role": "Partner intake",
        "techs": ["react", "next.js", "saas"],
        "salary": "Partner rates not published",
        "risks": ["Partner review gate", "You deliver under their banner, not end-client brand alone"],
        "service": "React/Next delivery partner for agency overflow",
    },
]


def main() -> None:
    leads: list[Lead] = []
    for r in ROWS:
        intent = r.get("intent_override") or "EXPLICIT_DEMAND"
        expl = (
            "Public hiring/partner page with published business email"
            if intent == "EXPLICIT_DEMAND"
            else "Published role but hiring currently on hold"
        )
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
            intent=intent,
            intent_explanation=expl,
            evidence=[
                Evidence(
                    summary=r["desc"][:280],
                    excerpt=r["desc"][:280],
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
            next_action=f"Email {r['email']} with tailored pitch after you approve the draft.",
            status="qualified",
        )
        lead.scores = score_lead(lead, crit)
        lead.outreach = generate_outreach(lead)
        lead.outreach.subject = f"React/Next.js availability for {r['company']}"
        lead.outreach.send_approved = False
        leads.append(lead)

    leads = dedupe_leads(leads)
    leads.sort(
        key=lambda L: (
            0 if L.intent == "EXPLICIT_DEMAND" else 1,
            -(L.scores.overall if L.scores else 0),
        )
    )
    info = upsert_leads(leads, ROOT / "leads" / "store" / "leads_store.json")

    store = load_store()
    for lid, row in list(store.get("leads", {}).items()):
        u = (row.get("url") or "").lower()
        if any(x in u for x in ("upwork.com", "freelancer.com", "zeerk.com")):
            row["status"] = "disqualified"
            note = f"[{today}] Disqualified: user wants direct email/phone clients, not marketplaces."
            row["notes"] = ((row.get("notes") or "") + "\n" + note).strip()
            store["leads"][lid] = row
    save_store(store)

    paths = export_run(
        leads,
        crit,
        source_meta={
            "mode": "direct_contact_only",
            "excluded": ["upwork", "freelancer", "fiverr"],
            "note": "Only leads with publicly published business email and/or phone.",
        },
    )
    print(
        json.dumps(
            {
                "persist": info,
                "export": str(paths["dir"]),
                "leads": [
                    {
                        "id": L.id,
                        "intent": L.intent,
                        "fit": round(L.scores.fit_score, 2),
                        "all": round(L.scores.overall, 2),
                        "company": L.company,
                        "title": L.title,
                        "email": next(
                            c.value for c in L.contacts if c.channel_type == "email"
                        ),
                        "phone": next(
                            (
                                c.value
                                for c in L.contacts
                                if (c.title or "").startswith("Phone")
                            ),
                            None,
                        ),
                        "url": L.url,
                        "risks": L.risks,
                    }
                    for L in leads
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
