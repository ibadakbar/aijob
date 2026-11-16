"""Shared interface for lead source adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from ..model import Lead, SearchCriteria


@dataclass
class SourceMeta:
    name: str
    official_api: bool
    notes: str = ""
    implemented: bool = True


@dataclass
class FetchResult:
    leads: list[Lead] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)


class LeadSourceAdapter(ABC):
    meta: SourceMeta

    @abstractmethod
    def fetch(self, criteria: SearchCriteria, **kwargs: Any) -> FetchResult:
        """Fetch and normalize leads. Never raise on per-item parse errors."""


class StubAdapter(LeadSourceAdapter):
    """Placeholder for sources without a verified permitted feed."""

    def __init__(self, meta: SourceMeta):
        self.meta = meta

    def fetch(self, criteria: SearchCriteria, **kwargs: Any) -> FetchResult:
        return FetchResult(
            leads=[],
            errors=[],
            meta={
                "stub": True,
                "implemented": False,
                "reason": self.meta.notes,
            },
        )
