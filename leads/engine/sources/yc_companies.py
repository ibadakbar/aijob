"""Y Combinator company directory → startup leads + published founder contacts.

Uses YC's public directory search (Algolia, search-only secured key from the
companies page) with a yc-oss.github.io fallback. Founder names and LinkedIn
URLs are taken only when they literally appear on the public YC company page.

Never invents co-founder emails. YC's ``has_email`` flag means Bookface may
have a mailbox — it is **not** a published address and must not be stored as one.
"""

from __future__ import annotations

import html as html_lib
import json
import random
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from typing import Any, Optional

from job_scraper.engine.http import UA, fetch_json
from job_scraper.engine.normalize import detect_country, detect_workplace

from ..contacts import build_contacts_from_listing, extract_published_emails
from ..dedupe import make_lead_id
from ..intent import classify_intent
from ..model import ContactChannel, Evidence, Lead, LeadType, SearchCriteria
from ..sanitize import safe_excerpt, sanitize_text
from .base import FetchResult, LeadSourceAdapter, SourceMeta

ALGOLIA_APP = "45BWZJ1SGC"
ALGOLIA_INDEX = "YCCompany_production"
ALGOLIA_URL = f"https://{ALGOLIA_APP.lower()}-dsn.algolia.net/1/indexes/{ALGOLIA_INDEX}/query"
YC_DIRECTORY = "https://www.ycombinator.com/companies"
YC_OSS_HIRING = "https://yc-oss.github.io/api/companies/hiring.json"
YC_OSS_ALL = "https://yc-oss.github.io/api/companies/all.json"

_STACK_RE = re.compile(
    r"(?i)\b(react(?:\.?js)?|next\.?js|typescript|javascript|node\.?js|full[-\s]?stack|"
    r"frontend|front-end|saas|b2b|api|dashboard|ai|llm|software|developer|"
    r"web app|platform)\b"
)

_ALGOLIA_OPTS_RE = re.compile(r"AlgoliaOpts\s*=\s*(\{.*?\});", re.S)
_FOUNDERS_KEY_RE = re.compile(r'"founders"\s*:\s*(\[)')


def _http_get(url: str, *, timeout: float = 30.0) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": UA, "Accept": "text/html,application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "replace")


def _http_post_json(url: str, body: dict[str, Any], *, headers: dict[str, str]) -> Any:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"User-Agent": UA, "Content-Type": "application/json", **headers},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_algolia_secured_key() -> str:
    """Read the public search-only secured API key from YC's companies page."""
    page = _http_get(YC_DIRECTORY)
    match = _ALGOLIA_OPTS_RE.search(page)
    if not match:
        raise RuntimeError("ycombinator: AlgoliaOpts not found on companies page")
    opts = json.loads(match.group(1))
    key = (opts.get("key") or "").strip()
    if not key:
        raise RuntimeError("ycombinator: empty Algolia key")
    return key


def parse_founders_json(page_html: str) -> list[dict[str, Any]]:
    """Extract the ``founders`` array embedded in a YC company HTML page."""
    text = html_lib.unescape(page_html)
    match = _FOUNDERS_KEY_RE.search(text)
    if not match:
        return []
    start = match.start(1)
    depth = 0
    end = start
    for i, ch in enumerate(text[start:], start):
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    try:
        data = json.loads(text[start:end])
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def linkedin_people_search(name: str, company: str) -> str:
    q = urllib.parse.quote(f"{name} {company}".strip())
    return (
        "https://www.linkedin.com/search/results/people/"
        f"?keywords={q}&origin=GLOBAL_SEARCH_HEADER"
    )


def _stack_blob(row: dict[str, Any]) -> str:
    tags = row.get("tags") or []
    industries = row.get("industries") or []
    return " ".join(
        [
            str(row.get("name") or ""),
            str(row.get("one_liner") or ""),
            str(row.get("long_description") or ""),
            str(row.get("industry") or ""),
            str(row.get("subindustry") or ""),
            " ".join(str(t) for t in tags),
            " ".join(str(t) for t in industries),
        ]
    )


def _matches_stack(blob: str, technologies: list[str]) -> bool:
    lower = blob.lower()
    if technologies:
        for tech in technologies:
            t = tech.lower().strip()
            if not t:
                continue
            if t in lower or t.replace(".", "") in lower.replace(".", ""):
                return True
        # Soft: general software/SaaS still useful for founder outreach
        if _STACK_RE.search(blob):
            return True
        return False
    return bool(_STACK_RE.search(blob))


def _geo_ok(row: dict[str, Any], geographies: list[str]) -> bool:
    if not geographies:
        return True
    regions = " ".join(str(r) for r in (row.get("regions") or [])).lower()
    loc = str(row.get("all_locations") or "").lower()
    blob = f"{regions} {loc}"
    for geo in geographies:
        g = geo.lower()
        if g in ("remote", "worldwide", "global"):
            if "remote" in blob or "america" in blob or "europe" in blob or "uk" in blob:
                return True
            continue
        aliases = {
            "united states": ("united states", "usa", "america / canada", "us"),
            "united kingdom": ("united kingdom", "uk", "europe"),
            "canada": ("canada", "america / canada"),
            "australia": ("australia", "oceania"),
            "new zealand": ("new zealand", "oceania"),
            "germany": ("germany", "europe"),
            "europe": ("europe",),
            "uae": ("middle east", "uae", "united arab"),
        }
        needles = aliases.get(g, (g,))
        if any(n in blob for n in needles):
            return True
    # Remote-friendly YC rows often omit geo — keep them
    if "remote" in blob or not (row.get("all_locations") or "").strip():
        return True
    return False


class YCCompaniesSource(LeadSourceAdapter):
    meta = SourceMeta(
        name="ycombinator",
        official_api=False,
        notes=(
            "YC public company directory (Algolia search-only key from ycombinator.com/companies) "
            "with yc-oss.github.io JSON fallback. Founder names/LinkedIn from public company pages. "
            "Does not expose private founder emails."
        ),
    )

    def fetch(self, criteria: SearchCriteria, **kwargs: Any) -> FetchResult:
        if "ycombinator" in {s.lower() for s in criteria.excluded_sources} or "yc" in {
            s.lower() for s in criteria.excluded_sources
        }:
            return FetchResult(meta={"skipped": "excluded_sources"})

        enrich_founders = bool(kwargs.get("enrich_founders", True))
        enrich_site_email = bool(kwargs.get("enrich_site_email", True))
        hiring_only = bool(
            kwargs.get(
                "hiring_only",
                re.search(r"(?i)\b(hiring|jobs?|career)\b", criteria.raw_prompt or criteria.query_text or ""),
            )
        )
        limit = max(1, min(int(criteria.limit or 20), 50))
        errors: list[str] = []
        rows: list[dict[str, Any]] = []
        meta: dict[str, Any] = {"attribution": "Source: Y Combinator company directory (public)."}

        try:
            key = fetch_algolia_secured_key()
            rows = self._algolia_search(criteria, key=key, hiring_only=hiring_only, limit=limit * 3)
            meta["backend"] = "algolia"
        except Exception as exc:  # noqa: BLE001
            errors.append(f"ycombinator algolia: {exc}")
            try:
                rows = self._oss_fallback(criteria, hiring_only=hiring_only, limit=limit * 3)
                meta["backend"] = "yc_oss_fallback"
            except Exception as exc2:  # noqa: BLE001
                return FetchResult(errors=errors + [f"ycombinator oss: {exc2}"], meta=meta)

        excluded = {c.lower() for c in criteria.excluded_companies}
        today = date.today().isoformat()
        leads: list[Lead] = []

        for row in rows:
            company = sanitize_text(str(row.get("name") or ""), max_len=120)
            if not company or company.lower() in excluded:
                continue
            blob = _stack_blob(row)
            if criteria.technologies and not _matches_stack(blob, criteria.technologies):
                continue
            if not _geo_ok(row, criteria.geographies):
                continue
            if hiring_only and not row.get("isHiring"):
                continue
            try:
                lead = self._normalize(row, criteria=criteria, today=today)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"ycombinator parse: {exc}")
                continue
            leads.append(lead)
            if len(leads) >= limit:
                break

        if enrich_founders:
            for lead in leads:
                try:
                    self._enrich_founders(lead, today=today)
                    time.sleep(0.35 + random.random() * 0.25)
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"ycombinator founders {lead.company}: {exc}")

        if enrich_site_email:
            for lead in leads[: min(10, len(leads))]:
                website = str((lead.raw or {}).get("website") or "")
                if not website.startswith("http"):
                    continue
                try:
                    self._enrich_site_email(lead, website=website, today=today)
                    time.sleep(0.25 + random.random() * 0.2)
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"ycombinator site {lead.company}: {exc}")

        meta.update(
            {
                "raw_count": len(rows),
                "returned": len(leads),
                "hiring_only": hiring_only,
                "enrich_founders": enrich_founders,
            }
        )
        return FetchResult(leads=leads, errors=errors, meta=meta)

    def _algolia_query_terms(self, criteria: SearchCriteria) -> str:
        """Short Algolia query — AND-ing many tech tokens returns zero hits."""
        preferred = ("react", "saas", "typescript", "next.js", "node", "ai", "b2b")
        techs = [t.lower() for t in (criteria.technologies or [])]
        picked: list[str] = []
        for p in preferred:
            if any(p in t or t in p for t in techs):
                # Algolia matches "nextjs" better than "next.js"
                picked.append("nextjs" if p == "next.js" else p)
            if len(picked) >= 2:
                break
        if not picked:
            raw = (criteria.query_text or "").lower()
            for p in preferred:
                if p in raw:
                    picked.append("nextjs" if p == "next.js" else p)
                if len(picked) >= 2:
                    break
        return " ".join(picked) if picked else "saas software"

    def _algolia_search(
        self,
        criteria: SearchCriteria,
        *,
        key: str,
        hiring_only: bool,
        limit: int,
    ) -> list[dict[str, Any]]:
        query = self._algolia_query_terms(criteria)
        body: dict[str, Any] = {
            "query": query,
            "hitsPerPage": min(100, max(limit * 3, 30)),
            "page": 0,
        }
        # Prefer string filters; nested status+hiring facetFilters often over-constrain.
        filters: list[str] = ['status:"Active"']
        if hiring_only:
            filters.append("isHiring:true")
        body["filters"] = " AND ".join(filters)

        data = _http_post_json(
            ALGOLIA_URL,
            body,
            headers={
                "X-Algolia-Application-Id": ALGOLIA_APP,
                "X-Algolia-API-Key": key,
            },
        )
        hits = data.get("hits") or []
        if not hits and hiring_only:
            # Retry with hiring only (some older rows omit status facet)
            body.pop("filters", None)
            body["filters"] = "isHiring:true"
            data = _http_post_json(
                ALGOLIA_URL,
                body,
                headers={
                    "X-Algolia-Application-Id": ALGOLIA_APP,
                    "X-Algolia-API-Key": key,
                },
            )
            hits = data.get("hits") or []
        return [h for h in hits if isinstance(h, dict)]

    def _oss_fallback(
        self,
        criteria: SearchCriteria,
        *,
        hiring_only: bool,
        limit: int,
    ) -> list[dict[str, Any]]:
        url = YC_OSS_HIRING if hiring_only else YC_OSS_ALL
        try:
            data = fetch_json(url)
        except urllib.error.HTTPError:
            data = fetch_json(YC_OSS_HIRING)
        if not isinstance(data, list):
            return []
        out: list[dict[str, Any]] = []
        for row in data:
            if not isinstance(row, dict):
                continue
            if row.get("status") and str(row.get("status")).lower() not in ("active", ""):
                if hiring_only:
                    continue
            if hiring_only and not row.get("isHiring"):
                continue
            blob = _stack_blob(row)
            if criteria.technologies and not _matches_stack(blob, criteria.technologies):
                continue
            out.append(row)
            if len(out) >= limit:
                break
        return out

    def _normalize(self, row: dict[str, Any], *, criteria: SearchCriteria, today: str) -> Lead:
        company = sanitize_text(str(row.get("name") or ""), max_len=120)
        one_liner = sanitize_text(str(row.get("one_liner") or ""), max_len=200)
        batch = sanitize_text(str(row.get("batch") or ""), max_len=40)
        slug = str(row.get("slug") or "").strip()
        yc_url = str(row.get("url") or "").strip()
        if not yc_url and slug:
            yc_url = f"https://www.ycombinator.com/companies/{slug}"
        website = str(row.get("website") or "").strip()
        is_hiring = bool(row.get("isHiring"))
        location = sanitize_text(str(row.get("all_locations") or ""), max_len=160)
        regions = [str(r) for r in (row.get("regions") or [])]
        desc = sanitize_text(str(row.get("long_description") or one_liner), max_len=4000)
        blob = f"{one_liner}\n{desc}\nYC batch {batch}\n{'hiring' if is_hiring else ''}"

        lead_type: LeadType = "full_time" if is_hiring else "client"
        source_kind = "job_listing" if is_hiring else "directory"
        intent, intent_x = classify_intent(
            title=one_liner or company,
            description=blob,
            lead_type_hint=lead_type,
            source_kind=source_kind,
        )
        if not is_hiring and intent == "POTENTIAL_FIT":
            intent_x = (
                f"YC-backed company ({batch or 'batch unknown'}); funding/directory "
                "signal only — no published hiring ask in directory row"
            )

        tech = []
        for m in _STACK_RE.finditer(f"{one_liner} {desc}"):
            tok = m.group(0).lower()
            if tok not in tech:
                tech.append(tok)
        for t in criteria.technologies:
            if t.lower() not in {x.lower() for x in tech}:
                # keep criteria stack as soft tags when description is thin
                pass

        title = one_liner or f"YC company — {company}"
        if is_hiring:
            title = f"[Hiring] {title}"

        workplace = detect_workplace(location + " " + " ".join(regions))
        country = detect_country(location) or (
            detect_country(" ".join(regions)) if regions else None
        )

        evidence = [
            Evidence(
                summary=f"Y Combinator directory: {company} ({batch or 'batch n/a'})"
                + (" — marked isHiring" if is_hiring else ""),
                excerpt=safe_excerpt(one_liner or desc, max_len=280),
                source_url=yc_url,
                checked_date=today,
            )
        ]
        if website:
            evidence.append(
                Evidence(
                    summary="Company website from YC directory",
                    excerpt=website,
                    source_url=website,
                    checked_date=today,
                )
            )

        lead_id = make_lead_id(
            source="ycombinator",
            company=company,
            title=title,
            url=yc_url or website,
        )
        contacts: list[ContactChannel] = []
        if website:
            # Placeholder until site enrichment; directory itself has no emails
            contacts = build_contacts_from_listing(
                description="",
                listing_url=yc_url,
                company=company,
                check_mx=False,
            )

        risks = [
            "Co-founder emails are not published on YC pages — use LinkedIn/profile links only "
            "unless an address literally appears on the company site.",
        ]
        if not is_hiring:
            risks.append(
                "Directory/funding alone is not proven demand (demand_proven expected false unless hiring)."
            )

        return Lead(
            id=lead_id,
            name=company,
            lead_type=lead_type,
            company=company,
            title=title,
            url=yc_url or website,
            source="ycombinator",
            intent=intent,
            intent_explanation=intent_x,
            evidence=evidence,
            technical_requirements=tech[:8],
            profile_match_reasons=[
                f"YC batch {batch}" if batch else "YC-backed company",
                "Software/SaaS-adjacent listing" if _STACK_RE.search(blob) else "YC directory match",
            ],
            recommended_service=(
                "Full-stack React/Next.js product engineering (contract or full-time)"
            ),
            contacts=contacts,
            location=location,
            workplace=workplace or "unknown",
            country=country,
            checked_date=today,
            status="needs_review" if not is_hiring else "new",
            risks=risks,
            next_action=(
                "Open founder LinkedIn (published) or apply on careers if hiring"
                if is_hiring
                else "Review founders on YC page; LinkedIn outreach only — no invented email"
            ),
            raw={
                "batch": batch,
                "slug": slug,
                "website": website,
                "isHiring": is_hiring,
                "one_liner": one_liner,
                "team_size": row.get("team_size"),
                "industry": row.get("industry"),
                "regions": regions,
                "founders": [],
                "app_name": company,
                "product": one_liner,
            },
        )

    def _enrich_founders(self, lead: Lead, *, today: str) -> None:
        url = lead.url
        if not url or "ycombinator.com/companies/" not in url:
            return
        html = _http_get(url)
        founders = parse_founders_json(html)
        cleaned: list[dict[str, Any]] = []
        for f in founders:
            if not isinstance(f, dict):
                continue
            name = sanitize_text(str(f.get("full_name") or ""), max_len=80)
            if not name:
                continue
            title = sanitize_text(str(f.get("title") or "Founder"), max_len=80)
            li = str(f.get("linkedin_url") or "").strip() or None
            # has_email is a Bookface flag — never treat as a published mailbox
            cleaned.append(
                {
                    "full_name": name,
                    "title": title,
                    "linkedin_url": li,
                    "twitter_url": str(f.get("twitter_url") or "").strip() or None,
                    "is_active": bool(f.get("is_active", True)),
                    "linkedin_search": linkedin_people_search(name, lead.company),
                }
            )
            if li:
                lead.contacts.append(
                    ContactChannel(
                        channel_type="professional_profile",
                        value=li,
                        name=name,
                        title=title,
                        source_url=url,
                        verification_status="published_on_official_source",
                        verification_method="literal_url_on_yc_company_page",
                        date_checked=today,
                        notes="Published founder LinkedIn on YC company page (not an email).",
                    )
                )
            else:
                lead.contacts.append(
                    ContactChannel(
                        channel_type="professional_profile",
                        value=linkedin_people_search(name, lead.company),
                        name=name,
                        title=title,
                        source_url=url,
                        verification_status="unverified",
                        verification_method="linkedin_people_search_link_only",
                        date_checked=today,
                        notes=(
                            "Founder name published on YC; LinkedIn URL missing — "
                            "search link only, not a verified profile."
                        ),
                    )
                )
            lead.evidence.append(
                Evidence(
                    summary=f"YC-listed founder: {name} ({title})",
                    excerpt=(li or "LinkedIn URL not published on YC page"),
                    source_url=url,
                    checked_date=today,
                )
            )

        lead.raw = dict(lead.raw or {})
        lead.raw["founders"] = cleaned
        if cleaned:
            names = ", ".join(c["full_name"] for c in cleaned[:4])
            lead.next_action = (
                f"Contact founder(s) via published LinkedIn: {names}"
                + (" — or apply if hiring" if lead.raw.get("isHiring") else "")
            )

    def _enrich_site_email(self, lead: Lead, *, website: str, today: str) -> None:
        """Pull emails only if they literally appear on public company pages."""
        base = website.rstrip("/")
        paths = ["", "/contact", "/about", "/company", "/careers", "/team"]
        seen_emails: set[str] = set()
        for path in paths:
            url = base if not path else f"{base}{path}"
            try:
                page = _http_get(url)
            except Exception:  # noqa: BLE001
                continue
            for email in extract_published_emails(page):
                if email in seen_emails:
                    continue
                seen_emails.add(email)
                lead.contacts.append(
                    ContactChannel(
                        channel_type="email",
                        value=email,
                        name=None,
                        title=None,
                        source_url=url,
                        verification_status="published_on_official_source",
                        verification_method="literal_email_on_company_public_page",
                        date_checked=today,
                        notes=f"Published on company page {url} (not from YC).",
                    )
                )
                lead.evidence.append(
                    Evidence(
                        summary=f"Published email on company site: {email}",
                        excerpt=email,
                        source_url=url,
                        checked_date=today,
                    )
                )
                if len(seen_emails) >= 3:
                    return
            time.sleep(0.15 + random.random() * 0.1)


__all__ = [
    "YCCompaniesSource",
    "fetch_algolia_secured_key",
    "parse_founders_json",
    "linkedin_people_search",
]
