"""Cache company, domain, vacancy, and extraction results so research is not repeated."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Optional

from .dedupe import domain_of, fold_name, normalize_url
from .incremental import utcnow_iso
from .model import Lead
from .persist import atomic_write_json

TIER_EXTRACT = "extract"
TIER_RESEARCH = "research"


def own_domain(lead: Lead) -> str:
    """Employer-site host, when the listing URL is the company's own domain.

    Job-board hosts (the company name is not in the host) are not cached as
    the company domain, or every later vacancy on that board would look researched.
    """
    host = domain_of(lead.url)
    token = fold_name(lead.company)
    if token and token in fold_name(host):
        return host
    return ""


def model_tier_for(lead: Lead, *, company_cached: bool) -> str:
    """Cheap extraction for clear listings. Strong research only when the case is ambiguous.

    A company or domain already in the cache stays on the cheap path.
    """
    if company_cached:
        return TIER_EXTRACT
    if lead.intent != "EXPLICIT_DEMAND":
        return TIER_RESEARCH
    if not any((e.excerpt or e.summary) for e in lead.evidence):
        return TIER_RESEARCH
    return TIER_EXTRACT


class ResearchCache:
    def __init__(self, path: Path):
        self.path = path
        self.data = self._load(path)
        self.vacancy_hits = 0
        self.company_hits = 0
        self.ai_hits = 0

    @staticmethod
    def _load(path: Path) -> dict[str, Any]:
        empty: dict[str, Any] = {
            "version": 1,
            "vacancies": {},
            "companies": {},
            "domains": {},
            "ai": {},
        }
        if not path.is_file():
            return empty
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return empty
        if not isinstance(data, dict):
            return empty
        for key in ("vacancies", "companies", "domains", "ai"):
            if not isinstance(data.get(key), dict):
                data[key] = {}
        data.setdefault("version", 1)
        return data

    def save(self) -> None:
        atomic_write_json(self.path, self.data)

    def vacancy(self, url: str, content_hash: str) -> Optional[dict[str, Any]]:
        row = (self.data.get("vacancies") or {}).get(normalize_url(url))
        if not isinstance(row, dict):
            return None
        if row.get("hash") != content_hash:
            return None
        self.vacancy_hits += 1
        return row

    def remember_vacancy(self, lead: Lead, *, tier: str) -> None:
        url = normalize_url(lead.url)
        if not url:
            return
        self.data.setdefault("vacancies", {})[url] = {
            "hash": lead.content_hash,
            "lead_id": lead.id,
            "scores": lead.scores.to_dict() if lead.scores else None,
            "outreach": lead.outreach.to_dict() if lead.outreach else None,
            "confidence": lead.confidence,
            "status": lead.status,
            "model_tier": tier,
            "cached_at": utcnow_iso(),
        }

    def company_cached(self, lead: Lead) -> bool:
        company_key = fold_name(lead.company)
        domain = own_domain(lead)
        companies = self.data.get("companies") or {}
        domains = self.data.get("domains") or {}
        if company_key and company_key in companies:
            self.company_hits += 1
            return True
        if domain and domain in domains:
            self.company_hits += 1
            return True
        return False

    def remember_company(self, lead: Lead, *, tier: str) -> None:
        company_key = fold_name(lead.company)
        domain = own_domain(lead)
        stamp = utcnow_iso()
        if company_key:
            bucket = self.data.setdefault("companies", {}).setdefault(
                company_key,
                {"name": lead.company, "domains": [], "lead_ids": [], "tier": tier, "cached_at": stamp},
            )
            if domain and domain not in bucket["domains"]:
                bucket["domains"].append(domain)
            if lead.id not in bucket["lead_ids"]:
                bucket["lead_ids"].append(lead.id)
            bucket["tier"] = tier
            bucket["cached_at"] = stamp
        if domain:
            self.data.setdefault("domains", {})[domain] = {
                "company_key": company_key,
                "cached_at": stamp,
            }

    def cached_compute(
        self,
        *,
        task: str,
        tier: str,
        content_hash: str,
        compute: Callable[[], Any],
    ) -> tuple[Any, bool]:
        """Return a cached extraction/research result, computing it once on a miss."""
        key = f"{tier}:{task}:{content_hash}"
        found = (self.data.get("ai") or {}).get(key)
        if isinstance(found, dict) and "result" in found:
            self.ai_hits += 1
            return found["result"], True
        result = compute()
        self.data.setdefault("ai", {})[key] = {
            "tier": tier,
            "task": task,
            "result": result,
            "cached_at": utcnow_iso(),
        }
        return result, False
