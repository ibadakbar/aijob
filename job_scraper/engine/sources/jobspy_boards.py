"""JobSpy board-volume bridge (Indeed / LinkedIn / Glassdoor / ZipRecruiter / …).

Requires optional dependency: ``pip install python-jobspy``
Inspired by speedyapply/JobSpy + kbwhodat/jobdrop coverage (consumer boards).

Depth model (two sweeps):
  1. Worldwide — Indeed multi-country, remote + visa/relocation language.
  2. Pakistan — Indeed PK, any workplace (onsite / hybrid / remote).
Plus one multi-site (Indeed+LinkedIn+Glassdoor) remote pass for LinkedIn/Glassdoor depth.
"""

from __future__ import annotations

from typing import Any

from ..model import NormalizedJob
from ..normalize import detect_country, detect_workplace, strip_html, title_matches_roles
from ..sponsorship import classify_sponsorship
from .base import FetchResult, SourceAdapter, SourceMeta

# Target-geo Indeed hosts for remote / visa / relocation depth (Ibad profile).
WORLDWIDE_INDEED_COUNTRIES = [
    "USA",
    "UK",
    "Canada",
    "Germany",
    "Netherlands",
    "Ireland",
    "Australia",
    "New Zealand",
    "UAE",
    "Switzerland",
    "Sweden",
    "Denmark",
    "Finland",
    "Saudi Arabia",
    "Qatar",
]

# Worldwide: remote OR sponsorship / relocation / hire-anywhere language.
WORLDWIDE_QUERIES = [
    'React OR Next.js OR "full stack" TypeScript remote',
    'React (Node OR TypeScript) ("visa sponsorship" OR relocation OR "work from anywhere" OR worldwide OR "hire globally")',
    '"frontend" OR "full stack" (React OR Next.js) (sponsorship OR relocation OR "from anywhere" OR EOR)',
]

# Pakistan: any workplace mode — no remote-only filter.
PAKISTAN_QUERIES = [
    'React OR Next.js OR "full stack" OR MERN OR TypeScript',
    '"software engineer" OR "web developer" OR "frontend" OR "fullstack" (React OR Node)',
]

PAKISTAN_LOCATIONS = ["Pakistan", "Karachi", "Lahore", "Islamabad"]


class JobSpyBoardsSource(SourceAdapter):
    meta = SourceMeta(
        name="jobspy",
        official_api=False,
        notes=(
            "JobSpy bridge: Indeed multi-country remote/visa + Pakistan any-mode + "
            "one LinkedIn/Glassdoor remote pass."
        ),
    )

    def fetch(
        self,
        *,
        sites: list[str] | None = None,
        queries: list[str] | None = None,
        location: str = "Remote",
        is_remote: bool = True,
        hours_old: int = 336,
        results_wanted: int = 25,
        country_indeed: str = "USA",
        role_filter: bool = True,
        max_jobs: int = 180,
        worldwide_countries: list[str] | None = None,
        pakistan: bool = True,
        **_: Any,
    ) -> FetchResult:
        try:
            from jobspy import scrape_jobs
        except ImportError:
            return FetchResult(
                jobs=[],
                errors=["jobspy not installed — pip install python-jobspy"],
                meta={"installed": False},
            )

        jobs: list[NormalizedJob] = []
        errors: list[str] = []
        seen_urls: set[str] = set()
        meta_runs: list[dict[str, Any]] = []

        def _ingest(
            df: Any,
            *,
            query: str,
            sweep: str,
            force_country: str | None = None,
            cap: int | None = None,
        ) -> None:
            limit = max_jobs if cap is None else min(cap, max_jobs)
            if df is None or getattr(df, "empty", True):
                return
            for _, row in df.iterrows():
                if len(jobs) >= limit:
                    return
                title = str(row.get("title") or "").strip()
                if role_filter and not title_matches_roles(title):
                    continue
                company = str(row.get("company") or "").strip() or "Unknown"
                url = str(row.get("job_url_direct") or row.get("job_url") or "").strip()
                if (
                    not title
                    or not url
                    or url.lower() in ("nan", "none", "null")
                    or url in seen_urls
                ):
                    continue
                seen_urls.add(url)
                loc = str(row.get("location") or "")
                desc = strip_html(str(row.get("description") or ""))
                emails = row.get("emails")
                if emails is not None and str(emails) not in ("", "nan", "None"):
                    desc = (desc + f"\n\nContact emails from board: {emails}").strip()
                salary = None
                try:
                    mn, mx = row.get("min_amount"), row.get("max_amount")
                    cur = row.get("currency") or ""
                    if mn == mn or mx == mx:  # not NaN
                        salary = f"{mn or ''}-{mx or ''} {cur}".strip(" -")
                except Exception:  # noqa: BLE001
                    salary = None
                published = None
                dp = row.get("date_posted")
                if dp is not None and str(dp) not in ("", "nan", "None"):
                    published = str(dp)[:10]
                remote_flag = row.get("is_remote")
                workplace = detect_workplace(
                    loc,
                    desc,
                    explicit="remote" if remote_flag in (True, "True", "true", 1) else None,
                )
                country = force_country or detect_country(loc, desc)
                sponsorship = classify_sponsorship(desc, source_url=url)
                site = str(row.get("site") or "jobspy")
                jobs.append(
                    NormalizedJob(
                        title=title,
                        company=company,
                        url=url,
                        source="jobspy",
                        location=loc,
                        country=country,
                        workplace=workplace,
                        employment_type=str(row.get("job_type") or "") or None,
                        published_date=published,
                        description=desc,
                        salary=salary,
                        sponsorship=sponsorship,
                        status="open",
                        source_job_id=str(row.get("id") or "") or None,
                        raw={
                            "board": site,
                            "query": query,
                            "emails": str(emails) if emails is not None else None,
                            "sweep": sweep,
                        },
                    )
                )

        def _run(
            *,
            site_list: list[str],
            query: str,
            loc: str,
            remote: bool,
            country: str,
            wanted: int,
            sweep: str,
            force_country: str | None = None,
            cap: int | None = None,
        ) -> None:
            limit = max_jobs if cap is None else min(cap, max_jobs)
            if len(jobs) >= limit:
                return
            try:
                df = scrape_jobs(
                    site_name=site_list,
                    search_term=query,
                    location=loc,
                    results_wanted=wanted,
                    hours_old=hours_old,
                    is_remote=remote,
                    country_indeed=country,
                    verbose=0,
                )
            except Exception as exc:  # noqa: BLE001
                errors.append(f"jobspy/{sweep}/{country}/{query[:36]}: {exc}")
                meta_runs.append(
                    {"sweep": sweep, "country": country, "query": query, "error": str(exc)}
                )
                return
            before = len(jobs)
            _ingest(
                df,
                query=query,
                sweep=sweep,
                force_country=force_country,
                cap=limit,
            )
            meta_runs.append(
                {
                    "sweep": sweep,
                    "country": country,
                    "query": query,
                    "added": len(jobs) - before,
                    "sites": site_list,
                }
            )

        ww_countries = worldwide_countries or WORLDWIDE_INDEED_COUNTRIES
        ww_queries = queries or WORLDWIDE_QUERIES
        multi_sites = sites or ["indeed", "linkedin", "glassdoor"]

        # Reserve room for Pakistan so WW volume cannot starve the local sweep.
        pk_budget = min(50, max(25, max_jobs // 4)) if pakistan else 0

        def _under(cap: int) -> bool:
            return len(jobs) < cap

        # --- Sweep 1 (first): Pakistan — any workplace (onsite / hybrid / remote) ---
        if pakistan:
            for loc in PAKISTAN_LOCATIONS:
                if not _under(pk_budget):
                    break
                for query in PAKISTAN_QUERIES:
                    if not _under(pk_budget):
                        break
                    _run(
                        site_list=["indeed"],
                        query=query,
                        loc=loc,
                        remote=False,
                        country="Pakistan",
                        wanted=max(results_wanted, 30),
                        sweep="pakistan_any_mode",
                        force_country="PK",
                        cap=pk_budget,
                    )

        # --- Sweep 2: Indeed-only multi-country remote / visa / relocation ---
        for country in ww_countries:
            if not _under(max_jobs):
                break
            for query in ww_queries:
                if not _under(max_jobs):
                    break
                _run(
                    site_list=["indeed"],
                    query=query,
                    loc=location or "Remote",
                    remote=True,
                    country=country,
                    wanted=results_wanted,
                    sweep="worldwide_remote_visa",
                    cap=max_jobs,
                )

        # --- Sweep 3: one multi-site remote pass (LinkedIn + Glassdoor + Indeed) ---
        for query in ww_queries[:2]:
            if not _under(max_jobs):
                break
            _run(
                site_list=multi_sites,
                query=query,
                loc=location or "Remote",
                remote=True,
                country=country_indeed or "USA",
                wanted=max(results_wanted, 30),
                sweep="multisite_remote",
                cap=max_jobs,
            )

        return FetchResult(
            jobs=jobs,
            errors=errors,
            meta={
                "installed": True,
                "sites": multi_sites,
                "worldwide_countries": ww_countries,
                "pakistan": pakistan,
                "queries_ww": len(ww_queries),
                "runs": len(meta_runs),
                "count": len(jobs),
            },
        )
