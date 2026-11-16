"""Source adapters. Import registry of live + stub adapters."""

from .arbeitnow import ArbeitnowSource
from .ashby import AshbySource
from .base import SourceAdapter
from .greenhouse import GreenhouseSource
from .lever import LeverSource
from .stubs import EURES_STUB, RELOCATE_ME_STUB, WELLFOUND_STUB

LIVE_SOURCES = {
    "arbeitnow": ArbeitnowSource,
    "greenhouse": GreenhouseSource,
    "ashby": AshbySource,
    "lever": LeverSource,
}

STUB_SOURCES = {
    "relocate.me": RELOCATE_ME_STUB,
    "wellfound": WELLFOUND_STUB,
    "eures": EURES_STUB,
}

__all__ = [
    "SourceAdapter",
    "LIVE_SOURCES",
    "STUB_SOURCES",
    "ArbeitnowSource",
    "GreenhouseSource",
    "AshbySource",
    "LeverSource",
]
