"""Description-first Path A / Path B eligibility for visa-aware discovery.

Path A — remote + (verified/possible sponsorship OR remote-international hire language).
Path B — onsite/hybrid + verified sponsorship/relocation into a target geography.
Path PK — Pakistan-local roles (any workplace: onsite / hybrid / remote). Kept even
without sponsorship language — local market exception for the candidate profile.

Fake-remote / country-only remote (US-only, within the U.S., Remote UK only, etc.) is
always dropped for remote roles — even if WWR/RemoteOK labels the row "Worldwide" or
sponsorship classification is possible/verified. Overseas hire language must appear
without a hard geo-lock in the same listing.
"""

from __future__ import annotations

import re
from typing import Optional

from .model import NormalizedJob
from .normalize import TARGET_COUNTRIES

_PAKISTAN_RE = re.compile(
    r"\b(pakistan|karachi|lahore|islamabad|rawalpindi|peshawar|faisalabad)\b",
    re.I,
)

_REMOTE_INTL = [
    r"\bworldwide\b",
    r"\bfrom\s+anywhere\b",
    r"\banywhere\s+in\s+the\s+world\b",
    r"\bwork\s+from\s+anywhere\b",
    r"\bremote[\s-]?international\b",
    r"\binternationally\s+remote\b",
    r"\boverseas\b",
    r"\bany\s+country\b",
    r"\bregardless\s+of\s+(location|country)\b",
    r"\bhire\s+(from\s+)?anywhere\b",
    r"\bhire\s+globally\b",
    r"\bwe\s+hire\s+globally\b",
    r"\bglobally\s+remote\b",
    r"\bremote\s+\(global\)\b",
    r"\bglobal\s+remote\b",
    r"\bremote[,\s]+global\b",
    r"\bEOR\b",
    r"\bemployer\s+of\s+record\b",
]

_FAKE_REMOTE = [
    r"within\s+the\s+u\.?\s*s\.?",
    r"from\s+anywhere\s+within\s+the\s+u\.?\s*s",
    r"anywhere\s+within\s+the\s+u\.?\s*s",
    r"u\.?s\.?\s+only",
    r"united\s+states\s+only",
    r"remote[,\s\-–—]+united\s+states\b",
    r"remote\s*[-–—]?\s*u\.?\s*s\.?\b",
    r"fully\s+remote\s*\(\s*us\s*\)",
    r"remote\s*\(\s*us\s*\)",
    r"u\.?s\.?\s*[- ]?\s*based",
    r"us[-\s]?based[,\s]+remote",
    r"must\s+be\s+(?:located|based|reside|living)\s+in\s+the\s+(?:us|u\.s\.|united\s+states)",
    r"candidates\s+must\s+be\s+currently\s+based\s+in\s+the\s+(?:us|united\s+states|netherlands|uk|united\s+kingdom|canada|australia)",
    r"authorized\s+to\s+work\s+in\s+the\s+u\.?s",
    r"work\s+authorization\s+in\s+the\s+(?:us|united\s+states)\b",
    r"must\s+have\s+(?:valid\s+)?(?:us|u\.s\.)\s+work\s+authorization",
    r"remote\s+(?:uk|united\s+kingdom|australia|canada|germany|netherlands|ireland)\s+only",
    r"headquarters:\s*remote\s*[-–—]\s*united\s+states",
    r"united\s+states,\s*canada,\s*or\s*south\s*america\s+only",
    r"(?:us|united\s+states).{0,40}(?:canada|south\s+america).{0,20}only",
]

_COUNTRY_ONLY_REMOTE = [
    r"remote\s*[-–—,]?\s*(us|usa|united states|uk|united kingdom|canada|australia|germany|netherlands|ireland|sweden|denmark|finland|switzerland|uae)\b",
    r"\b(us|usa|uk|canada|australia)[\s-]+only\b",
    r"must\s+be\s+(based|located)\s+in\s+(the\s+)?(us|usa|uk|united kingdom|canada|australia|germany|eu)\b",
    r"candidates\s+must\s+(reside|live)\s+in\b",
]

_REMOTE_INTL_RE = re.compile("|".join(_REMOTE_INTL), re.I)
_FAKE_REMOTE_RE = re.compile("|".join(_FAKE_REMOTE), re.I)
_COUNTRY_ONLY_RE = re.compile("|".join(_COUNTRY_ONLY_REMOTE), re.I)


def remote_international(text: str) -> bool:
    return bool(_REMOTE_INTL_RE.search(text or ""))


def country_only_remote(text: str) -> bool:
    return bool(_COUNTRY_ONLY_RE.search(text or ""))


def fake_remote(text: str) -> bool:
    """US/UK/AU-only 'remote' geo-locks (including WWR fake Worldwide labels)."""
    t = text or ""
    return bool(_FAKE_REMOTE_RE.search(t) or _COUNTRY_ONLY_RE.search(t))


def _remoteish(job: NormalizedJob, blob: str) -> bool:
    if job.workplace == "remote":
        return True
    if job.workplace == "unknown" and re.search(r"\bremote\b", blob, re.I):
        return True
    return False


def _pakistan_local(job: NormalizedJob) -> bool:
    """Pakistan-local roles: any workplace mode is allowed (profile exception).

    Prefer country / sweep tag / location — not full description — so a Berlin
    posting that mentions a Pakistan teammate does not get a false PK keep.
    """
    if job.country == "PK":
        return True
    if (job.raw or {}).get("sweep") == "pakistan_any_mode":
        return True
    if _PAKISTAN_RE.search(job.location or ""):
        return True
    return False


def path_ab_verdict(job: NormalizedJob) -> tuple[Optional[str], str]:
    """Return (path|None, reason). path is 'A', 'B', 'PK', or None if ineligible."""
    blob = f"{job.title or ''} {job.location or ''} {job.description or ''}"
    sp = job.sponsorship
    classification = sp.classification if sp else "unknown"
    reloc = bool(sp and sp.relocation_support)

    # Pakistan: keep onsite / hybrid / remote without requiring visa language.
    if _pakistan_local(job):
        return "PK", "pakistan local — any workplace mode allowed"

    if _remoteish(job, blob):
        # Fail closed on geo-locks even when feed title says "Worldwide" or
        # sponsorship classification is possible/verified (common WWR/RemoteOK noise).
        if fake_remote(blob):
            return None, "fake-remote / country-only remote"
        if classification in ("verified_in_listing", "possible"):
            return "A", f"remote + sponsorship={classification}"
        if remote_international(blob):
            return "A", "remote + remote-international hire language"
        return None, "remote without sponsorship or worldwide/overseas hire language"

    if job.workplace in ("onsite", "hybrid"):
        if classification == "verified_in_listing" or reloc:
            if job.country and job.country not in TARGET_COUNTRIES:
                return None, f"onsite/hybrid sponsorship but country {job.country} outside targets"
            return "B", f"{job.workplace} + sponsorship/relocation verified"
        return None, f"{job.workplace} without verified sponsorship/relocation"

    if fake_remote(blob) and re.search(r"\bremote\b", blob, re.I):
        return None, "fake-remote / country-only remote"
    if classification == "verified_in_listing" and remote_international(blob):
        return "A", "unknown workplace + verified sponsorship + remote-intl"
    if classification == "verified_in_listing" or reloc:
        return "B", "unknown workplace + verified sponsorship/relocation"
    if remote_international(blob) and "remote" in blob.lower():
        return "A", "unknown workplace + remote-intl language"
    return None, "workplace unknown / insufficient Path A/B evidence"


def filter_path_ab(jobs: list[NormalizedJob]) -> tuple[list[NormalizedJob], list[dict[str, str]]]:
    """Keep Path A/B jobs; return (kept, near_misses with reasons)."""
    kept: list[NormalizedJob] = []
    near: list[dict[str, str]] = []
    for job in jobs:
        path, reason = path_ab_verdict(job)
        if path:
            job.raw = {**(job.raw or {}), "path": path, "path_reason": reason}
            kept.append(job)
        else:
            near.append(
                {
                    "company": job.company,
                    "title": job.title,
                    "url": job.url,
                    "workplace": job.workplace,
                    "sponsorship": job.sponsorship.classification if job.sponsorship else "unknown",
                    "reason": reason,
                }
            )
    return kept, near
