"""Lead source adapters."""

from .arbeitnow_leads import ArbeitnowLeadsSource
from .ats_leads import AshbyLeadsSource, GreenhouseLeadsSource, LeverLeadsSource
from .base import FetchResult, LeadSourceAdapter, SourceMeta, StubAdapter
from .fixture import FixtureSource
from .remotive import RemotiveSource
from .stubs import STUB_SOURCES
from .yc_companies import YCCompaniesSource

LIVE_SOURCES: dict[str, type[LeadSourceAdapter]] = {
    "remotive": RemotiveSource,
    "arbeitnow": ArbeitnowLeadsSource,
    "greenhouse": GreenhouseLeadsSource,
    "ashby": AshbyLeadsSource,
    "lever": LeverLeadsSource,
    "ycombinator": YCCompaniesSource,
    "yc": YCCompaniesSource,  # alias
    "fixture": FixtureSource,
}


def register_source(name: str, adapter_cls: type[LeadSourceAdapter]) -> None:
    """Register a lead source without editing the discovery pipeline.

    A job board, company career feed, or other source is usable as soon as its
    adapter subclass is registered under a unique name.
    """
    key = name.lower().strip()
    if not key:
        raise ValueError("source name is required")
    LIVE_SOURCES[key] = adapter_cls


def unregister_source(name: str) -> None:
    LIVE_SOURCES.pop(name.lower().strip(), None)


def list_sources() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for name, cls in LIVE_SOURCES.items():
        meta = getattr(cls, "meta", None)
        rows.append(
            {
                "name": name,
                "implemented": True,
                "official_api": bool(getattr(meta, "official_api", False)),
                "notes": getattr(meta, "notes", ""),
            }
        )
    for name, stub in STUB_SOURCES.items():
        rows.append(
            {
                "name": name,
                "implemented": False,
                "official_api": False,
                "notes": stub.meta.notes,
            }
        )
    return rows


__all__ = [
    "LIVE_SOURCES",
    "STUB_SOURCES",
    "FetchResult",
    "LeadSourceAdapter",
    "SourceMeta",
    "StubAdapter",
    "RemotiveSource",
    "ArbeitnowLeadsSource",
    "GreenhouseLeadsSource",
    "AshbyLeadsSource",
    "LeverLeadsSource",
    "YCCompaniesSource",
    "FixtureSource",
    "register_source",
    "unregister_source",
    "list_sources",
]
