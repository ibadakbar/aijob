"""Stub adapters for high-interest sources without a verified permitted feed."""

from .base import SourceMeta, StubAdapter

RELOCATE_ME_STUB = StubAdapter(
    SourceMeta(
        name="relocate.me",
        official_api=False,
        implemented=False,
        notes=(
            "Relocation-focused board; no verified public job API as of 2026-10-27. "
            "Do not HTML-scrape until ToS/robots and a stable feed are confirmed."
        ),
    )
)

WELLFOUND_STUB = StubAdapter(
    SourceMeta(
        name="wellfound",
        official_api=False,
        implemented=False,
        notes="No stable unauthenticated public board API verified; auth/anti-bot common.",
    )
)

EURES_STUB = StubAdapter(
    SourceMeta(
        name="eures",
        official_api=False,
        implemented=False,
        notes="EU official portal; programmatic access not verified for this project — stub only.",
    )
)
