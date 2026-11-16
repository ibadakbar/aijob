"""Shared interface for job source adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

from ..model import NormalizedJob


@dataclass
class SourceMeta:
    name: str
    official_api: bool
    notes: str = ""
    implemented: bool = True


@dataclass
class FetchResult:
    jobs: list[NormalizedJob] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)


class SourceAdapter(ABC):
    meta: SourceMeta

    @abstractmethod
    def fetch(self, **kwargs: Any) -> FetchResult:
        """Fetch and normalize jobs. Never raise on per-item parse errors."""


class StubAdapter(SourceAdapter):
    """Placeholder for sources without a verified permitted feed."""

    def __init__(self, meta: SourceMeta):
        self.meta = meta

    def fetch(self, **kwargs: Any) -> FetchResult:
        return FetchResult(
            jobs=[],
            errors=[],
            meta={
                "stub": True,
                "implemented": False,
                "reason": self.meta.notes,
            },
        )
