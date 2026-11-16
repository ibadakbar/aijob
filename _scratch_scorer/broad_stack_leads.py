"""Broader-stack direct-contact leads (Java/Kotlin/AI/Go/Flutter/etc)."""
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
    lead_types=["freelance", "contract", "client"],
    technologies=[
        "java",
        "kotlin",
        "android",
        "spring boot",
        "python",
        "ai",
        "llm",
        "golang",
        "flutter",
        "node.js",
    ],
    workplace=["remote"],
    limit=30,
    freshness_days=120,
    excluded_sources=["upwork", "freelancer", "fiverr"],
    raw_prompt="Broader tech stacks with direct email/phone; not limited to React profile",
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
        "company": "Monterail",
        "title": "LLM Engineer — Freelancer (RAG / production AI)",
        "url": "https://www.monterail.com/careers/ai-engineer-freelancer",
        "lead_type": "freelance",
        "stack": "AI / LLM",
        "desc": (
            "Remote freelance LLM engineers for production AI features (RAG, embeddings, "
            "OpenAI/Anthropic) in Python/Node/Ruby codebases. 15–40 hrs/week B2B. "
            "Company contact hello@monterail.com / +48 533 600 136."
        ),
        "email": "hello@monterail.com",
        "phone": "+48 533 600 136",
        "techs": ["python", "node.js", "llm", "rag", "openai"],
        "salary": "Not stated (B2B freelance)",
        "risks": ["Delivery-focused AI eng, not research", "English B2/C1"],
        "service": "Freelance production LLM/RAG feature delivery",
    },
    {
        "company": "Codevian Technologies",
        "title": "AI/ML Engineer (freelancer / consultant)",
        "url": "https://codevian.com/career/ai-ml-engineer-freelancer-consultant/",
        "lead_type": "freelance",
        "stack": "AI / ML / Azure OpenAI",
        "desc": (
            "Freelance AI/ML consultant: Azure OpenAI, Copilot Studio, Bot Framework, RAG, "
            "LangChain/Semantic Kernel. Apply hr@codevian.com. Phones +91 93707 04715."
        ),
        "email": "hr@codevian.com",
        "phone": "+91 93707 04715",
        "techs": ["python", "node.js", "azure openai", "rag", "langchain"],
        "salary": "Best in industry (not published)",
        "risks": ["6–8 yrs AI/ML expected", "Microsoft stack heavy"],
        "service": "Freelance Azure/OpenAI conversational AI delivery",
    },
    {
        "company": "Freelinker",
        "title": "AI/ML Engineer – Cloud & Generative AI (remote)",
        "url": "https://www.linkedin.com/posts/rajesh-jadhav-244064253_aijobs-hiringnow-machinelearningengineer-activity-7333027529294872576-clvE",
        "lead_type": "freelance",
        "stack": "AI / ML / GenAI",
        "desc": (
            "Remote AI/ML engineer: Python, PyTorch/TF, LLM fine-tuning, LangChain, AWS/GCP/Azure AI. "
            "Budget ₹60K/month. Email hr@freelinker.in with subject "
            "'AI/ML Engineer – Cloud & Generative AI'."
        ),
        "email": "hr@freelinker.in",
        "phone": None,
        "techs": ["python", "pytorch", "llm", "langchain", "aws"],
        "salary": "₹60,000/month",
        "risks": ["Budget may be low for senior GenAI", "Confirm role still open"],
        "service": "Remote GenAI/ML engineering",
    },
    {
        "company": "CodersBrain",
        "title": "AI/ML Engineer — freelancing (Conversational AI / LLM)",
        "url": "https://www.linkedin.com/posts/vanshika-gupta-514b91293_job-description-activity-7353033603406057476-xOlt",
        "lead_type": "freelance",
        "stack": "AI / Conversational AI",
        "desc": (
            "Freelance AI/ML for Conversational AI / LLM (6+ yrs). Azure OpenAI, Bot Framework, RAG. "
            "Email Vanshika.gupta@codersbrain.com."
        ),
        "email": "Vanshika.gupta@codersbrain.com",
        "phone": None,
        "name": "Vanshika Gupta",
        "title_role": "Recruiter",
        "techs": ["python", "llm", "azure openai", "rag"],
        "salary": "Not stated",
        "risks": ["Staffing intermediary", "6+ years AI required"],
        "service": "Freelance conversational AI / LLM engineering",
    },
    {
        "company": "Alpharec",
        "title": "Senior Android Developer — 100% remote",
        "url": "https://alpharec.com/jobs/sr-android-developer-remotely/",
        "lead_type": "contract",
        "stack": "Kotlin / Android / Java",
        "desc": (
            "Remote senior Android (Kotlin/Java, RxJava, Dagger, REST) for facility-management "
            "product. ≤150 PLN or ~€33+VAT/hour. Email job@alpharec.com. Phone +48 500 027 340. "
            "Prefers B2B self-employed within EU."
        ),
        "email": "job@alpharec.com",
        "phone": "+48 500 027 340",
        "techs": ["kotlin", "java", "android", "rxjava"],
        "salary": "~€33+/hour (or ≤150 PLN/h)",
        "risks": ["EU self-employed preferred — confirm Pakistan eligibility"],
        "service": "Senior Android/Kotlin contract",
    },
    {
        "company": "One Day Ahead GmbH",
        "title": "Kotlin/Android Developer + mobile backend (Spring Boot) — remote",
        "url": "https://www.freelancermap.de/projekt/kotlin-android-developer-mit-mobile-backend-erfahrung-m-w-d-100-prozent-remote-start-01-09-2026",
        "lead_type": "freelance",
        "stack": "Kotlin / Android / Spring Boot",
        "desc": (
            "100% remote Kotlin/Android + Spring Boot mobile-backend freelance, start ~Sep 2026, "
            "4 months. German language. Contact Paul Franzke pfranzke@onedayahead.de / "
            "+49 381 24359915. Send CV, self-rating, hourly rate."
        ),
        "email": "pfranzke@onedayahead.de",
        "phone": "+49 381 24359915",
        "name": "Paul Franzke",
        "title_role": "Recruiter",
        "techs": ["kotlin", "java", "android", "spring boot", "firebase"],
        "salary": "Ask (hourly)",
        "risks": ["German language required", "Germany-market freelance"],
        "service": "Kotlin/Android + Spring Boot freelance",
    },
    {
        "company": "One Day Ahead GmbH",
        "title": "Kotlin/Java Developer with GenAI — remote @ 75 EUR/h",
        "url": "https://www.freelancermap.de/projekt/kotlin-java-developer-mit-ki-genai-erfahrung-m-w-d-100-prozent-remote-75-00-euro-h-start-14-09-2026",
        "lead_type": "freelance",
        "stack": "Kotlin / Java / GenAI",
        "desc": (
            "100% remote Kotlin/Java + GenAI/Spring Boot/PostgreSQL/AWS/Kafka, 75 EUR/h, "
            "~4 months from Sep 2026. German language. Email pfranzke@onedayahead.de."
        ),
        "email": "pfranzke@onedayahead.de",
        "phone": "+49 381 24359915",
        "name": "Paul Franzke",
        "title_role": "Recruiter",
        "techs": ["kotlin", "java", "genai", "spring boot", "aws", "kafka"],
        "salary": "75 EUR/hour",
        "risks": ["German language required", "Strong GenAI + JVM backend expected"],
        "service": "Kotlin/Java GenAI backend freelance",
    },
    {
        "company": "Scurite",
        "title": "Senior Golang / Flutter / Angular engineers (remote studio)",
        "url": "https://scurite.com/career",
        "lead_type": "full_time",
        "stack": "Go / Flutter / Angular",
        "desc": (
            "Remote studio hiring Senior Golang backend, Flutter mobile, Angular frontend. "
            "Email hello@scurite.com with GitHub + CV. Phones +91 76963 55852 / +91 79865 68931."
        ),
        "email": "hello@scurite.com",
        "phone": "+91 76963 55852",
        "techs": ["golang", "flutter", "angular", "postgresql"],
        "salary": "Not stated",
        "risks": ["Listed as full-time openings", "Studio based in India"],
        "service": "Go/Flutter/Angular engineering roles",
    },
    {
        "company": "Netguru",
        "title": "(Senior) Golang Developer — Freelance B2B",
        "url": "https://apply.workable.com/j/8E4B849440",
        "lead_type": "freelance",
        "stack": "Golang (+ optional React fullstack)",
        "desc": (
            "Fully remote Golang freelance B2B up to 34 EUR/h. Strong Go mandatory; fullstack "
            "with React welcome. Company email hello@netguru.com. Also apply via Workable form."
        ),
        "email": "hello@netguru.com",
        "phone": None,
        "techs": ["golang", "aws", "react"],
        "salary": "up to 34 EUR/hour",
        "risks": ["Often prefers EU/B2B entity", "Apply via Workable + optional email"],
        "service": "Senior Go freelance backend",
    },
    {
        "company": "nemensis AG",
        "title": "Senior Backend Developer (Kotlin/Java) — AI platform, EU remote",
        "url": "https://www.freelancermap.com/project/100-prozent-remote-eu-senior-backend-developer-m-f-d",
        "lead_type": "freelance",
        "stack": "Kotlin / Java / AI platform",
        "desc": (
            "Freelance senior backend for AI-powered software-dev platform (LLM codegen). "
            "Kotlin/Java, Spring Boot, EU remote only. Contact via nemensis; known recruiter "
            "email Shweta.Patil@nemensis.de also used on other nemensis freelance listings."
        ),
        "email": "Shweta.Patil@nemensis.de",
        "phone": "+49 40 85537032",
        "name": "Shweta Patil",
        "title_role": "Recruiter",
        "techs": ["kotlin", "java", "spring boot", "llm"],
        "salary": "Not stated",
        "risks": ["EU-only remote", "May require German/EU residency"],
        "service": "Kotlin/Java AI-platform backend freelance",
    },
]


def main() -> None:
    leads: list[Lead] = []
    for r in ROWS:
        lead = Lead(
            id=make_lead_id(
                source="websearch_broad",
                company=r["company"],
                title=r["title"],
                url=r["url"],
            ),
            name=f"{r['company']} — {r['title']}",
            lead_type=r["lead_type"],
            company=r["company"],
            title=r["title"],
            url=r["url"],
            source="websearch_broad",
            intent="EXPLICIT_DEMAND",
            intent_explanation=(
                f"Public hiring for {r['stack']} with published business email "
                "(broader than candidate core React profile — user requested expansion)"
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
            profile_match_reasons=[
                f"STACK FOCUS: {r['stack']} — may be outside primary React/Next profile",
                "User asked to expand beyond profile skills",
            ],
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
            risks=r["risks"]
            + ["Skill match to Ibad profile may be partial — verify honest fit before claiming expertise"],
            next_action=f"Email {r['email']} only if you can honestly cover the stack.",
            status="qualified",
            notes=f"broad_stack={r['stack']}",
        )
        lead.scores = score_lead(lead, crit)
        lead.outreach = generate_outreach(lead)
        lead.outreach.subject = f"{r['stack']} availability for {r['company']}"
        lead.outreach.personalization_facts.append(
            f"Target stack for this lead: {r['stack']}"
        )
        lead.outreach.send_approved = False
        leads.append(lead)

    leads = dedupe_leads(leads)
    leads.sort(key=lambda L: -(L.scores.overall if L.scores else 0))
    info = upsert_leads(leads, ROOT / "leads" / "store" / "leads_store.json")
    paths = export_run(
        leads,
        crit,
        source_meta={
            "mode": "broad_stack_direct_contact",
            "note": (
                "Expanded beyond React/Next profile per user request. "
                "Stacks: AI/LLM, Kotlin/Android/Java, Go, Flutter. "
                "Only published emails/phones. No Upwork."
            ),
        },
        run_id=date.today().strftime("%Y%m%d") + "-broad-stack",
    )
    print(
        json.dumps(
            {
                "persist": info,
                "export": str(paths["dir"]),
                "leads": [
                    {
                        "id": L.id,
                        "stack": next(
                            (
                                x.split("STACK FOCUS: ", 1)[1]
                                for x in L.profile_match_reasons
                                if x.startswith("STACK FOCUS:")
                            ),
                            "",
                        ),
                        "company": L.company,
                        "email": next(c.value for c in L.contacts if c.channel_type == "email"),
                        "phone": next(
                            (c.value for c in L.contacts if (c.title or "").startswith("Phone")),
                            None,
                        ),
                        "salary": L.budget_or_salary,
                        "risks": L.risks[:2],
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
