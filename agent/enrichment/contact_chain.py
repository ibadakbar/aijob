"""Public contact-chain enricher.

Chain (published only — never invent emails/phones):
  listing / company URL → homepage → /contact /about /team /careers pages
  → extract literal email, phone, WhatsApp from HTML
  → if a contact name is known, prefer mailto near that name

Does not log into LinkedIn, guess name@company.com, or scrape private pages.
"""

from __future__ import annotations

import logging
import re
import time
from datetime import date
from html import unescape
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from agent.models.opportunity import OpportunityRecord, now_iso
from agent.quality.contact_ladder import (
    extract_published_phone,
    extract_published_whatsapp,
    is_valid_email_format,
    normalize_whatsapp,
)
from agent.scoring.scores import score_opportunity
from agent.storage.excel_store import ExcelStore

log = logging.getLogger("opportunity_agent")

_UA = (
    "Mozilla/5.0 (compatible; OpportunityAgent/1.0; +https://localhost; "
    "public-contact-enrichment)"
)
_TIMEOUT = 12
_MAX_BYTES = 400_000
_CONTACT_PATHS = (
    "/contact",
    "/contact-us",
    "/contacts",
    "/about",
    "/about-us",
    "/team",
    "/our-team",
    "/people",
    "/company",
    "/careers",
    "/jobs",
    "/hire",
    "/hiring",
    "/impressum",
    "/legal",
    "/support",
)
_SKIP_HOST_PARTS = (
    "linkedin.com",
    "facebook.com",
    "twitter.com",
    "x.com",
    "instagram.com",
    "youtube.com",
    "google.com",
    "github.com",
    "glassdoor.",
    "indeed.",
    "lever.co",
    "greenhouse.io",
    "ashbyhq.com",
    "workable.com",
    "freehire.me",
    "remotive.com",
    "weworkremotely.com",
    "jobleads.",
    "whatjobs.",
    "upwork.com",
    "freelancer.com",
    "fiverr.com",
    "zeerk.com",
    "peopleperhour.com",
    "contra.com",
    "craigslist.",
)

_EMAIL_RE = re.compile(
    r"(?<![A-Za-z0-9._%+-])"
    r"([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,24})"
    r"(?![A-Za-z0-9._%+-])"
)
_FAKE_LOCAL = {
    "example",
    "email",
    "name",
    "user",
    "test",
    "noreply",
    "no-reply",
    "donotreply",
    "privacy",
    "webmaster",
}
_FAKE_DOMAINS = {
    "example.com",
    "example.org",
    "sentry.io",
    "wixpress.com",
    "googleapis.com",
    "schema.org",
    "email.com",
    "domain.com",
    "company.com",
}


def _strip_html(html: str) -> str:
    raw = html or ""
    # Pull mailto/tel/wa links out of attributes BEFORE tag strip (otherwise lost)
    extras: list[str] = []
    for m in re.finditer(r"(?i)mailto:([A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,24})", raw):
        extras.append(m.group(1))
    for m in re.finditer(r"(?i)tel:([+\d][\d\-().\s]{6,})", raw):
        extras.append(m.group(1))
    for m in re.finditer(
        r"(?i)(?:https?://)?(?:wa\.me/|api\.whatsapp\.com/send\?phone=)(\+?[\d]+)",
        raw,
    ):
        extras.append(m.group(0))
    text = re.sub(r"(?is)<script[^>]*>.*?</script>", " ", raw)
    text = re.sub(r"(?is)<style[^>]*>.*?</style>", " ", text)
    text = re.sub(r"(?is)<!--.*?-->", " ", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = unescape(text)
    if extras:
        text = text + " " + " ".join(extras)
    return re.sub(r"\s+", " ", text).strip()


def _fetch(url: str, *, timeout: int = _TIMEOUT) -> tuple[str, str]:
    """Return (final_url, html_text) or ("", "")."""
    url = (url or "").strip()
    if not url.startswith(("http://", "https://")):
        return "", ""
    try:
        req = Request(url, headers={"User-Agent": _UA, "Accept": "text/html,*/*"})
        with urlopen(req, timeout=timeout) as resp:
            final = str(resp.geturl() or url)
            raw = resp.read(_MAX_BYTES)
            charset = "utf-8"
            ctype = (resp.headers.get_content_charset() or "").strip()
            if ctype:
                charset = ctype
            try:
                html = raw.decode(charset, errors="replace")
            except LookupError:
                html = raw.decode("utf-8", errors="replace")
            return final, html
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        log.debug("fetch failed %s: %s", url, exc)
        return "", ""


def _host_ok(url: str) -> bool:
    try:
        host = (urlparse(url).hostname or "").lower()
    except ValueError:
        return False
    if not host:
        return False
    return not any(part in host for part in _SKIP_HOST_PARTS)


def _homepage(url: str) -> str:
    try:
        p = urlparse(url)
        if not p.scheme or not p.netloc:
            return ""
        return f"{p.scheme}://{p.netloc}/"
    except ValueError:
        return ""


def _same_host(a: str, b: str) -> bool:
    try:
        return (urlparse(a).hostname or "").lower() == (urlparse(b).hostname or "").lower()
    except ValueError:
        return False


def _clean_email(email: str) -> str:
    e = (email or "").strip().lower().rstrip(".,;:)")
    if not e or not is_valid_email_format(e):
        return ""
    local, _, domain = e.partition("@")
    if local.split("+")[0] in _FAKE_LOCAL:
        return ""
    if domain in _FAKE_DOMAINS or domain.endswith(".example"):
        return ""
    if domain.endswith((".png", ".jpg", ".gif", ".svg", ".webp", ".css", ".js")):
        return ""
    return e


def _emails_from_text(text: str) -> list[str]:
    out: list[str] = []
    for m in _EMAIL_RE.finditer(text or ""):
        e = _clean_email(m.group(1))
        if e and e not in out:
            out.append(e)
    return out


def _prefer_email_near_name(text: str, name: str, emails: list[str]) -> str:
    """If contact name appears near a mailto/email on a team page, prefer that."""
    if not name or not emails:
        return emails[0] if emails else ""
    parts = [p for p in re.split(r"\s+", name.strip()) if len(p) >= 2]
    if not parts:
        return emails[0]
    # Window search around name
    for m in re.finditer(re.escape(parts[0]), text, re.I):
        start = max(0, m.start() - 120)
        end = min(len(text), m.end() + 200)
        window = text[start:end]
        if len(parts) > 1 and parts[-1].casefold() not in window.casefold():
            continue
        near = _emails_from_text(window)
        for e in near:
            if e in emails:
                return e
    # Name local-part match only if email literally on page (already in emails)
    first = parts[0].casefold()
    for e in emails:
        local = e.split("@", 1)[0].casefold()
        if first in local:
            return e
    return emails[0]


def _candidate_urls(rec: OpportunityRecord) -> list[str]:
    seeds: list[str] = []
    for raw in (
        rec.company_website,
        rec.source_url,
    ):
        u = (raw or "").strip()
        if u.startswith("http") and _host_ok(u):
            seeds.append(u)
    # URLs embedded in description/evidence
    blob = f"{rec.description or ''} {rec.evidence or ''}"
    for m in re.finditer(r"https?://[^\s<>\"']+", blob):
        u = m.group(0).rstrip(").,;]'\"")
        if _host_ok(u):
            seeds.append(u)
    # Dedupe preserving order
    out: list[str] = []
    seen: set[str] = set()
    for u in seeds:
        key = u.rstrip("/").casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(u)
    return out


def _contact_page_urls(home: str, html: str, *, limit: int = 5) -> list[str]:
    found: list[str] = []
    # Standard path guesses
    for path in _CONTACT_PATHS:
        found.append(urljoin(home, path))
    # Links on homepage that look like contact/about/team
    for m in re.finditer(r'(?i)href=["\']([^"\']+)["\']', html or ""):
        href = m.group(1).strip()
        if href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
            continue
        full = urljoin(home, href)
        if not _same_host(home, full):
            continue
        path = (urlparse(full).path or "").casefold()
        # Skip auth walls
        if any(x in path for x in ("/login", "/signin", "/signup", "/auth")):
            continue
        if any(
            k in path
            for k in (
                "contact",
                "about",
                "team",
                "people",
                "career",
                "job",
                "hire",
                "impressum",
                "support",
            )
        ):
            found.append(full)
    out: list[str] = []
    seen: set[str] = set()
    for u in found:
        key = u.rstrip("/").casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(u)
        if len(out) >= limit:
            break
    return out


def enrich_record_contact_chain(
    rec: OpportunityRecord,
    *,
    max_pages: int = 5,
    timeout: int = _TIMEOUT,
) -> dict[str, Any]:
    """Mutate ``rec`` with published contacts found via public page chain."""
    before = {
        "email": rec.contact_email or "",
        "phone": getattr(rec, "contact_phone", "") or "",
        "whatsapp": getattr(rec, "contact_whatsapp", "") or "",
        "linkedin": rec.linkedin_url or "",
    }
    # Skip if already has strong contact
    if before["email"] and (before["phone"] or before["whatsapp"]):
        return {"ok": True, "skipped": True, "reason": "already_has_contacts", "pages": 0}

    seeds = _candidate_urls(rec)
    if not seeds:
        return {"ok": True, "skipped": True, "reason": "no_public_url", "pages": 0}

    pages_fetched = 0
    all_text: list[str] = []
    chain_urls: list[str] = []
    home = ""

    # If seed is a directory (YC etc.), pull the real company website first
    expanded: list[str] = []
    for seed in seeds[:3]:
        host = (urlparse(seed).hostname or "").lower()
        if "ycombinator.com" in host:
            _f, html = _fetch(seed, timeout=timeout)
            if html:
                pages_fetched += 1
                chain_urls.append(_f or seed)
                all_text.append(_strip_html(html))
                for m in re.finditer(
                    r'(?i)href=["\'](https?://(?!(?:www\.)?ycombinator\.com|bookface-static)[^"\']+)["\']',
                    html,
                ):
                    cand = m.group(1).split("?")[0].rstrip("/")
                    low = cand.casefold()
                    if any(
                        x in low
                        for x in (
                            "linkedin.com",
                            "twitter.com",
                            "facebook.com",
                            "github.com",
                            ".ico",
                            ".png",
                            ".svg",
                            ".jpg",
                            "googleapis.com",
                            "cloudflare",
                        )
                    ):
                        continue
                    if not _host_ok(cand):
                        continue
                    home_c = _homepage(cand)
                    if not home_c:
                        continue
                    expanded.append(home_c)
                    if not rec.company_website:
                        rec.company_website = home_c.rstrip("/")
                    break
            continue
        expanded.append(seed)
    if not expanded:
        expanded = [s for s in seeds if _host_ok(s)][:2]

    for seed in expanded[:2]:
        final, html = _fetch(seed, timeout=timeout)
        if not html:
            continue
        pages_fetched += 1
        chain_urls.append(final or seed)
        all_text.append(_strip_html(html))
        home = _homepage(final or seed)
        if home and not rec.company_website:
            rec.company_website = home.rstrip("/")
        # Follow contact/about/team on same host
        for page in _contact_page_urls(home or seed, html, limit=max_pages):
            if pages_fetched >= max_pages:
                break
            if page.rstrip("/").casefold() in {u.rstrip("/").casefold() for u in chain_urls}:
                continue
            f2, h2 = _fetch(page, timeout=timeout)
            if not h2:
                continue
            pages_fetched += 1
            chain_urls.append(f2 or page)
            all_text.append(_strip_html(h2))
            time.sleep(0.35)  # polite
        if pages_fetched >= 2:
            break

    if not all_text:
        return {"ok": True, "skipped": False, "reason": "fetch_empty", "pages": 0}

    blob = "\n".join(all_text)
    emails = _emails_from_text(blob)
    phone = extract_published_phone(blob)
    wa = extract_published_whatsapp(blob)
    if not wa and phone and re.search(r"(?i)whats?\s*app", blob):
        wa = normalize_whatsapp(phone)

    email = ""
    if emails:
        email = _prefer_email_near_name(blob, rec.contact_name or "", emails)

    # Prefer hiring mailboxes when present
    for e in emails:
        local = e.split("@", 1)[0].lower()
        if local.split("+")[0] in {
            "careers",
            "jobs",
            "hiring",
            "hello",
            "join",
            "talent",
            "people",
            "founders",
            "hr",
            "recruiting",
        }:
            email = e
            break
    if not email and emails:
        email = emails[0]

    changed = False
    if email and not rec.contact_email:
        rec.contact_email = email
        rec.email_status = "PUBLIC_UNVERIFIED"
        changed = True
    if phone and not getattr(rec, "contact_phone", ""):
        rec.contact_phone = phone
        changed = True
    if wa and not getattr(rec, "contact_whatsapp", ""):
        rec.contact_whatsapp = wa
        changed = True

    # LinkedIn /in/ published on pages
    if not rec.linkedin_url:
        m = re.search(r"https?://(?:www\.)?linkedin\.com/in/[A-Za-z0-9\-_%]+/?", blob, re.I)
        if m:
            rec.linkedin_url = m.group(0).rstrip("/")
            changed = True

    if changed:
        note = "contact_chain=" + ",".join(chain_urls[:4])
        if rec.evidence:
            if "contact_chain=" not in rec.evidence:
                rec.evidence = f"{rec.evidence} | {note}"[:800]
        else:
            rec.evidence = note[:800]
        rec.last_verified = date.today().isoformat()
        score_opportunity(rec)

    return {
        "ok": True,
        "skipped": False,
        "changed": changed,
        "pages": pages_fetched,
        "urls": chain_urls[:8],
        "email": rec.contact_email or "",
        "phone": getattr(rec, "contact_phone", "") or "",
        "whatsapp": getattr(rec, "contact_whatsapp", "") or "",
        "before": before,
    }


def run_contact_chain_enrichment(
    store: ExcelStore | None = None,
    *,
    limit: int = 25,
    only_missing: bool = True,
    types: tuple[str, ...] = ("client", "job", "contract", "founder", "agency", "recruiter"),
) -> dict[str, Any]:
    """Enrich Excel rows missing email/phone via public page chain."""
    store = store or ExcelStore()
    store.ensure_workbook()
    rows = store.load_all_opportunities()
    ranked: list[tuple[int, OpportunityRecord]] = []
    for r in rows:
        otype = (r.opportunity_type or "").lower()
        if otype not in types:
            continue
        if (r.status or "").lower() in ("expired", "closed", "rejected", "withdrawn"):
            continue
        has_email = bool(r.contact_email)
        has_phone = bool(getattr(r, "contact_phone", ""))
        has_wa = bool(getattr(r, "contact_whatsapp", ""))
        if only_missing and has_email and (has_phone or has_wa):
            continue
        seeds = _candidate_urls(r)
        if not seeds:
            continue
        score = 0
        if r.company_website and _host_ok(r.company_website):
            score += 3
        if r.contact_name:
            score += 1
        if not has_email:
            score += 2
        ranked.append((score, r))
    ranked.sort(key=lambda x: x[0], reverse=True)
    candidates = [r for _s, r in ranked[:limit]]

    enriched = 0
    changed_rows: list[OpportunityRecord] = []
    details: list[dict[str, Any]] = []
    for rec in candidates:
        try:
            result = enrich_record_contact_chain(rec)
        except Exception as exc:  # noqa: BLE001
            log.warning("contact_chain failed for %s: %s", rec.id, exc)
            details.append({"id": rec.id, "ok": False, "error": str(exc)})
            continue
        details.append({"id": rec.id, "company": rec.company, **result})
        if result.get("changed"):
            enriched += 1
            changed_rows.append(rec)
        time.sleep(0.2)

    upsert: dict[str, Any] = {}
    if changed_rows:
        upsert = store.upsert_opportunities(
            changed_rows,
            history_summary=f"contact_chain enrichment {now_iso()}",
            backup=True,
        )
        store.record_source_run(
            "contact_chain",
            success=True,
            new_records=0,
            duplicates=int(upsert.get("updated") or 0),
        )

    return {
        "ok": True,
        "candidates": len(candidates),
        "enriched": enriched,
        "upsert": upsert,
        "samples": details[:15],
    }
