"""Deduplicate leads by URL, company+title, and stable id."""

from __future__ import annotations

import hashlib
import re
from urllib.parse import urlsplit, urlunsplit

from .model import Lead
from .score import intent_rank_key


def normalize_url(url: str) -> str:
    parts = urlsplit((url or "").strip())
    if not parts.scheme or not parts.netloc:
        return (url or "").rstrip("/").lower()
    path = parts.path.rstrip("/") or "/"
    host = parts.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return urlunsplit((parts.scheme.lower(), host, path, "", "")).lower()


def fold_name(value: str) -> str:
    return "".join(ch for ch in (value or "").lower() if ch.isalnum())


def domain_of(url: str) -> str:
    host = urlsplit(url or "").netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def company_title_key(company: str, title: str) -> str:
    return f"{fold_name(company)}::{fold_name(title)}"


def make_lead_id(*, source: str, company: str, title: str, url: str) -> str:
    """Stable id from source + company + title + normalized URL."""
    raw = f"{source}|{company_title_key(company, title)}|{normalize_url(url)}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
    slug = re.sub(r"[^a-z0-9]+", "-", (company or "lead").lower()).strip("-")[:24] or "lead"
    return f"{slug}-{digest}"


def _better(a: Lead, b: Lead) -> Lead:
    ia, ib = intent_rank_key(a.intent), intent_rank_key(b.intent)
    if ia != ib:
        return a if ia < ib else b
    sa = a.scores.overall if a.scores else 0.0
    sb = b.scores.overall if b.scores else 0.0
    if sa != sb:
        return a if sa >= sb else b
    # Prefer richer evidence / contacts
    if len(a.evidence) != len(b.evidence):
        return a if len(a.evidence) > len(b.evidence) else b
    return a if len(a.contacts) >= len(b.contacts) else b


def dedupe_leads(leads: list[Lead]) -> list[Lead]:
    by_url: dict[str, Lead] = {}
    url_to_ct: dict[str, str] = {}
    for lead in leads:
        url_key = normalize_url(lead.url)
        ct = company_title_key(lead.company, lead.title)
        if url_key in by_url:
            by_url[url_key] = _better(by_url[url_key], lead)
            continue
        existing = next((u for u, c in url_to_ct.items() if c == ct), None)
        if existing is not None:
            by_url[existing] = _better(by_url[existing], lead)
            continue
        by_url[url_key] = lead
        url_to_ct[url_key] = ct
    return list(by_url.values())
