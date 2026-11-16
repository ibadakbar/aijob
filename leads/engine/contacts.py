"""Discover and label publicly published contact channels — never fabricate."""

from __future__ import annotations

import re
import socket
import subprocess
from datetime import date
from typing import Optional
from urllib.parse import urlparse

from .model import ContactChannel, ContactVerification
from .sanitize import sanitize_text

# Deliberately strict: require a plausible TLD and reject obvious placeholders.
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
    "you",
    "someone",
    "firstname",
    "lastname",
    "yourname",
    "username",
    "noreply",
    "no-reply",
    "donotreply",
}

_FAKE_DOMAINS = {
    "example.com",
    "example.org",
    "example.net",
    "email.com",
    "domain.com",
    "company.com",
    "sentry.io",
    "wixpress.com",
    "googleapis.com",
    "schema.org",
    "placeholder.local",
}


def extract_published_emails(text: str) -> list[str]:
    """Return emails that literally appear in text, filtering placeholders."""
    found: list[str] = []
    for match in _EMAIL_RE.finditer(sanitize_text(text, max_len=20000)):
        email = match.group(1).strip().lower()
        local, _, domain = email.partition("@")
        if not local or not domain:
            continue
        if local.split("+")[0] in _FAKE_LOCAL:
            continue
        if domain in _FAKE_DOMAINS or domain.endswith(".example") or domain == "example":
            continue
        # RFC 2606 / reserved names often used in docs — keep .test for fixtures
        if domain.endswith(".invalid") or domain.endswith(".localhost"):
            continue
        if email not in found:
            found.append(email)
    return found


def _domain_from_url(url: str) -> Optional[str]:
    try:
        host = urlparse(url).hostname
    except ValueError:
        return None
    if not host:
        return None
    host = host.lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def domain_has_mx(domain: str, *, timeout: float = 3.0) -> Optional[bool]:
    """Best-effort MX / A lookup. None = could not check. True ≠ mailbox exists."""
    domain = (domain or "").strip().lower().rstrip(".")
    if not domain or "." not in domain:
        return None
    # Prefer nslookup (available on Windows and most Unix).
    try:
        proc = subprocess.run(
            ["nslookup", "-type=MX", domain],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        lower = out.lower()
        if "mail exchanger" in lower or "mx preference" in lower:
            return True
        if "non-existent domain" in lower or "can't find" in lower:
            # Fall through to A-record probe — some small sites have A only.
            pass
    except (OSError, subprocess.TimeoutExpired):
        pass
    try:
        socket.setdefaulttimeout(timeout)
        socket.getaddrinfo(domain, 25)
        return True
    except OSError:
        return False


def build_contacts_from_listing(
    *,
    description: str,
    listing_url: str,
    company: str = "",
    check_mx: bool = True,
) -> list[ContactChannel]:
    """Build contact channels from published listing text + application URL.

    Never invents emails. Application page is always recorded as a legitimate channel.
    """
    today = date.today().isoformat()
    contacts: list[ContactChannel] = []
    emails = extract_published_emails(description)

    listing_host = _domain_from_url(listing_url)
    for email in emails:
        domain = email.split("@", 1)[1]
        status: ContactVerification = "published_on_official_source"
        method = "literal_email_in_source_text"
        notes = "Published in listing/description text; mailbox existence not proven."
        if check_mx:
            mx = domain_has_mx(domain)
            if mx is True:
                # Upgrade label carefully: MX proves domain accepts mail routing,
                # not that this mailbox exists.
                status = "domain_mx_present"
                method = "literal_email_in_source_text+mx_or_a_lookup"
                notes = (
                    "Email published in source text; domain has MX/A records. "
                    "This does not confirm the mailbox exists or accepts mail."
                )
            elif mx is False:
                status = "unverified"
                method = "literal_email_in_source_text+mx_lookup_failed"
                notes = "Email appeared in text but domain MX/A lookup failed."
            else:
                status = "published_on_official_source"
                notes += " MX check unavailable on this host."
        # Prefer company-looking domains when listing is on a job board
        if listing_host and domain == listing_host:
            notes += " Domain matches listing host."
        contacts.append(
            ContactChannel(
                channel_type="email",
                value=email,
                name=None,
                title=None,
                source_url=listing_url,
                verification_status=status,
                verification_method=method,
                date_checked=today,
                notes=notes,
            )
        )

    if listing_url:
        contacts.append(
            ContactChannel(
                channel_type="application_page",
                value=listing_url,
                name=company or None,
                title="Application / project page",
                source_url=listing_url,
                verification_status="published_on_official_source",
                verification_method="listing_url_from_source_api",
                date_checked=today,
                notes="Official listing/application URL from the source feed.",
            )
        )

    if not contacts:
        contacts.append(
            ContactChannel(
                channel_type="unknown",
                value="",
                source_url=listing_url or "",
                verification_status="unknown",
                verification_method="no_public_contact_found",
                date_checked=today,
                notes="No published email found; do not invent one. Use the listing URL or company contact form after manual research.",
            )
        )
    return contacts
