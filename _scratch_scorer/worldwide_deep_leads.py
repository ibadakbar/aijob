"""Deep worldwide authentic-contact developer hiring leads (multi-platform)."""
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
    lead_types=["freelance", "contract", "full_time", "client"],
    technologies=["react", "next.js", "typescript", "node.js", "full-stack", "javascript"],
    workplace=["remote"],
    limit=30,
    freshness_days=120,
    excluded_sources=["upwork", "freelancer", "fiverr"],
    raw_prompt="Deep worldwide authentic developer hiring with published email/phone",
)


def contacts(email: str, url: str, *, phone=None, name=None, title=None):
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
            notes="Published publicly. Mailbox existence not proven.",
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
        "company": "VyrroTech",
        "title": "Senior Full-Stack Engineer",
        "url": "https://vyrrotech.com/careers/senior-full-stack-engineer",
        "platform": "Company careers (UAE/UK)",
        "lead_type": "full_time",
        "region": "UAE / UK / remote-hybrid",
        "desc": (
            "Sharjah UAE agency/product delivery studio hiring Senior FS "
            "(TS, React/Next, Node, PostgreSQL). Markets US/UK/UAE/KSA. "
            "hello@vyrrotech.com; UAE +971 58 570 7287; UK +44 7368 408232."
        ),
        "email": "hello@vyrrotech.com",
        "phone": "+971 58 570 7287",
        "techs": ["typescript", "react", "next.js", "node.js", "postgresql"],
        "salary": "Not stated",
        "risks": ["Remote-hybrid wording — confirm fully remote from PK"],
        "fit": "Excellent stack + mentoring matches profile",
    },
    {
        "company": "NETREX",
        "title": "Full Stack Developer (actively hiring)",
        "url": "https://www.netrexinc.com/careers",
        "platform": "Company careers (UAE multi-geo)",
        "lead_type": "full_time",
        "region": "Dubai / Remote",
        "desc": (
            "NETREX careers lists Full Stack Developer Actively Hiring "
            "(Dubai/Remote, 3–6 yrs, posted Jul 2026). Contact "
            "info@netrexinc.com / +971 50 200 8313 on careers header."
        ),
        "email": "info@netrexinc.com",
        "phone": "+971 50 200 8313",
        "techs": ["full-stack", "javascript", "react"],
        "salary": "Not stated",
        "risks": ["Role detail page may use form — use published info@ first", "Confirm stack depth"],
        "fit": "UAE remote FS opening with phone+email",
    },
    {
        "company": "8Byte Digital",
        "title": "Full-Stack Entwickler (React/Next/TS)",
        "url": "https://8byte.de/jobs/",
        "platform": "Company careers (Germany)",
        "lead_type": "full_time",
        "region": "Germany remote/hybrid",
        "desc": (
            "German web agency hiring Full-Stack (React, Next.js, TypeScript, PHP/Node) "
            "remote/hybrid ASAP. hallo@8byte.de; phone +49 2592 9786601."
        ),
        "email": "hallo@8byte.de",
        "phone": "+49 2592 9786601",
        "techs": ["react", "next.js", "typescript", "node.js"],
        "salary": "Not stated",
        "risks": ["German company — English OK on page but hybrid may prefer EU", "PHP optional"],
        "fit": "Core React/Next/TS match; agentic coding encouraged",
    },
    {
        "company": "EaseControl / Andymen",
        "title": "Full-Stack Developer (Node.js + React) FT/Freelance",
        "url": "https://www.easecontrol.de/karriere",
        "platform": "Company careers (Germany ERP startup)",
        "lead_type": "freelance",
        "region": "Germany remote or Bad Nauheim",
        "desc": (
            "German ERP-for-trades startup hiring Full-Stack Node+React "
            "20–40h/week FT or freelance; also React PWA frontend. "
            "jobs@easecontrol.de on careers page."
        ),
        "email": "jobs@easecontrol.de",
        "phone": None,
        "techs": ["node.js", "react", "postgresql", "express"],
        "salary": "Not stated (hours negotiable)",
        "risks": ["German product/context", "No phone on careers page"],
        "fit": "Strong React/Node; freelance option good for PK",
    },
    {
        "company": "entrecode",
        "title": "Senior Frontend (React/TS) / Backend Node",
        "url": "https://entrecode.de/jobs",
        "platform": "Company careers (Germany)",
        "lead_type": "full_time",
        "region": "Stuttgart / Remote",
        "desc": (
            "Stuttgart software firm: Senior Frontend React/TypeScript and "
            "Backend Node.js/Cloud remote/office. jobs@entrecode.de."
        ),
        "email": "jobs@entrecode.de",
        "phone": None,
        "techs": ["react", "typescript", "node.js"],
        "salary": "Not stated",
        "risks": ["May prefer DE/EU for employment", "No phone listed"],
        "fit": "Senior React/TS frontend strong match",
    },
    {
        "company": "Numbered Agency",
        "title": "Full Stack Developer (React/Next + Shopify)",
        "url": "https://numbered.com/career/full-stack-developer",
        "platform": "Company careers (NL/FR)",
        "lead_type": "full_time",
        "region": "Remote Lyon FR / Amsterdam NL",
        "desc": (
            "Creative studio hiring Full Stack for React/Next/TS + Shopify Plus "
            "headless e-commerce. jobs@numbered.com subject Full Stack / Shopify Developer."
        ),
        "email": "jobs@numbered.com",
        "phone": None,
        "techs": ["react", "next.js", "typescript", "shopify"],
        "salary": "Based on experience",
        "risks": ["EU remote preference possible", "Shopify depth needed", "No phone"],
        "fit": "Shopify on profile secondary skills — strong differentiator",
    },
    {
        "company": "Babou",
        "title": "Agent-Native Software Engineer",
        "url": "https://babou.ai/careers",
        "platform": "Company careers + HN Who's Hiring",
        "lead_type": "full_time",
        "region": "Remote worldwide",
        "desc": (
            "Product startup: TypeScript/Next/Node/Postgres + AI agents. "
            "Hiring anywhere. careers@babou.ai (also posted on HN June 2026)."
        ),
        "email": "careers@babou.ai",
        "phone": None,
        "techs": ["typescript", "next.js", "node.js", "postgresql", "ai agents"],
        "salary": "Not stated",
        "risks": ["High bar on agent-native shipping", "No phone"],
        "fit": "Claude Code / agent workflow aligns with your tooling",
    },
    {
        "company": "Pango",
        "title": "Senior Full Stack / Tech Lead",
        "url": "https://news.ycombinator.com/item?id=48458096",
        "platform": "Hacker News Who's Hiring",
        "lead_type": "full_time",
        "region": "Remote LATAM stated (Stockholm core)",
        "desc": (
            "HN June 2026: Agentic OS for e-commerce logistics. React/JS or "
            "PHP/Laravel; Shopify plus. Apply steve@pango.ai."
        ),
        "email": "steve@pango.ai",
        "phone": None,
        "name": "Steve Rahimi",
        "techs": ["react", "javascript", "shopify", "php"],
        "salary": "Not stated",
        "risks": ["LATAM remote preference may exclude PK", "Post ~4 months old — confirm open"],
        "fit": "Shopify/e-com plus React; verify geography first",
    },
    {
        "company": "Xleron",
        "title": "Full Stack Developer (Next.js / Nest)",
        "url": "https://jobseeker.lk/full-stack-developer-17/",
        "platform": "Jobseeker.lk + company contact",
        "lead_type": "full_time",
        "region": "Remote (Sri Lanka company)",
        "desc": (
            "Remote Full Stack: Next.js, React, TS, Nest.js, Postgres/Drizzle. "
            "careers@xleron.io. Company contact also lists +94 743 640 884 / hello@xleron.io."
        ),
        "email": "careers@xleron.io",
        "phone": "+94 743 640 884",
        "techs": ["next.js", "react", "typescript", "nestjs", "postgresql"],
        "salary": "Not stated",
        "risks": ["Board deadline Aug 2026 — confirm still open", "Nest.js depth"],
        "fit": "Next/React/TS core; Nest learnable from Node",
    },
    {
        "company": "BR7 Technologies",
        "title": "Senior Full-Stack Engineer",
        "url": "https://br7tech.dev/careers/senior-full-stack-engineer",
        "platform": "Company careers (Pakistan)",
        "lead_type": "full_time",
        "region": "Remote Pakistan GMT+5",
        "desc": (
            "PK remote Senior FS Next.js/TS/Node/tRPC/Postgres/AWS. "
            "Form on careers; company publishes hello@br7tech.dev for contact."
        ),
        "email": "hello@br7tech.dev",
        "phone": None,
        "techs": ["next.js", "typescript", "node.js", "postgresql", "trpc"],
        "salary": "Not stated",
        "risks": ["Prefer form apply; email is general hello@", "No phone"],
        "fit": "Timezone-perfect; stack match; Pakistan-based",
    },
    {
        "company": "PrithviTek",
        "title": "Senior Full-Stack Engineer (Next.js & TypeScript)",
        "url": "https://www.linkedin.com/posts/nirvi-k-a6838518_hello-all-interested-candidates-please-activity-7480125856808558593-nPwH",
        "platform": "LinkedIn public hiring post",
        "lead_type": "full_time",
        "region": "100% Remote",
        "desc": (
            "Public LinkedIn JD: Senior FS Next.js/React19/TS/Prisma/Redis/AWS "
            "pricing intelligence product. recruit@prithvitek.com."
        ),
        "email": "recruit@prithvitek.com",
        "phone": None,
        "techs": ["next.js", "react", "typescript", "prisma", "postgresql", "aws"],
        "salary": "Not stated",
        "risks": ["6+ yrs frontend asked", "Staffing firm intermediary", "No phone"],
        "fit": "Strong Next/TS full-stack; senior bar high",
    },
    {
        "company": "UpSunday",
        "title": "Frontend Developer, Next.js (project-based)",
        "url": "https://wellfound.com/jobs/4772699-video-editor-remote-project-based-clone",
        "platform": "Wellfound",
        "lead_type": "freelance",
        "region": "Remote everywhere",
        "desc": (
            "Wellfound: project-based Next.js/TS/Tailwind/GSAP/Vercel frontend. "
            "Apply project@upsunday.co with live sites. Claude Code mentioned as plus."
        ),
        "email": "project@upsunday.co",
        "phone": None,
        "techs": ["next.js", "typescript", "tailwind", "gsap"],
        "salary": "Paid per project",
        "risks": ["Wellfound URL slug odd — verify listing", "Animation-heavy", "No phone"],
        "fit": "Next/TS frontend freelance; Claude Code bonus",
    },
    {
        "company": "Gumb AG",
        "title": "Freelance Next.js Developer (marketing site)",
        "url": "https://wellfound.com/jobs/4589412-freelance-next-js-developer-marketing-site-landing-pages",
        "platform": "Wellfound (Switzerland SaaS)",
        "lead_type": "freelance",
        "region": "Remote India or Pakistan",
        "desc": (
            "Swiss SaaS Gumb hiring freelance Next.js for marketing site. "
            "Explicitly hires India/Pakistan. $6–7/hr via Wellfound terms — rate risk."
        ),
        "email": None,  # Wellfound apply — need application_page only if no email
        "phone": None,
        "techs": ["next.js", "react", "typescript"],
        "salary": "$6–7/hour (low)",
        "risks": [
            "Very low rate",
            "Camera-on Discord requirement",
            "No email — Wellfound application only",
        ],
        "fit": "PK-eligible Next.js freelance but compensation weak",
        "skip_no_email": True,
    },
]


def main() -> None:
    leads: list[Lead] = []
    for r in ROWS:
        if r.get("skip_no_email") or not r.get("email"):
            continue
        lead = Lead(
            id=make_lead_id(
                source="websearch_worldwide",
                company=r["company"],
                title=r["title"],
                url=r["url"],
            ),
            name=f"{r['company']} — {r['title']}",
            lead_type=r["lead_type"],
            company=r["company"],
            title=r["title"],
            url=r["url"],
            source="websearch_worldwide",
            intent="EXPLICIT_DEMAND",
            intent_explanation=(
                f"Public hiring on {r['platform']} with published apply email"
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
            profile_match_reasons=[r["fit"], f"Region: {r['region']}", f"Platform: {r['platform']}"],
            recommended_service=r["title"],
            contacts=contacts(
                r["email"],
                r["url"],
                phone=r.get("phone"),
                name=r.get("name"),
            ),
            budget_or_salary=r["salary"],
            location=r["region"],
            workplace="remote",
            checked_date=today,
            risks=r["risks"],
            next_action=f"Email {r['email']} with CV + portfolio links.",
            status="qualified",
            notes=f"platform={r['platform']}; region={r['region']}",
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
            "mode": "worldwide_deep_multi_platform",
            "platforms": [
                "company_careers",
                "HN_whos_hiring",
                "Wellfound",
                "LinkedIn_public_posts",
                "Jobseeker.lk",
                "Remotive",
                "Arbeitnow",
            ],
            "skipped": [
                "20byte (Indonesia citizen only)",
                "Taqweed (Arabic required — dealbreaker)",
                "Gumb (no published email; $6-7/hr)",
                "Mentblue (site mismatch / unreliable)",
            ],
            "api_export": "leads/exports/20261027-154932",
            "note": "Only literally published emails/phones. No Upwork.",
        },
        run_id=date.today().strftime("%Y%m%d") + "-worldwide-deep",
    )
    print(
        json.dumps(
            {
                "persist": info,
                "export": str(paths["dir"]),
                "count": len(leads),
                "leads": [
                    {
                        "id": L.id,
                        "company": L.company,
                        "region": L.location,
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
