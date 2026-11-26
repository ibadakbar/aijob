"""Contact ladder: public email → founder LinkedIn → careers apply URL only.

Never invent emails. Format-check + optional MX; mark provenance.
"""

from __future__ import annotations

import re
import smtplib
import socket
from dataclasses import dataclass
from typing import Any, Optional

_EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,24}$"
)

# Tier A hiring mailboxes (must be published — we only validate format/MX)
_TIER_A_LOCAL = frozenset(
    {
        "careers",
        "jobs",
        "hiring",
        "hello",
        "join",
        "talent",
        "people",
        "founders",
        "recruiting",
        "hr",
    }
)

_INFER_FORBIDDEN = re.compile(
    r"(?i)\b(guess|pattern|inferred|constructed|likely|probably)\b"
)


_PHONE_RE = re.compile(
    r"(?:\+|00)?[\d][\d\s\-().]{7,18}\d"
)


@dataclass
class ContactVerdict:
    tier: str  # A | B | C | none
    email: str = ""
    phone: str = ""
    whatsapp: str = ""  # wa.me link or empty
    email_status: str = "NOT_FOUND"  # VERIFIED | PUBLIC_UNVERIFIED | INFERRED | NOT_FOUND
    linkedin_url: str = ""
    apply_url: str = ""
    provenance: str = ""
    drop: bool = False
    drop_reason: str = ""


def extract_published_phone(*blobs: str) -> str:
    """Return a phone only when clearly present in published text — never invent."""
    for blob in blobs:
        text = blob or ""
        # Prefer labeled phones
        labeled = re.search(
            r"(?i)(?:phone|tel|mobile|whatsapp|call)\s*[:#]?\s*((?:\+|00)?[\d][\d\s\-().]{7,18}\d)",
            text,
        )
        if labeled:
            return re.sub(r"\s+", " ", labeled.group(1)).strip()
        tel = re.search(r"tel:([+\d][\d\-().\s]{6,})", text, re.I)
        if tel:
            return re.sub(r"\s+", " ", tel.group(1)).strip()
    return ""


def _digits_phone(raw: str) -> str:
    digits = re.sub(r"\D", "", raw or "")
    if digits.startswith("00"):
        digits = digits[2:]
    return digits


def normalize_whatsapp(raw: str) -> str:
    """Normalize published WhatsApp to ``https://wa.me/<digits>`` or empty."""
    val = (raw or "").strip()
    if not val:
        return ""
    # Already a wa.me / api.whatsapp.com link
    m = re.search(
        r"(?:https?://)?(?:wa\.me/|api\.whatsapp\.com/send\?phone=)(\+?[\d]+)",
        val,
        re.I,
    )
    if m:
        digits = _digits_phone(m.group(1))
        if 8 <= len(digits) <= 15:
            return f"https://wa.me/{digits}"
    digits = _digits_phone(val)
    if 8 <= len(digits) <= 15:
        return f"https://wa.me/{digits}"
    return ""


def extract_published_whatsapp(*blobs: str) -> str:
    """Return WhatsApp only when literally published — never invent.

    Looks for wa.me / api.whatsapp.com links and labeled WhatsApp numbers.
    """
    for blob in blobs:
        text = blob or ""
        if not text:
            continue
        # Explicit WhatsApp deep links
        for m in re.finditer(
            r"(?:https?://)?(?:wa\.me/|api\.whatsapp\.com/send\?phone=)(\+?[\d]+)",
            text,
            re.I,
        ):
            got = normalize_whatsapp(m.group(0))
            if got:
                return got
        # Labeled WhatsApp: ... number
        labeled = re.search(
            r"(?i)(?:whats?\s*app|whatsapp|wa)\s*[:#/\-]?\s*((?:\+|00)?[\d][\d\s\-().]{7,18}\d)",
            text,
        )
        if labeled:
            got = normalize_whatsapp(labeled.group(1))
            if got:
                return got
        # "chat on WhatsApp" near a phone
        near = re.search(
            r"(?i)whats?\s*app.{0,40}?((?:\+|00)?[\d][\d\s\-().]{7,18}\d)",
            text,
        )
        if near:
            got = normalize_whatsapp(near.group(1))
            if got:
                return got
    return ""


def is_valid_email_format(email: str) -> bool:
    e = (email or "").strip()
    if not e or len(e) > 254:
        return False
    if not _EMAIL_RE.match(e):
        return False
    local, _, domain = e.partition("@")
    if not local or not domain or ".." in e:
        return False
    return True


def mx_present(domain: str, timeout: float = 3.0) -> bool | None:
    """Return True/False if resolvable; None if DNS libs unavailable / timeout."""
    domain = (domain or "").strip().lower().rstrip(".")
    if not domain:
        return None
    try:
        import dns.resolver  # type: ignore

        answers = dns.resolver.resolve(domain, "MX", lifetime=timeout)
        return len(list(answers)) > 0
    except ImportError:
        pass
    except Exception:  # noqa: BLE001
        return False
    # Fallback: A-record exists (weak signal)
    try:
        socket.setdefaulttimeout(timeout)
        socket.getaddrinfo(domain, 25)
        return True
    except OSError:
        return False


def classify_email(
    email: str,
    *,
    verification_status: str = "",
    notes: str = "",
    check_mx: bool = True,
) -> tuple[str, str]:
    """Return (email_status, provenance). INFERRED → caller should drop."""
    e = (email or "").strip()
    if not e:
        return "NOT_FOUND", ""
    blob = f"{verification_status} {notes}"
    if _INFER_FORBIDDEN.search(blob) or verification_status.lower() in (
        "inferred",
        "guessed",
        "pattern_generated",
    ):
        return "INFERRED", "rejected_inferred_email"
    if not is_valid_email_format(e):
        return "INFERRED", "invalid_email_format"

    status = "PUBLIC_UNVERIFIED"
    prov = "published_literal"
    if verification_status in (
        "published_on_official_source",
        "domain_mx_present",
        "literal_email_on_official_page",
    ):
        prov = verification_status

    if check_mx:
        domain = e.split("@", 1)[1]
        mx = mx_present(domain)
        if mx is True:
            status = "VERIFIED"
            prov = f"{prov}+mx"
        elif mx is False:
            # Keep but flag — domain may still accept via A record elsewhere
            status = "PUBLIC_UNVERIFIED"
            prov = f"{prov}+no_mx"

    return status, prov


def ladder_from_contacts(
    contacts: list[dict[str, Any]] | None,
    *,
    source_url: str = "",
    founders: list[dict[str, Any]] | None = None,
    check_mx: bool = False,
) -> ContactVerdict:
    """Pick best published contact. Never invent."""
    email = ""
    phone = ""
    whatsapp = ""
    email_status = "NOT_FOUND"
    email_prov = ""
    linkedin = ""
    name = ""
    title = ""

    for ch in contacts or []:
        if not isinstance(ch, dict):
            continue
        ctype = str(ch.get("channel_type") or ch.get("type") or "")
        val = str(ch.get("value") or "").strip()
        vs = str(ch.get("verification_status") or "")
        notes = str(ch.get("notes") or "")
        if ctype == "email" and val and not email:
            st, prov = classify_email(val, verification_status=vs, notes=notes, check_mx=check_mx)
            if st == "INFERRED":
                continue  # never keep invented
            email = val
            email_status = st
            email_prov = prov
            name = str(ch.get("name") or "")
            title = str(ch.get("title") or "")
        if ctype in ("whatsapp", "wa", "whats_app") and val and not whatsapp:
            whatsapp = normalize_whatsapp(val) or extract_published_whatsapp(val, notes)
        if ctype in ("phone", "tel", "whatsapp", "mobile") and val and not phone:
            phone = val
            if ctype == "whatsapp" and not whatsapp:
                whatsapp = normalize_whatsapp(val)
        elif not phone:
            maybe = extract_published_phone(val, notes)
            if maybe and ("phone" in ctype.lower() or "tel" in ctype.lower() or ctype == "unknown"):
                # Only accept unknown-channel values that look like phones with enough digits
                digits = re.sub(r"\D", "", maybe)
                if 8 <= len(digits) <= 15:
                    phone = maybe
        # Catch wa.me in any channel value/notes
        if not whatsapp:
            whatsapp = extract_published_whatsapp(val, notes)
        if ctype == "professional_profile" and "linkedin.com/in/" in val.lower() and not linkedin:
            linkedin = val
        if ctype in ("application_page", "url") and val.startswith("http") and not source_url:
            source_url = val

    for f in founders or []:
        if not isinstance(f, dict):
            continue
        li = str(f.get("linkedin_url") or f.get("linkedin") or "")
        if "linkedin.com/in/" in li.lower() and not linkedin:
            linkedin = li
            if not name:
                name = str(f.get("name") or "")
                title = str(f.get("title") or "Founder")

    apply_url = source_url or ""

    if email:
        local = email.split("@", 1)[0].lower()
        tier = "A"
        if local.split("+")[0] in _TIER_A_LOCAL or title:
            tier = "A"
        return ContactVerdict(
            tier=tier,
            email=email,
            phone=phone,
            whatsapp=whatsapp,
            email_status=email_status,
            linkedin_url=linkedin,
            apply_url=apply_url,
            provenance=email_prov or "published_email",
        )
    if whatsapp or phone:
        return ContactVerdict(
            tier="A",
            phone=phone,
            whatsapp=whatsapp,
            linkedin_url=linkedin,
            apply_url=apply_url,
            provenance="published_whatsapp" if whatsapp else "published_phone",
            email_status="NOT_FOUND",
        )
    if linkedin:
        return ContactVerdict(
            tier="B",
            linkedin_url=linkedin,
            apply_url=apply_url,
            phone=phone,
            whatsapp=whatsapp,
            provenance="founder_or_named_linkedin",
            email_status="NOT_FOUND",
        )
    if apply_url:
        return ContactVerdict(
            tier="C",
            apply_url=apply_url,
            provenance="apply_url_only",
            email_status="NOT_FOUND",
        )
    return ContactVerdict(tier="none", drop=False, provenance="no_contact_path")


def apply_contact_ladder_to_record(rec, contacts=None, founders=None, *, check_mx: bool = False):
    """Mutate OpportunityRecord with ladder result. Drops INFERRED emails."""
    from agent.models.opportunity import OpportunityRecord

    assert isinstance(rec, OpportunityRecord)
    verdict = ladder_from_contacts(
        contacts,
        source_url=rec.source_url,
        founders=founders,
        check_mx=check_mx,
    )
    if verdict.email:
        rec.contact_email = verdict.email
        rec.email_status = verdict.email_status
    elif rec.contact_email:
        st, prov = classify_email(rec.contact_email, check_mx=check_mx)
        if st == "INFERRED":
            rec.contact_email = ""
            rec.email_status = "NOT_FOUND"
            verdict.provenance = prov
        else:
            rec.email_status = st
    if verdict.phone:
        rec.contact_phone = verdict.phone
    elif not getattr(rec, "contact_phone", ""):
        maybe = extract_published_phone(rec.description or "", rec.evidence or "")
        if maybe:
            rec.contact_phone = maybe
    # WhatsApp: published only; leave empty/null when not found
    if verdict.whatsapp:
        rec.contact_whatsapp = verdict.whatsapp
    elif not getattr(rec, "contact_whatsapp", ""):
        wa = extract_published_whatsapp(
            rec.description or "",
            rec.evidence or "",
            rec.source_url or "",
            getattr(rec, "contact_phone", "") or "",
        )
        # Only promote phone → WhatsApp when text explicitly mentions WhatsApp
        blob = f"{rec.description or ''} {rec.evidence or ''}"
        if wa:
            rec.contact_whatsapp = wa
        elif re.search(r"(?i)whats?\s*app", blob) and getattr(rec, "contact_phone", ""):
            maybe_wa = normalize_whatsapp(rec.contact_phone)
            if maybe_wa:
                rec.contact_whatsapp = maybe_wa
        else:
            rec.contact_whatsapp = ""
    if verdict.linkedin_url and not rec.linkedin_url:
        rec.linkedin_url = verdict.linkedin_url
    if verdict.provenance:
        note = f"contact_tier={verdict.tier}; {verdict.provenance}"
        if rec.evidence:
            if "contact_tier=" not in rec.evidence:
                rec.evidence = f"{rec.evidence} | {note}"[:800]
        else:
            rec.evidence = note
    # Store tier in next_action hint if empty
    if not rec.next_action and verdict.tier in ("A", "B", "C"):
        rec.next_action = f"contact_tier_{verdict.tier}"
    return verdict
