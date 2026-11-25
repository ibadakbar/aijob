"""Quality gates: freshness, Path A/B, contact ladder, hireability."""

from .pipeline import GateResult, apply_quality_gates

__all__ = ["GateResult", "apply_quality_gates"]
