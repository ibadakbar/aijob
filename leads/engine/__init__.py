"""Lead discovery pipeline: criteria → sources → intent → score → persist → export."""

from .pipeline import discover_leads

__all__ = ["discover_leads"]
