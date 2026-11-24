"""Hiring Cafe via optional Apify actor (AnshumanAtrey/hiringcafe-jobs-search).

No free bulk public API (legacy /api/search-jobs is locked). When ``APIFY_TOKEN``
is set, calls the Apify actor with visaSponsorship + remote filters.
Without a token, returns a clear skip meta (use JobSpy/RemoteOK instead).
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any

from ..http import UA
from ..model import NormalizedJob
from ..normalize import detect_country, detect_workplace, strip_html, title_matches_roles
from ..sponsorship import classify_sponsorship
from .base import FetchResult, SourceAdapter, SourceMeta

ACTOR = "anshumanatrey~hiringcafe-jobs-search"
RUN_URL = f"https://api.apify.com/v2/acts/{ACTOR}/runs"
DATASET_URL = "https://api.apify.com/v2/datasets/{id}/items"


def _apify_json(url: str, *, token: str, method: str = "GET", body: dict | None = None) -> Any:
    data = None
    headers = {"User-Agent": UA, "Accept": "application/json", "Authorization": f"Bearer {token}"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310
        return json.loads(resp.read().decode("utf-8"))


class HiringCafeSource(SourceAdapter):
    meta = SourceMeta(
        name="hiringcafe",
        official_api=False,
        notes="Optional Apify actor for Hiring Cafe visaSponsorship + remote search.",
    )

    def fetch(
        self,
        *,
        search_terms: list[str] | None = None,
        visa_sponsorship: bool = True,
        work_type: str = "remote",
        posted_within: str = "14 days",
        max_jobs: int = 40,
        role_filter: bool = True,
        wait_seconds: int = 90,
        **_: Any,
    ) -> FetchResult:
        token = (os.environ.get("APIFY_TOKEN") or os.environ.get("APIFY_API_TOKEN") or "").strip()
        if not token:
            return FetchResult(
                jobs=[],
                errors=[],
                meta={
                    "skipped": True,
                    "reason": "Set APIFY_TOKEN to enable Hiring Cafe (Apify actor). Free HC API is locked.",
                },
            )

        terms = search_terms or ["React TypeScript", "Full Stack Engineer", "Frontend Engineer Next.js"]
        payload = {
            "searchTerms": "\n".join(terms),
            "location": "Worldwide",
            "workType": work_type,
            "postedWithin": posted_within,
            "visaSponsorship": visa_sponsorship,
            "maxJobs": max_jobs,
            "includeDetails": True,
        }
        errors: list[str] = []
        try:
            run = _apify_json(f"{RUN_URL}?waitForFinish={wait_seconds}", token=token, method="POST", body=payload)
            data = run.get("data") if isinstance(run, dict) else None
            if not isinstance(data, dict):
                return FetchResult(jobs=[], errors=["hiringcafe: unexpected Apify run payload"], meta={})
            status = data.get("status")
            ds = data.get("defaultDatasetId")
            if status not in ("SUCCEEDED", "SUCCEEDED".lower()) and status != "SUCCEEDED":
                # Apify uses SUCCEEDED
                if status != "SUCCEEDED":
                    errors.append(f"hiringcafe: run status={status}")
            if not ds:
                return FetchResult(jobs=[], errors=errors or ["hiringcafe: no dataset"], meta={"status": status})
            items = _apify_json(f"{DATASET_URL.format(id=ds)}?clean=true&format=json", token=token)
        except urllib.error.HTTPError as exc:
            return FetchResult(jobs=[], errors=[f"hiringcafe Apify HTTP {exc.code}: {exc.reason}"], meta={})
        except Exception as exc:  # noqa: BLE001
            return FetchResult(jobs=[], errors=[f"hiringcafe: {exc}"], meta={})

        if not isinstance(items, list):
            return FetchResult(jobs=[], errors=["hiringcafe: dataset not a list"], meta={})

        jobs: list[NormalizedJob] = []
        for row in items:
            if not isinstance(row, dict):
                continue
            title = (row.get("title") or "").strip()
            if role_filter and not title_matches_roles(title):
                continue
            company = ""
            co = row.get("company")
            if isinstance(co, dict):
                company = (co.get("name") or "").strip()
            company = company or (row.get("companyName") or "Hiring Cafe").strip()
            url = (row.get("applyUrl") or row.get("apply_url") or row.get("url") or "").strip()
            if not title or not url:
                continue
            loc = row.get("location") or row.get("places") or "Worldwide"
            if isinstance(loc, list):
                loc = ", ".join(str(x) for x in loc)
            desc = strip_html(row.get("description") or row.get("descriptionText") or "")
            if row.get("visaSponsorship") or row.get("visa_sponsorship"):
                desc = (desc + "\n\nVisa sponsorship flagged on Hiring Cafe listing.").strip()
            if work_type == "remote" or "remote" in str(loc).lower() or str(row.get("workplaceType") or "").lower() == "remote":
                desc = (desc + "\n\nRemote / worldwide listing (Hiring Cafe).").strip()
            published = None
            for key in ("postedAt", "posted_at", "datePosted", "publishedAt"):
                val = row.get(key)
                if isinstance(val, str) and len(val) >= 10:
                    published = val[:10]
                    break
            workplace = detect_workplace(str(loc), desc, explicit="remote" if work_type == "remote" else None)
            country = detect_country(str(loc), desc)
            sponsorship = classify_sponsorship(desc, source_url=url)
            # Prefer verified when HC visa flag is true
            if (row.get("visaSponsorship") or row.get("visa_sponsorship")) and sponsorship.classification in (
                "unknown",
                "possible",
            ):
                from ..model import SponsorshipEvidence, SponsorshipResult

                sponsorship = SponsorshipResult(
                    classification="verified_in_listing",
                    confidence=0.85,
                    evidence=[
                        SponsorshipEvidence(
                            excerpt="Hiring Cafe visaSponsorship=true for this posting.",
                            source_url=url,
                            pattern="hiringcafe visaSponsorship filter",
                        )
                    ],
                    relocation_support=None,
                    notes="Hiring Cafe structured visa flag.",
                )
            jobs.append(
                NormalizedJob(
                    title=title,
                    company=company,
                    url=url,
                    source="hiringcafe",
                    location=str(loc),
                    country=country,
                    workplace=workplace,
                    published_date=published,
                    description=desc,
                    sponsorship=sponsorship,
                    status="open",
                    source_job_id=str(row.get("atsJobId") or row.get("id") or "") or None,
                    raw={"board": "hiringcafe", "ats": row.get("ats")},
                )
            )
            if len(jobs) >= max_jobs:
                break
        return FetchResult(jobs=jobs, errors=errors, meta={"actor": ACTOR, "count": len(jobs)})
