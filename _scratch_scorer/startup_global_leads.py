"""Global startup tech hiring leads with published email/phone only."""
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
    lead_types=["client", "freelance", "contract", "full_time"],
    technologies=["react", "next.js", "typescript", "node.js", "full-stack", "javascript"],
    industries=["startup"],
    workplace=["remote"],
    limit=25,
    freshness_days=90,
    excluded_sources=["upwork", "freelancer", "fiverr"],
    raw_prompt=(
        "Global startups hiring tech talent with authentic published email/phone"
    ),
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
        "company": "SpaceCapture",
        "title": "Full-Stack Developer (Next.js / React)",
        "url": "https://spacecapture.ai/careers/full-stack-developer",
        "lead_type": "full_time",
        "desc": (
            "AI field-inspection startup hiring remote Full-Stack (Next.js/React/TypeScript). "
            "Apply contact@spacecapture.ai. Published phones: USA +1 646 421 5740, "
            "UAE +971 56 256 7509, and others on careers page."
        ),
        "email": "contact@spacecapture.ai",
        "phone": "+1 646 421 5740",
        "techs": ["next.js", "react", "typescript", "rest"],
        "salary": "Not stated",
        "location": "Remote worldwide",
        "risks": ["Posted as fresher-friendly; confirm senior band", "Verify salary before commit"],
        "service": "Full-stack Next.js/React product engineering",
        "fit_note": "Strong stack match (React/Next/TS dashboards)",
    },
    {
        "company": "WeBuildCrew",
        "title": "Senior Full-Stack Developer",
        "url": "https://webuildcrew.com/careers",
        "lead_type": "full_time",
        "desc": (
            "Remote-first agency/startup crew (Pakistan/UAE/Europe) hiring Senior Full-Stack "
            "(Next.js, Node, TypeScript, PostgreSQL). Email webuildcrew@gmail.com. "
            "Phone +92 308 2769473 published on careers page."
        ),
        "email": "webuildcrew@gmail.com",
        "phone": "+92 308 2769473",
        "techs": ["next.js", "node.js", "typescript", "postgresql"],
        "salary": "USD rates (not published)",
        "location": "Remote (PK / UAE / EU team)",
        "risks": ["Gmail apply address", "Agency client work vs product company"],
        "service": "Senior full-stack SaaS/marketplace delivery",
        "fit_note": "Strong stack + Pakistan-friendly remote",
    },
    {
        "company": "iReadCustomer",
        "title": "Full-Stack Developer (AI-Driven)",
        "url": "https://ireadcustomer.com/en/career/full-stack-developer-ai-driven",
        "lead_type": "full_time",
        "desc": (
            "SEA DataTech/AI software house hiring remote AI-driven Full-Stack "
            "(TypeScript, Next.js, Node, Prisma, MongoDB, LangChain). "
            "hr@ireadcustomer.com; phones 085-990-8320 and +66 92 939 9442 on page."
        ),
        "email": "hr@ireadcustomer.com",
        "phone": "+66 92 939 9442",
        "techs": ["typescript", "next.js", "node.js", "mongodb", "langchain"],
        "salary": "Up to ~50,000+ THB/month + project bonus",
        "location": "Remote WFH (SEA company)",
        "risks": ["THB compensation band may be low vs EU/US", "Client-delivery pace"],
        "service": "AI-driven full-stack client product delivery",
        "fit_note": "Next/Node match; AI tooling adjacent to Plai/SaaS work",
    },
    {
        "company": "AMK Solutions",
        "title": "Senior Full-Stack Engineer (Node.js + Next.js)",
        "url": "https://amk.solutions/job/fullstack-developer",
        "lead_type": "full_time",
        "desc": (
            "AI consulting for ed-tech hiring Senior Full-Stack (Node/Express/TS + Next/React). "
            "Remote; US business hours. Apply hr@amk.solutions. No phone on official contact page."
        ),
        "email": "hr@amk.solutions",
        "phone": None,
        "techs": ["node.js", "next.js", "react", "typescript", "mongodb"],
        "salary": "Competitive (not published)",
        "location": "Remote (US hours)",
        "risks": ["Must cover US hours from PK", "No published phone"],
        "service": "Senior full-stack ed-tech AI platforms",
        "fit_note": "Excellent stack match (5+ yrs framing fits)",
    },
    {
        "company": "Owlery",
        "title": "Full Stack Engineer (remote)",
        "url": "https://owlery.ai/careers/full-stack-engineer-remote",
        "lead_type": "full_time",
        "desc": (
            "Seed-stage Silicon Valley AI logistics/TMS startup. Stack TypeScript/Next.js/"
            "Node/MongoDB. Apply careers@owlery.ai. No reliable company phone on careers page."
        ),
        "email": "careers@owlery.ai",
        "phone": None,
        "techs": ["typescript", "next.js", "node.js", "mongodb", "ai agents"],
        "salary": "Not stated",
        "location": "Remote (HQ Silicon Valley)",
        "risks": ["Early-stage; possible US-hour bias", "No published phone"],
        "service": "Full-stack AI product engineering",
        "fit_note": "Strong Next/TS/Node match; logistics AI product",
    },
    {
        "company": "KeyCandle",
        "title": "Frontend Developer (React/Next.js)",
        "url": "https://keycandle.com/careers",
        "lead_type": "full_time",
        "desc": (
            "Remote crypto trading startup hiring Frontend (React/Next/TS) $60–90k and "
            "Senior Backend (Node/TS). careers@keycandle.com published on careers page."
        ),
        "email": "careers@keycandle.com",
        "phone": None,
        "techs": ["react", "next.js", "typescript", "websocket"],
        "salary": "$60–90k frontend / $80–120k backend",
        "location": "100% remote worldwide",
        "risks": ["Crypto/trading domain", "No published phone"],
        "service": "Frontend React/Next trading UI",
        "fit_note": "Strong frontend React/Next match",
    },
    {
        "company": "PingAura AI",
        "title": "Frontend Engineer",
        "url": "https://www.pingaura.ai/careers/frontend-engineer",
        "lead_type": "full_time",
        "desc": (
            "Pre-seed AI visibility startup (Google for Startups / AWS backed). "
            "Frontend Engineer Next.js 16 / React 19 / TS dashboards. "
            "Apply careers@pingaura.ai. Job posting lists India applicant location."
        ),
        "email": "careers@pingaura.ai",
        "phone": None,
        "techs": ["next.js", "react", "typescript", "supabase", "tailwind"],
        "salary": "India early-stage band (not published)",
        "location": "Remote / Mumbai preference (India)",
        "risks": ["India location preference may block PK", "No published phone"],
        "service": "Frontend AI dashboard engineering",
        "fit_note": "Dashboard/analytics UI close to Plai experience",
    },
    {
        "company": "Primefold",
        "title": "Product Engineer (full-stack)",
        "url": "https://www.linkedin.com/posts/primefold_exciting-times-at-primefold-we-are-hiring-activity-7475110522569330688-HdwD",
        "lead_type": "full_time",
        "desc": (
            "AI-native platform hiring remote Product Engineer (TypeScript, React, Next.js, "
            "Node, Postgres). Public LinkedIn post: work@primefold.ai."
        ),
        "email": "work@primefold.ai",
        "phone": None,
        "techs": ["typescript", "react", "next.js", "node.js", "postgres"],
        "salary": "Not stated",
        "location": "Remote full-time",
        "risks": ["LinkedIn post age — confirm still open", "No published phone"],
        "service": "Product engineering end-to-end",
        "fit_note": "Full-stack TS/React/Next/Node match",
    },
    {
        "company": "Start Spark",
        "title": "Full-Stack / All-Rounder Developer (FT / Freelance / Contract)",
        "url": "https://www.linkedin.com/posts/prathamaroraceo_jd-activity-7505962032664350721-Upum",
        "lead_type": "contract",
        "desc": (
            "Startup hiring versatile full-stack for AI+IoT+fleet product. Engagement FT/"
            "freelance/contract, remote. Apply hr.startspark@gmail.com (LinkedIn hiring post)."
        ),
        "email": "hr.startspark@gmail.com",
        "phone": None,
        "techs": ["react", "next.js", "flutter", "aws", "postgresql", "webrtc"],
        "salary": "Ask (not published)",
        "location": "Remote / flexible",
        "risks": ["Gmail HR address", "Broad stack incl. Flutter/IoT", "No phone"],
        "service": "Contract/freelance full-stack product build",
        "fit_note": "React/Next + streaming/WebRTC adjacent to your projects",
    },
    {
        "company": "Kathi Tech Labs",
        "title": "Freelance Developers (MERN / RN / AI)",
        "url": "https://www.linkedin.com/posts/huzaifakathi_hiring-freelancedeveloper-freelancer-activity-7504131531024777216-2Js5",
        "lead_type": "freelance",
        "desc": (
            "KTL expanding freelance network: React Native, MERN, Flutter, AI, DevOps. "
            "Send CV/portfolio to info@kathitechlabs.com (LinkedIn post)."
        ),
        "email": "info@kathitechlabs.com",
        "phone": None,
        "techs": ["react", "mern", "react native", "node.js"],
        "salary": "Project-based",
        "location": "Remote freelance",
        "risks": ["Network/bench style — qualify each project", "No phone on post"],
        "service": "Freelance MERN/RN project delivery",
        "fit_note": "MERN/React Native matches profile",
    },
    {
        "company": "Elegantay",
        "title": "Frontend React Developer (Remote / Freelance)",
        "url": "https://www.linkedin.com/posts/elegantay_frontend-react-developer-wanted-remote-activity-7366568368033644544-xybc",
        "lead_type": "freelance",
        "desc": (
            "UK/PK-linked team hiring React/Vite freelance for AI platforms (4–6 weeks, "
            "possible ongoing). Apply franchisengineai@gmail.com."
        ),
        "email": "franchisengineai@gmail.com",
        "phone": None,
        "techs": ["react", "vite", "supabase", "openai"],
        "salary": "Monthly or fixed fee",
        "location": "Remote freelance",
        "risks": ["Post may be older", "Gmail apply", "Short contract"],
        "service": "Freelance React UI for AI prototypes",
        "fit_note": "React + API/Supabase fit",
    },
    {
        "company": "Squoosh.AI",
        "title": "Full-Stack Engineer (remote)",
        "url": "https://hnhiring.fyi/job/613243",
        "lead_type": "full_time",
        "desc": (
            "HN Jobs: Squoosh.AI Full-Stack Engineer remote US — React/Next/TS/Python/"
            "Postgres. Apply tyler@squoosh.ai subject 'HN — Full Stack'. "
            "$90k–150k. US work auth noted on PhD track; verify FT engineer geo rules."
        ),
        "email": "tyler@squoosh.ai",
        "phone": None,
        "techs": ["react", "next.js", "typescript", "python", "postgresql"],
        "salary": "$90k–150k USD/year",
        "location": "Remote (US notes on listing)",
        "risks": ["Confirm work-authorization requirements", "No phone"],
        "service": "Full-stack AI product engineering",
        "fit_note": "React/Next/TS core match",
    },
]


def main() -> None:
    leads: list[Lead] = []
    for r in ROWS:
        lead = Lead(
            id=make_lead_id(
                source="websearch_startup",
                company=r["company"],
                title=r["title"],
                url=r["url"],
            ),
            name=f"{r['company']} — {r['title']}",
            lead_type=r["lead_type"],
            company=r["company"],
            title=r["title"],
            url=r["url"],
            source="websearch_startup",
            intent="EXPLICIT_DEMAND",
            intent_explanation=(
                "Public startup/agency hiring post with literally published apply email"
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
            profile_match_reasons=[r["fit_note"]],
            recommended_service=r["service"],
            contacts=contacts(
                r["email"],
                r["url"],
                phone=r.get("phone"),
            ),
            budget_or_salary=r["salary"],
            location=r["location"],
            workplace="remote",
            checked_date=today,
            risks=r["risks"],
            next_action=f"Email {r['email']} with CV + portfolio; phone only if published.",
            status="qualified",
            notes="startup_global_authentic_contact",
        )
        lead.scores = score_lead(lead, crit)
        lead.outreach = generate_outreach(lead)
        lead.outreach.subject = f"Application — {r['title']} at {r['company']}"
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
            "mode": "startup_global_authentic_contacts",
            "apis": "remotive+arbeitnow also run separately (20261027-142555)",
            "note": (
                "Only leads with literally published emails. Phones included only when "
                "printed on official careers/contact pages. No invented addresses. "
                "No Upwork/Freelancer."
            ),
        },
        run_id=date.today().strftime("%Y%m%d") + "-startup-global",
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
                        "title": L.title,
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
                        "fit": L.scores.fit_score if L.scores else None,
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
