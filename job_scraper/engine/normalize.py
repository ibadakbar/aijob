"""Country / workplace / HTML cleanup helpers."""

from __future__ import annotations

import html
import re
from typing import Optional

from .model import Workplace

# Target markets for this engine (Pakistan outbound).
TARGET_COUNTRIES = {
    "DE": ["germany", "deutschland", "berlin", "munich", "münchen", "hamburg", "frankfurt", "cologne", "köln"],
    "NL": ["netherlands", "holland", "amsterdam", "rotterdam", "utrecht", "eindhoven"],
    "GB": ["united kingdom", "uk", "england", "scotland", "wales", "london", "manchester", "edinburgh", "belfast", "northern ireland"],
    "IE": ["ireland", "dublin", "cork", "galway"],
    "AU": ["australia", "sydney", "melbourne", "brisbane", "perth", "adelaide", "canberra"],
    "CA": ["canada", "toronto", "vancouver", "montreal", "ottawa", "calgary"],
    "NZ": ["new zealand", "auckland", "wellington", "christchurch"],
    "US": ["united states", "usa", "u.s.", "new york", "san francisco", "seattle", "austin", "boston", "remote - us"],
    "SE": ["sweden", "stockholm", "gothenburg", "göteborg", "malmö"],
    "FI": ["finland", "helsinki", "espoo"],
    "DK": ["denmark", "copenhagen", "aarhus", "øresund"],
    "AE": ["uae", "united arab emirates", "dubai", "abu dhabi"],
    "SA": ["saudi arabia", "riyadh", "jeddah", "dammam"],
    "QA": ["qatar", "doha"],
    "PK": ["pakistan", "karachi", "lahore", "islamabad"],
    "CH": ["switzerland", "zurich", "zürich", "geneva", "basel"],
}

ROLE_KEYWORDS = [
    "software engineer",
    "software developer",
    "full stack",
    "fullstack",
    "full-stack",
    "frontend",
    "front-end",
    "front end",
    "react",
    "next.js",
    "nextjs",
    "typescript",
    "node.js",
    "nodejs",
    "javascript engineer",
    "web engineer",
    "web developer",
]

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def strip_html(text: str) -> str:
    if not text:
        return ""
    # Greenhouse often double-escapes entities
    unescaped = html.unescape(html.unescape(text))
    plain = _TAG_RE.sub(" ", unescaped)
    return _WS_RE.sub(" ", plain).strip()


def detect_country(location: str, description: str = "") -> Optional[str]:
    blob = f"{location} {description[:500]}".lower()
    # Prefer more specific multi-word markers first by sorting markers by length
    scored: list[tuple[int, str]] = []
    for code, markers in TARGET_COUNTRIES.items():
        for m in markers:
            if m in blob:
                scored.append((len(m), code))
                break
    if not scored:
        if "remote" in blob and "europe" in blob:
            return None
        return None
    scored.sort(reverse=True)
    return scored[0][1]


def detect_workplace(location: str, description: str = "", explicit: Optional[str] = None) -> Workplace:
    if explicit:
        e = explicit.lower().replace(" ", "")
        if e in ("remote", "remotely"):
            return "remote"
        if e in ("hybrid",):
            return "hybrid"
        if e in ("onsite", "on-site"):
            return "onsite"
    blob = f"{location} {description[:800]}".lower()
    if re.search(r"\bhybrid\b", blob):
        return "hybrid"
    if re.search(r"\bremote\b", blob) and not re.search(r"not\s+remote", blob):
        return "remote"
    if re.search(r"on[\s-]?site|in[\s-]?office", blob):
        return "onsite"
    return "unknown"


def title_matches_roles(title: str) -> bool:
    t = (title or "").lower()
    return any(k in t for k in ROLE_KEYWORDS)


def country_in_targets(country: Optional[str], targets: Optional[set[str]] = None) -> bool:
    if country is None:
        return True  # keep remote/unknown for later ranking; filter optionally
    allowed = targets or set(TARGET_COUNTRIES)
    return country in allowed
