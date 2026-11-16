"""Optional UK licensed-sponsor registry lookup → sponsor_company_only evidence.

The official CSV is published on GOV.UK under the Open Government Licence.
Download manually (or with a one-off fetch) into job_scraper/cache/uk_sponsors.csv.
This module never claims a vacancy offers sponsorship — only that the employer
appears on the Worker / Temporary Worker register.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Optional

CACHE = Path(__file__).resolve().parent.parent / "cache" / "uk_sponsors.csv"


def load_sponsor_names(path: Path | None = None) -> set[str]:
    p = path or CACHE
    if not p.exists():
        return set()
    names: set[str] = set()
    with p.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        # GOV.UK columns: Organisation Name, Town/City, County, Type & Rating, Route
        for row in reader:
            name = (row.get("Organisation Name") or row.get("organisation_name") or "").strip()
            if name:
                names.add(_fold(name))
    return names


def _fold(name: str) -> str:
    return "".join(ch for ch in name.lower() if ch.isalnum())


def company_on_uk_register(company: str, names: Optional[set[str]] = None) -> bool:
    registry = names if names is not None else load_sponsor_names()
    if not registry:
        return False
    folded = _fold(company)
    if folded in registry:
        return True
    # Soft contains match for short company tokens (min length guard)
    if len(folded) < 5:
        return False
    return any(folded in n or n in folded for n in registry if abs(len(n) - len(folded)) < 8)
