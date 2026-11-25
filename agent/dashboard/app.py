"""Streamlit dashboard — reads Excel; does not run the agent loop."""

from __future__ import annotations

import subprocess
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import importlib

# Drop cached agent.* so Streamlit soft-reruns pick up new symbols from disk.
for _mod_name in list(sys.modules):
    if _mod_name == "agent" or _mod_name.startswith("agent."):
        del sys.modules[_mod_name]
importlib.invalidate_caches()

from agent.models.opportunity import OpportunityRecord, format_12h  # noqa: E402
from agent.scheduler.runner import (  # noqa: E402
    is_agent_alive,
    live_status,
    load_control,
    load_state,
    request_stop_agent,
    set_control,
    start_agent_process,
)
from agent.storage.excel_store import ExcelStore  # noqa: E402

st.set_page_config(page_title="Opportunity Agent", layout="wide", page_icon="🛰️")


def _agent_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(ROOT / "agent" / "cli.py"), *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )


def _parse_day(value: str) -> Optional[date]:
    if not value:
        return None
    raw = str(value).strip()
    # Prefer full datetime (incl. 12h AM/PM), then date-only
    for fmt in (
        "%Y-%m-%d %I:%M:%S %p",
        "%Y-%m-%d %I:%M %p",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d-%m-%Y",
    ):
        try:
            chunk = raw[:22].strip() if "%p" in fmt else raw[:19].replace("T", " ")
            if fmt.endswith("%Y-%m-%d") or fmt in ("%Y/%m/%d", "%d-%m-%Y"):
                chunk = raw[:10]
            return datetime.strptime(chunk, fmt).date()
        except ValueError:
            continue
    # Fallback: first 10 chars as YYYY-MM-DD
    try:
        return datetime.strptime(raw[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def _row_day(r: OpportunityRecord, field: str) -> Optional[date]:
    if field == "Posted":
        return _parse_day(r.posted_date) or _parse_day(r.discovered_date)
    return _parse_day(r.discovered_date) or _parse_day(r.posted_date)


def _date_bounds(rows: list[OpportunityRecord], field: str) -> tuple[date, date]:
    days = [d for r in rows if (d := _row_day(r, field)) is not None]
    today = date.today()
    if not days:
        return today - timedelta(days=7), today
    return min(days), max(days)


def render_date_filter(
    rows: list[OpportunityRecord],
    *,
    key_prefix: str,
) -> tuple[list[OpportunityRecord], str]:
    """Day-by-day / range filter. Returns (filtered_rows, caption)."""
    field = st.radio(
        "Date field",
        ["Discovered", "Posted"],
        horizontal=True,
        key=f"{key_prefix}_date_field",
    )
    lo, hi = _date_bounds(rows, field)
    today = date.today()
    # Clamp defaults into available range
    default_day = min(max(today, lo), hi)

    mode = st.radio(
        "Date filter",
        ["All dates", "Today", "Single day", "Date range"],
        horizontal=True,
        key=f"{key_prefix}_date_mode",
        index=2 if lo == hi else 0,
    )

    start: Optional[date] = None
    end: Optional[date] = None
    if mode == "Today":
        start = end = today
    elif mode == "Single day":
        c1, c2, c3 = st.columns([1, 2, 1])
        with c1:
            if st.button("← Prev", key=f"{key_prefix}_prev"):
                st.session_state[f"{key_prefix}_day"] = (
                    _parse_day(str(st.session_state.get(f"{key_prefix}_day", default_day)))
                    or default_day
                ) - timedelta(days=1)
        with c3:
            if st.button("Next →", key=f"{key_prefix}_next"):
                st.session_state[f"{key_prefix}_day"] = (
                    _parse_day(str(st.session_state.get(f"{key_prefix}_day", default_day)))
                    or default_day
                ) + timedelta(days=1)
        if f"{key_prefix}_day" not in st.session_state:
            st.session_state[f"{key_prefix}_day"] = default_day
        # Keep picker in bounds when possible
        cur = st.session_state[f"{key_prefix}_day"]
        if isinstance(cur, str):
            cur = _parse_day(cur) or default_day
        if cur < lo:
            cur = lo
        if cur > hi:
            cur = hi
        st.session_state[f"{key_prefix}_day"] = cur
        with c2:
            picked = st.date_input(
                "Day",
                value=cur,
                min_value=lo,
                max_value=hi,
                key=f"{key_prefix}_day_picker",
            )
        if isinstance(picked, tuple):
            picked = picked[0] if picked else cur
        st.session_state[f"{key_prefix}_day"] = picked
        start = end = picked
    elif mode == "Date range":
        rng = st.date_input(
            "From → To",
            value=(lo, hi),
            min_value=lo,
            max_value=hi,
            key=f"{key_prefix}_range",
        )
        if isinstance(rng, tuple) and len(rng) == 2:
            start, end = rng[0], rng[1]
        elif isinstance(rng, date):
            start = end = rng

    if mode == "All dates" or start is None or end is None:
        return rows, "all dates"

    if start > end:
        start, end = end, start

    filtered: list[OpportunityRecord] = []
    for r in rows:
        d = _row_day(r, field)
        if d is None:
            continue  # undated hidden when a date filter is active
        if start <= d <= end:
            filtered.append(r)

    if start == end:
        label = f"{field.lower()} = {start.isoformat()}"
    else:
        label = f"{field.lower()} {start.isoformat()} → {end.isoformat()}"
    return filtered, label


def rows_to_table(rows: list[OpportunityRecord]) -> list[dict[str, Any]]:
    data = []
    for r in sorted(rows, key=lambda x: (-x.opportunity_score, x.company or "")):
        data.append(
            {
                "Score": r.opportunity_score,
                "Grade": r.grade,
                "Type": r.opportunity_type,
                "Company": r.company,
                "Title": r.role_or_title,
                "Path": r.path,
                "Remote": r.remote_type,
                "Visa": r.visa_sponsorship,
                "Email": r.contact_email,
                "Phone": getattr(r, "contact_phone", "") or "",
                "LinkedIn": r.linkedin_url,
                "Intent": r.intent_classification,
                "Source": r.source_name,
                "URL": r.source_url,
                "Status": r.status,
                "Discovered": format_12h(r.discovered_date),
                "Posted": format_12h(r.posted_date) if r.posted_date else "",
            }
        )
    return data


store = ExcelStore()
store.ensure_workbook()

st.title("Opportunity Discovery Agent")
st.caption("Excel-only persistence · dashboard does not own the background worker")

_HIDE_EXPIRED = frozenset({"expired", "closed", "rejected", "withdrawn"})

page = st.sidebar.radio(
    "Pages",
    [
        "Overview",
        "All Opportunities",
        "Jobs",
        "Clients",
        "Contracts & Freelance",
        "Founders & Clients",
        "Recruiters",
        "Agencies",
        "Companies",
        "Contacts",
        "Source Performance",
        "Search Configuration",
        "Logs",
        "Settings",
    ],
)
hide_expired = st.sidebar.checkbox(
    "Hide expired / closed (>3 months)",
    value=True,
    help="Listings older than 3 months are auto-marked expired and hidden by default.",
)


def _visible_rows(rows: list[OpportunityRecord]) -> list[OpportunityRecord]:
    if not hide_expired:
        return rows
    return [r for r in rows if (r.status or "").strip().lower() not in _HIDE_EXPIRED]

# Sidebar controls — Start launches a detached worker that survives Streamlit reruns
# (search / filters / page changes do NOT stop the agent).
c1, c2, c3, c4 = st.sidebar.columns(4)
if c1.button("Start", help="Launch background agent; keeps running until you press Stop"):
    result = start_agent_process()
    if result.get("already_running"):
        st.sidebar.success(f"Agent already running (pid {result.get('pid')})")
    else:
        st.sidebar.success(f"Agent started (pid {result.get('pid')}) — keeps running until Stop")
if c2.button("Pause"):
    if is_agent_alive():
        set_control("pause")
        st.sidebar.warning("Agent paused (still alive — Resume to continue)")
    else:
        st.sidebar.error("Agent not running — press Start first")
if c3.button("Resume"):
    if is_agent_alive():
        set_control("run")
        st.sidebar.success("Agent resumed")
    else:
        result = start_agent_process()
        st.sidebar.success(f"Agent was stopped — restarted (pid {result.get('pid')})")
if c4.button("Stop", help="Manually stop the background agent"):
    result = request_stop_agent(force=True)
    st.sidebar.info("Agent stopped" if result.get("stopped") else f"Stop signaled: {result}")

if st.sidebar.button("Run discovery now"):
    if not is_agent_alive():
        start_agent_process()
        time.sleep(1.5)
    set_control("run_now")
    st.sidebar.success("Discovery pass signaled (agent keeps running)")

if st.sidebar.button("Backup workbook"):
    path = store.backup("dashboard")
    st.sidebar.success(f"Backup: {path.name}")

if st.sidebar.button("Open data folder"):
    st.sidebar.code(str(ROOT / "data"))

stats = store.get_statistics()
state = load_state()
control = load_control()
agent_live = live_status()

if page == "Overview":
    st.subheader("Live metrics (from Excel)")
    cols = st.columns(5)
    cols[0].metric("Total", stats.get("total_opportunities", 0))
    cols[1].metric("New today", stats.get("new_today", 0))
    cols[2].metric("Grade A", stats.get("grade_a", 0))
    cols[3].metric("Jobs", stats.get("jobs", 0))
    cols[4].metric("Contracts", stats.get("contracts", 0))
    cols2 = st.columns(5)
    cols2[0].metric("Clients", stats.get("clients", 0))
    cols2[1].metric("Founders", stats.get("founders", 0))
    cols2[2].metric("Recruiters", stats.get("recruiters", 0))
    cols2[3].metric("Emails / phones", f"{stats.get('public_emails', 0)} / {stats.get('public_phones', 0)}")
    cols2[4].metric("Agent", agent_live.get("status", "unknown"))
    st.write("Last discovery:", stats.get("last_discovery") or "—")
    st.write("Last Excel update:", stats.get("last_excel_update") or "—")
    st.write(
        "Agent process:",
        f"pid {agent_live.get('pid')}" if agent_live.get("alive") else "not running",
        "· Control:",
        control,
    )
    if agent_live.get("alive"):
        st.success(
            "Agent is running in the background. Searching / filtering the table "
            "only refreshes this page — it will **not** stop the agent. Press **Stop** to end it."
        )
    else:
        st.warning(
            "Agent is stopped. Press **Start** in the sidebar — it stays up until you press **Stop** "
            "(PC must stay on / awake for continuous discovery)."
        )

    st.subheader("Excel opportunities (live)")
    ov_rows = _visible_rows(store.load_all_opportunities())
    ov_rows, date_label = render_date_filter(ov_rows, key_prefix="overview")
    ov_q = st.text_input("Filter company / title", key="overview_search")
    ov_min = st.slider("Min score", 0, 100, 0, key="overview_min_score")
    filtered = []
    for r in ov_rows:
        if r.opportunity_score < ov_min:
            continue
        blob = f"{r.company} {r.role_or_title}".lower()
        if ov_q and ov_q.lower() not in blob:
            continue
        filtered.append(r)
    ov_data = rows_to_table(filtered)
    st.dataframe(ov_data, use_container_width=True, height=480)
    st.caption(
        f"{len(ov_data)} rows · {date_label} · workbook {store.path}"
    )

elif page == "Clients":
    st.subheader("Clients — buyers needing your stack")
    st.caption(
        "Worldwide client/project demand matched to your profile (React / Next / TS / full-stack). "
        "Email & phone only when published on a public source — never invented. "
        "Run: `python agent\\cli.py hunt-clients`"
    )
    rows = [
        r
        for r in _visible_rows(store.load_all_opportunities())
        if r.opportunity_type.lower() == "client"
    ]
    rows, date_label = render_date_filter(rows, key_prefix="clients")
    f1, f2, f3 = st.columns(3)
    only_email = f1.checkbox("Has email", value=False, key="clients_email")
    only_phone = f2.checkbox("Has phone", value=False, key="clients_phone")
    only_contact = f3.checkbox("Any contact (email/phone/LinkedIn)", value=False, key="clients_any")
    min_score = st.slider("Min score", 0, 100, 0, key="clients_min")
    grade = st.multiselect(
        "Grade", ["A", "B", "C", "Low"], default=["A", "B", "C", "Low"], key="clients_grade"
    )
    q = st.text_input("Search company / need", key="clients_q")
    filtered = []
    for r in rows:
        if r.opportunity_score < min_score:
            continue
        if r.grade and r.grade not in grade:
            continue
        if only_email and not r.contact_email:
            continue
        if only_phone and not getattr(r, "contact_phone", ""):
            continue
        if only_contact and not (
            r.contact_email or getattr(r, "contact_phone", "") or r.linkedin_url
        ):
            continue
        blob = f"{r.company} {r.role_or_title} {r.description}".lower()
        if q and q.lower() not in blob:
            continue
        filtered.append(r)
    client_view = []
    for r in sorted(filtered, key=lambda x: (-x.opportunity_score, x.company or "")):
        client_view.append(
            {
                "Score": r.opportunity_score,
                "Grade": r.grade,
                "Company": r.company,
                "Need / Title": r.role_or_title,
                "Email": r.contact_email,
                "Phone": getattr(r, "contact_phone", "") or "",
                "LinkedIn": r.linkedin_url,
                "Budget": r.salary_or_budget,
                "Location": r.location,
                "Remote": r.remote_type,
                "Intent": r.intent_classification,
                "Source": r.source_name,
                "URL": r.source_url,
                "Status": r.status,
                "Discovered": format_12h(r.discovered_date),
            }
        )
    st.dataframe(client_view, use_container_width=True, height=520)
    with_email = sum(1 for r in filtered if r.contact_email)
    with_phone = sum(1 for r in filtered if getattr(r, "contact_phone", ""))
    st.caption(
        f"{len(client_view)} clients · email {with_email} · phone {with_phone} · "
        f"{date_label} · {store.path}"
    )
    if st.button("Hunt clients now", key="clients_hunt_btn"):
        from agent.discovery.clients.hunt import run_client_discovery

        with st.spinner("Hunting clients (leads radar + store)…"):
            result = run_client_discovery(store, discover=True)
        st.success(
            f"Fetched {result.get('fetched')} · kept {result.get('kept')} · "
            f"added {result.get('added')} · email {result.get('with_email')} · "
            f"phone {result.get('with_phone')}"
        )
        st.json(result.get("gate") or {})

elif page in (
    "All Opportunities",
    "Jobs",
    "Contracts & Freelance",
    "Founders & Clients",
    "Recruiters",
    "Agencies",
    "Companies",
):
    rows = _visible_rows(store.load_all_opportunities())
    type_filter = {
        "Jobs": {"job"},
        "Contracts & Freelance": {"contract", "freelance"},
        "Founders & Clients": {"founder"},
        "Recruiters": {"recruiter"},
        "Agencies": {"agency"},
        "Companies": {"company"},
    }.get(page)
    if type_filter:
        rows = [r for r in rows if r.opportunity_type.lower() in type_filter]

    rows, date_label = render_date_filter(rows, key_prefix=page.replace(" ", "_").lower())
    min_score = st.slider("Min score", 0, 100, 0)
    grade = st.multiselect("Grade", ["A", "B", "C", "Low"], default=["A", "B", "C", "Low"])
    q = st.text_input("Search company / title")
    filtered = []
    for r in rows:
        if r.opportunity_score < min_score:
            continue
        if r.grade and r.grade not in grade:
            continue
        blob = f"{r.company} {r.role_or_title}".lower()
        if q and q.lower() not in blob:
            continue
        filtered.append(r)
    data = rows_to_table(filtered)
    st.dataframe(data, use_container_width=True, height=520)
    st.caption(f"{len(data)} rows · {date_label} · workbook {store.path}")

elif page == "Contacts":
    rows = [r for r in _visible_rows(store.load_all_opportunities()) if r.contact_email]
    rows, date_label = render_date_filter(rows, key_prefix="contacts")
    st.dataframe(
        [
            {
                "Company": r.company,
                "Name": r.contact_name,
                "Position": r.contact_position,
                "Email": r.contact_email,
                "Status": r.email_status,
                "LinkedIn": r.linkedin_url,
                "Source": r.source_url,
                "Discovered": format_12h(r.discovered_date),
            }
            for r in rows
        ],
        use_container_width=True,
    )
    st.caption(f"{len(rows)} contacts · {date_label}")

elif page == "Source Performance":
    st.write("See `Source Performance` sheet in the workbook for per-source runs.")
    st.code(str(store.path))

elif page == "Search Configuration":
    cfg = ROOT / "agent" / "config" / "default.yaml"
    st.code(cfg.read_text(encoding="utf-8") if cfg.exists() else "missing config", language="yaml")

elif page == "Logs":
    log_path = ROOT / "logs" / "agent.log"
    if log_path.exists():
        st.text(log_path.read_text(encoding="utf-8")[-8000:])
    else:
        st.write("No agent.log yet.")
    st.json({"state": state, "control": control})

elif page == "Settings":
    st.write("Workbook:", store.path)
    st.write("Backups:", ROOT / "backups")
    st.write("Existing `/scrape` and `/leads` workflows are unchanged.")
    st.write("Agent Excel store is additive and is the persistent opportunity SoT for the 24/7 worker.")
