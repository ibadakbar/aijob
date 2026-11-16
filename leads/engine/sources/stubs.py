"""Documented stubs for sources that need auth, ToS review, or paid APIs."""

from .base import SourceMeta, StubAdapter

STUB_SOURCES = {
    "upwork": StubAdapter(
        SourceMeta(
            name="upwork",
            official_api=False,
            implemented=False,
            notes=(
                "Upwork project search requires authenticated API / ToS-compliant access. "
                "Not scraped. Enable only with official API credentials and user approval."
            ),
        )
    ),
    "contra": StubAdapter(
        SourceMeta(
            name="contra",
            official_api=False,
            implemented=False,
            notes="No verified public feed for automated search; agent may use WebSearch for public posts only.",
        )
    ),
    "wellfound": StubAdapter(
        SourceMeta(
            name="wellfound",
            official_api=False,
            implemented=False,
            notes="Same stub posture as job_scraper visa stubs — no permitted scrape.",
        )
    ),
    "linkedin_posts": StubAdapter(
        SourceMeta(
            name="linkedin_posts",
            official_api=False,
            implemented=False,
            notes=(
                "Do not scrape LinkedIn. Agent may use WebSearch snippets of public posts "
                "and record original URLs; never bypass login or CAPTCHA."
            ),
        )
    ),
}
