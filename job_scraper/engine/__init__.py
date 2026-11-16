"""Visa / relocation job discovery engine (extends /scrape; does not replace portal CLIs)."""

from .model import NormalizedJob, SponsorshipResult
from .pipeline import discover

__all__ = ["NormalizedJob", "SponsorshipResult", "discover"]
