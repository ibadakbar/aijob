"""Excel-only persistent store (openpyxl). No databases."""

from __future__ import annotations

import shutil
import time
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable, Optional

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

try:
    from filelock import FileLock, Timeout
except ImportError:  # pragma: no cover
    FileLock = None  # type: ignore
    Timeout = Exception  # type: ignore

from agent.models.opportunity import (
    OpportunityRecord,
    discovered_from_source,
    grade_from_score,
    is_date_only_timestamp,
    make_opportunity_id,
    norm_key,
    now_discovered,
    now_iso,
    parse_datetime_flexible,
    to_discovered_str,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WORKBOOK = ROOT / "data" / "opportunities.xlsx"
DEFAULT_BACKUP_DIR = ROOT / "backups"
DEFAULT_LOCK = ROOT / "data" / "opportunities.lock"

SHEETS = [
    "All Opportunities",
    "Jobs",
    "Contracts & Freelance",
    "Clients",
    "Founders & Clients",
    "Recruiters",
    "Agencies",
    "Companies",
    "Contacts",
    "Source Performance",
    "Discovery History",
    "Search Queries",
    "Agent Statistics",
]

ALL_OPPORTUNITIES_COLUMNS = [
    "ID",
    "Opportunity Type",
    "Company",
    "Role / Project Title",
    "Description",
    "Required Skills",
    "Country",
    "Location",
    "Remote Type",
    "International Eligibility",
    "Visa Sponsorship",
    "Relocation Support",
    "Salary / Budget",
    "Currency",
    "Posted Date",
    "Discovered Date",
    "Last Verified",
    "Source Name",
    "Source URL",
    "Company Website",
    "Contact Name",
    "Contact Position",
    "Contact Email",
    "Contact Phone",
    "WhatsApp",
    "Email Status",
    "LinkedIn URL",
    "Intent Classification",
    "Evidence",
    "Opportunity Score",
    "Grade",
    "Status",
    "Next Action",
    "Notes",
    "Path",
    "Sponsorship Class",
    "Skill Score",
]

# Manual fields preserved on upsert
PRESERVE_ON_UPDATE = ("Status", "Notes", "Next Action")

TYPE_TO_SHEET = {
    "job": "Jobs",
    "contract": "Contracts & Freelance",
    "freelance": "Contracts & Freelance",
    "client": "Clients",
    "founder": "Founders & Clients",
    "recruiter": "Recruiters",
    "agency": "Agencies",
    "company": "Companies",
}

HEADER_FILL = PatternFill("solid", fgColor="1F4E79")
HEADER_FONT = Font(color="FFFFFF", bold=True)


def _row_to_record(headers: list[str], values: list[Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for h, v in zip(headers, values):
        key = {
            "ID": "id",
            "Opportunity Type": "opportunity_type",
            "Company": "company",
            "Role / Project Title": "role_or_title",
            "Description": "description",
            "Required Skills": "required_skills",
            "Country": "country",
            "Location": "location",
            "Remote Type": "remote_type",
            "International Eligibility": "international_eligibility",
            "Visa Sponsorship": "visa_sponsorship",
            "Relocation Support": "relocation_support",
            "Salary / Budget": "salary_or_budget",
            "Currency": "currency",
            "Posted Date": "posted_date",
            "Discovered Date": "discovered_date",
            "Last Verified": "last_verified",
            "Source Name": "source_name",
            "Source URL": "source_url",
            "Company Website": "company_website",
            "Contact Name": "contact_name",
            "Contact Position": "contact_position",
            "Contact Email": "contact_email",
            "Contact Phone": "contact_phone",
            "WhatsApp": "contact_whatsapp",
            "Email Status": "email_status",
            "LinkedIn URL": "linkedin_url",
            "Intent Classification": "intent_classification",
            "Evidence": "evidence",
            "Opportunity Score": "opportunity_score",
            "Grade": "grade",
            "Status": "status",
            "Next Action": "next_action",
            "Notes": "notes",
            "Path": "path",
            "Sponsorship Class": "sponsorship_class",
            "Skill Score": "skill_score",
        }.get(h)
        if key:
            if key in ("discovered_date", "posted_date", "last_verified") and v is not None and v != "":
                out[key] = to_discovered_str(v) if key == "discovered_date" else (
                    v.isoformat() if isinstance(v, (date, datetime)) else str(v).strip()
                )
            else:
                out[key] = v if v is not None else ""
    return out


def _record_to_values(rec: OpportunityRecord) -> list[Any]:
    d = rec.to_row()
    mapping = [
        "id",
        "opportunity_type",
        "company",
        "role_or_title",
        "description",
        "required_skills",
        "country",
        "location",
        "remote_type",
        "international_eligibility",
        "visa_sponsorship",
        "relocation_support",
        "salary_or_budget",
        "currency",
        "posted_date",
        "discovered_date",
        "last_verified",
        "source_name",
        "source_url",
        "company_website",
        "contact_name",
        "contact_position",
        "contact_email",
        "contact_phone",
        "contact_whatsapp",
        "email_status",
        "linkedin_url",
        "intent_classification",
        "evidence",
        "opportunity_score",
        "grade",
        "status",
        "next_action",
        "notes",
        "path",
        "sponsorship_class",
        "skill_score",
    ]
    return [d.get(k, "") for k in mapping]


class ExcelStore:
    """Thread-safe-ish Excel workbook store with atomic replace + backups."""

    def __init__(
        self,
        path: Path | None = None,
        backup_dir: Path | None = None,
        lock_path: Path | None = None,
    ) -> None:
        self.path = Path(path or DEFAULT_WORKBOOK)
        self.backup_dir = Path(backup_dir or DEFAULT_BACKUP_DIR)
        self.lock_path = Path(lock_path or DEFAULT_LOCK)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)

    def ensure_workbook(self) -> Path:
        if self.path.is_file():
            self._migrate_schema()
            return self.path
        wb = Workbook()
        # remove default
        default = wb.active
        wb.remove(default)
        for name in SHEETS:
            ws = wb.create_sheet(name)
            if name == "All Opportunities" or name in TYPE_TO_SHEET.values():
                ws.append(ALL_OPPORTUNITIES_COLUMNS)
                self._style_header(ws)
            elif name == "Contacts":
                ws.append(
                    [
                        "ID",
                        "Full Name",
                        "Position",
                        "Company",
                        "Email",
                        "Email Status",
                        "LinkedIn URL",
                        "Website",
                        "Source URL",
                        "Evidence",
                        "Discovered Date",
                        "Notes",
                    ]
                )
                self._style_header(ws)
            elif name == "Source Performance":
                ws.append(
                    [
                        "Source Name",
                        "Runs",
                        "Successes",
                        "Failures",
                        "New Records",
                        "Duplicates",
                        "Last Success",
                        "Last Error",
                        "Enabled",
                    ]
                )
                self._style_header(ws)
            elif name == "Discovery History":
                ws.append(
                    [
                        "Timestamp",
                        "Opportunity ID",
                        "Change Type",
                        "Summary",
                        "Source Name",
                    ]
                )
                self._style_header(ws)
            elif name == "Search Queries":
                ws.append(
                    [
                        "Query ID",
                        "Engine",
                        "Query Text",
                        "Last Run",
                        "Hits",
                        "New Hits",
                        "Enabled",
                        "Notes",
                    ]
                )
                self._style_header(ws)
            elif name == "Agent Statistics":
                ws.append(["Metric", "Value", "Updated"])
                self._style_header(ws)
                for metric, value in [
                    ("total_opportunities", 0),
                    ("new_today", 0),
                    ("grade_a", 0),
                    ("jobs", 0),
                    ("contracts", 0),
                    ("explicit_demands", 0),
                    ("founders", 0),
                    ("recruiters", 0),
                    ("public_emails", 0),
                    ("last_discovery", ""),
                    ("last_excel_update", ""),
                ]:
                    ws.append([metric, value, now_iso()])
            self._autosize(ws)
        self._atomic_save(wb)
        return self.path

    def _style_header(self, ws) -> None:
        for cell in ws[1]:
            cell.fill = HEADER_FILL
            cell.font = HEADER_FONT
            cell.alignment = Alignment(wrap_text=True, vertical="center")
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions

    def _migrate_schema(self) -> None:
        """Add Clients sheet + Contact Phone column to older workbooks."""
        lock = self._lock()
        if lock:
            with lock:
                self._migrate_schema_unlocked()
        else:
            self._migrate_schema_unlocked()

    def _migrate_schema_unlocked(self) -> None:
        wb = load_workbook(self.path)
        changed = False
        if "Clients" not in wb.sheetnames:
            ws = wb.create_sheet("Clients", 3)
            ws.append(ALL_OPPORTUNITIES_COLUMNS)
            self._style_header(ws)
            changed = True
        for name in ("All Opportunities", "Jobs", "Contracts & Freelance", "Clients", "Founders & Clients", "Recruiters", "Agencies", "Companies"):
            if name not in wb.sheetnames:
                continue
            ws = wb[name]
            headers = [c.value for c in ws[1]]
            if "Contact Phone" not in headers and "Contact Email" in headers:
                # Insert after Contact Email
                email_i = headers.index("Contact Email") + 1  # 1-based insert after
                ws.insert_cols(email_i + 1)
                ws.cell(1, email_i + 1).value = "Contact Phone"
                headers = [c.value for c in ws[1]]
                self._style_header(ws)
                changed = True
            if "WhatsApp" not in headers and "Contact Phone" in headers:
                phone_i = headers.index("Contact Phone") + 1
                ws.insert_cols(phone_i + 1)
                ws.cell(1, phone_i + 1).value = "WhatsApp"
                headers = [c.value for c in ws[1]]
                self._style_header(ws)
                changed = True
            elif not headers or headers[0] != "ID":
                continue
            elif headers != ALL_OPPORTUNITIES_COLUMNS and (
                "Contact Phone" not in headers or "WhatsApp" not in headers
            ):
                # Rebuild header row if column set drifted — append missing at end
                for col in ALL_OPPORTUNITIES_COLUMNS:
                    if col not in headers:
                        ws.cell(1, len(headers) + 1).value = col
                        headers.append(col)
                        changed = True
                self._style_header(ws)
        if self._backfill_discovered_times(wb):
            changed = True
        if changed:
            self._atomic_save(wb)
        else:
            wb.close()

    def _created_times_from_history(self, wb: Workbook) -> dict[str, str]:
        """Map opportunity id → first Discovery History 'created' timestamp (12h string)."""
        if "Discovery History" not in wb.sheetnames:
            return {}
        ws = wb["Discovery History"]
        headers = [c.value for c in ws[1]]
        try:
            ts_i = headers.index("Timestamp") + 1
            id_i = headers.index("Opportunity ID") + 1
            type_i = headers.index("Change Type") + 1
        except ValueError:
            return {}
        out: dict[str, str] = {}
        for r in range(2, ws.max_row + 1):
            oid = str(ws.cell(r, id_i).value or "").strip()
            if not oid or oid in out:
                continue
            change = str(ws.cell(r, type_i).value or "").strip().lower()
            if change and change != "created":
                continue
            stamped = to_discovered_str(ws.cell(r, ts_i).value)
            if stamped and not is_date_only_timestamp(stamped):
                out[oid] = stamped
        return out

    def _backfill_discovered_times(self, wb: Workbook) -> bool:
        """Replace date-only Discovered Date cells with real create times from history."""
        created = self._created_times_from_history(wb)
        if not created:
            return False
        changed = False
        sheet_names = [
            "All Opportunities",
            "Jobs",
            "Contracts & Freelance",
            "Clients",
            "Founders & Clients",
            "Recruiters",
            "Agencies",
            "Companies",
        ]
        for name in sheet_names:
            if name not in wb.sheetnames:
                continue
            ws = wb[name]
            headers = [c.value for c in ws[1]]
            if "ID" not in headers or "Discovered Date" not in headers:
                continue
            id_col = headers.index("ID") + 1
            disc_col = headers.index("Discovered Date") + 1
            for r in range(2, ws.max_row + 1):
                oid = str(ws.cell(r, id_col).value or "").strip()
                if not oid or oid not in created:
                    continue
                cell = ws.cell(r, disc_col)
                if not is_date_only_timestamp(cell.value):
                    continue
                cell.value = created[oid]
                cell.number_format = "@"  # keep as text so Excel won't drop the clock
                changed = True
        return changed

    def repair_found_at_times(self, *, backup: bool = True) -> dict[str, int]:
        """Fix bulk-identical Discovered Date stamps using leads_store checked/published dates.

        Rows that share one batch clock (e.g. all ``11:44:26 AM``) get the lead's
        ``checked_date`` / ``published_date`` so the table shows when each listing
        was actually found — not one shared import second.
        """
        import json
        from datetime import timedelta

        self.ensure_workbook()
        if backup:
            self.backup("pre_repair_found_at")
        leads_path = ROOT / "leads" / "store" / "leads_store.json"
        by_url: dict[str, dict] = {}
        by_pair: dict[tuple[str, str], dict] = {}
        if leads_path.is_file():
            try:
                payload = json.loads(leads_path.read_text(encoding="utf-8"))
                for lead in (payload.get("leads") or {}).values():
                    if not isinstance(lead, dict):
                        continue
                    url = str(lead.get("url") or lead.get("source_url") or "").rstrip("/")
                    company = str(lead.get("company") or lead.get("company_name") or "")
                    title = str(
                        lead.get("title") or lead.get("role") or lead.get("opportunity_title") or ""
                    )
                    if url:
                        by_url[url.casefold()] = lead
                    if company and title:
                        by_pair[(norm_key(company), norm_key(title))] = lead
            except (OSError, json.JSONDecodeError):
                pass

        lock = self._lock()
        if lock:
            with lock:
                return self._repair_found_at_unlocked(by_url, by_pair)
        return self._repair_found_at_unlocked(by_url, by_pair)

    def _repair_found_at_unlocked(
        self,
        by_url: dict[str, dict],
        by_pair: dict[tuple[str, str], dict],
    ) -> dict[str, int]:
        from datetime import timedelta
        from collections import Counter

        wb = load_workbook(self.path)
        sheet_names = [
            "All Opportunities",
            "Jobs",
            "Contracts & Freelance",
            "Clients",
            "Founders & Clients",
            "Recruiters",
            "Agencies",
        ]
        # Detect bulk-identical stamps on All Opportunities
        ws0 = wb["All Opportunities"]
        h0 = [c.value for c in ws0[1]]
        disc0 = h0.index("Discovered Date") + 1
        counts: Counter[str] = Counter()
        for r in range(2, ws0.max_row + 1):
            counts[str(ws0.cell(r, disc0).value or "")] += 1
        bulk_stamps = {s for s, n in counts.items() if s and n >= 10}

        fixed = 0
        posted_fixed = 0
        used_seconds: dict[str, int] = {}  # date-key -> next second offset

        for name in sheet_names:
            if name not in wb.sheetnames:
                continue
            ws = wb[name]
            headers = [c.value for c in ws[1]]
            if "Discovered Date" not in headers or "Company" not in headers:
                continue
            disc_col = headers.index("Discovered Date") + 1
            company_col = headers.index("Company") + 1
            title_col = headers.index("Role / Project Title") + 1
            url_col = headers.index("Source URL") + 1 if "Source URL" in headers else None
            posted_col = headers.index("Posted Date") + 1 if "Posted Date" in headers else None

            for r in range(2, ws.max_row + 1):
                current = str(ws.cell(r, disc_col).value or "")
                company = str(ws.cell(r, company_col).value or "")
                title = str(ws.cell(r, title_col).value or "")
                url = ""
                if url_col:
                    url = str(ws.cell(r, url_col).value or "").rstrip("/")
                lead = None
                if url and url.casefold() in by_url:
                    lead = by_url[url.casefold()]
                elif (norm_key(company), norm_key(title)) in by_pair:
                    lead = by_pair[(norm_key(company), norm_key(title))]

                needs_fix = (current in bulk_stamps) or is_date_only_timestamp(current)
                if not needs_fix and not lead:
                    continue

                new_stamp = ""
                if lead:
                    new_stamp = discovered_from_source(
                        lead.get("checked_date"),
                        lead.get("discovered_at"),
                        lead.get("found_at"),
                        lead.get("published_date"),
                        lead.get("posted_date"),
                        fallback_now=False,
                    )
                    if posted_col and not ws.cell(r, posted_col).value:
                        pub = str(lead.get("published_date") or lead.get("posted_date") or "")[:10]
                        if pub:
                            ws.cell(r, posted_col).value = pub
                            posted_fixed += 1
                if not new_stamp and current in bulk_stamps:
                    # No lead match: keep the bulk day but stagger seconds so rows differ
                    dt = parse_datetime_flexible(current) or datetime.now()
                    day_key = dt.strftime("%Y-%m-%d")
                    offset = used_seconds.get(day_key, 0)
                    used_seconds[day_key] = offset + 1
                    new_stamp = (dt.replace(hour=dt.hour, minute=dt.minute, second=0) + timedelta(seconds=offset)).strftime(
                        "%Y-%m-%d %I:%M:%S %p"
                    )
                elif new_stamp:
                    # Stagger identical date-only checked_dates into unique clocks
                    dt = parse_datetime_flexible(new_stamp)
                    if dt:
                        day_key = dt.strftime("%Y-%m-%d %H:%M")
                        offset = used_seconds.get(day_key, 0)
                        used_seconds[day_key] = offset + 1
                        if offset:
                            new_stamp = (dt + timedelta(seconds=offset)).strftime(
                                "%Y-%m-%d %I:%M:%S %p"
                            )

                if new_stamp and new_stamp != current and needs_fix:
                    cell = ws.cell(r, disc_col)
                    cell.value = new_stamp
                    cell.number_format = "@"
                    fixed += 1

        if fixed or posted_fixed:
            self._atomic_save(wb)
        else:
            wb.close()
        return {
            "fixed_discovered": fixed,
            "fixed_posted": posted_fixed,
            "bulk_stamps": len(bulk_stamps),
        }

    def _autosize(self, ws) -> None:
        for idx, col in enumerate(ws.columns, start=1):
            length = 12
            for cell in col[:50]:
                try:
                    length = max(length, min(48, len(str(cell.value or ""))))
                except Exception:
                    pass
            ws.column_dimensions[get_column_letter(idx)].width = length + 2

    def _lock(self):
        if FileLock is None:
            return None
        return FileLock(str(self.lock_path), timeout=60)

    def _atomic_save(self, wb: Workbook) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".xlsx.tmp")
        for attempt in range(1, 6):
            try:
                wb.save(tmp)
                # Windows: replace may fail if Excel has file open
                if self.path.exists():
                    try:
                        self.path.unlink()
                    except PermissionError:
                        time.sleep(0.4 * attempt)
                        continue
                tmp.replace(self.path)
                return
            except PermissionError:
                time.sleep(0.5 * attempt)
            except OSError:
                time.sleep(0.5 * attempt)
        # last resort: save alongside
        fallback = self.path.with_name(f"{self.path.stem}_write_fail_{int(time.time())}.xlsx")
        wb.save(fallback)
        raise PermissionError(
            f"Could not replace {self.path}; wrote fallback {fallback}. Close Excel and retry."
        )

    def backup(self, label: str = "auto") -> Path:
        self.ensure_workbook()
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = self.backup_dir / f"opportunities_{label}_{stamp}.xlsx"
        shutil.copy2(self.path, dest)
        return dest

    def load_all_opportunities(self) -> list[OpportunityRecord]:
        self.ensure_workbook()
        lock = self._lock()
        if lock:
            with lock:
                return self._load_all_unlocked()
        return self._load_all_unlocked()

    def _load_all_unlocked(self) -> list[OpportunityRecord]:
        wb = load_workbook(self.path, read_only=True, data_only=True)
        try:
            ws = wb["All Opportunities"]
            rows = list(ws.iter_rows(values_only=True))
        finally:
            wb.close()
        if not rows:
            return []
        headers = [str(h or "") for h in rows[0]]
        out: list[OpportunityRecord] = []
        for row in rows[1:]:
            if not row or not any(row):
                continue
            data = _row_to_record(headers, list(row))
            if not data.get("id"):
                continue
            out.append(OpportunityRecord.from_row(data))
        return out

    def upsert_opportunities(
        self,
        records: Iterable[OpportunityRecord],
        *,
        backup: bool = True,
        history_summary: str = "upsert batch",
    ) -> dict[str, int]:
        records = list(records)
        self.ensure_workbook()
        if backup and records:
            self.backup("pre_upsert")
        lock = self._lock()
        if lock:
            with lock:
                return self._upsert_unlocked(records, history_summary=history_summary)
        return self._upsert_unlocked(records, history_summary=history_summary)

    def _upsert_unlocked(
        self,
        records: list[OpportunityRecord],
        *,
        history_summary: str,
    ) -> dict[str, int]:
        wb = load_workbook(self.path)
        ws = wb["All Opportunities"]
        headers = [cell.value for cell in ws[1]]
        id_col = headers.index("ID") + 1
        # index existing by ID and by url/company+title
        by_id: dict[str, int] = {}
        by_url: dict[str, int] = {}
        by_pair: dict[tuple[str, str], int] = {}
        for r in range(2, ws.max_row + 1):
            rid = ws.cell(r, id_col).value
            if not rid:
                continue
            by_id[str(rid)] = r
            company = str(ws.cell(r, headers.index("Company") + 1).value or "")
            title = str(ws.cell(r, headers.index("Role / Project Title") + 1).value or "")
            url = str(ws.cell(r, headers.index("Source URL") + 1).value or "").rstrip("/")
            by_pair[(norm_key(company), norm_key(title))] = r
            if url:
                by_url[url] = r

        added = updated = skipped = 0
        hist = wb["Discovery History"]
        for rec in records:
            if not rec.id:
                rec.id = make_opportunity_id(
                    rec.opportunity_type, rec.company, rec.role_or_title, rec.source_url
                )
            if not rec.grade and rec.opportunity_score:
                rec.grade = grade_from_score(float(rec.opportunity_score))
            if not rec.last_verified:
                rec.last_verified = date.today().isoformat()

            row_idx = by_id.get(rec.id)
            if row_idx is None and rec.source_url:
                row_idx = by_url.get(rec.source_url.rstrip("/"))
            if row_idx is None:
                row_idx = by_pair.get((norm_key(rec.company), norm_key(rec.role_or_title)))

            # Keep the durable ID already stored for this URL/company+title
            if row_idx is not None:
                existing_id = str(ws.cell(row_idx, id_col).value or "")
                if existing_id:
                    rec.id = existing_id

            values = _record_to_values(rec)
            disc_idx = ALL_OPPORTUNITIES_COLUMNS.index("Discovered Date")
            disc_col = headers.index("Discovered Date") + 1
            if row_idx is None:
                # New listing → save current local time as Found at (shown in dashboard table)
                stamp = now_discovered()
                rec.discovered_date = stamp
                values[disc_idx] = stamp
                ws.append(values)
                row_idx = ws.max_row
                disc_cell = ws.cell(row_idx, disc_col)
                disc_cell.value = stamp
                disc_cell.number_format = "@"
                by_id[rec.id] = row_idx
                by_pair[(norm_key(rec.company), norm_key(rec.role_or_title))] = row_idx
                if rec.source_url:
                    by_url[rec.source_url.rstrip("/")] = row_idx
                hist.append([now_iso(), rec.id, "created", history_summary, rec.source_name])
                added += 1
            else:
                # preserve manual status/notes/next_action
                for col_name in PRESERVE_ON_UPDATE:
                    col = headers.index(col_name) + 1
                    existing = ws.cell(row_idx, col).value
                    if existing not in (None, ""):
                        idx = ALL_OPPORTUNITIES_COLUMNS.index(col_name)
                        values[idx] = existing
                # preserve discovered date (never overwrite a real clock with "now")
                existing_disc = ws.cell(row_idx, disc_col).value
                if existing_disc:
                    values[disc_idx] = to_discovered_str(existing_disc)
                elif not values[disc_idx] or is_date_only_timestamp(values[disc_idx]):
                    values[disc_idx] = now_discovered()
                else:
                    values[disc_idx] = to_discovered_str(values[disc_idx])
                for c, val in enumerate(values, start=1):
                    cell = ws.cell(row_idx, c)
                    cell.value = val
                    if c == disc_col:
                        cell.value = str(values[disc_idx])
                        cell.number_format = "@"
                hist.append([now_iso(), rec.id, "updated", history_summary, rec.source_name])
                updated += 1

            # type sheet mirror
            type_sheet = TYPE_TO_SHEET.get(rec.opportunity_type.lower())
            if type_sheet and type_sheet in wb.sheetnames:
                self._mirror_to_type_sheet(wb[type_sheet], rec, values)

            # contacts sheet when email present
            if rec.contact_email and "Contacts" in wb.sheetnames:
                self._upsert_contact(wb["Contacts"], rec)

        self._refresh_statistics(wb)
        self._atomic_save(wb)
        return {"added": added, "updated": updated, "skipped": skipped, "total": added + updated}

    def _mirror_to_type_sheet(self, ws, rec: OpportunityRecord, values: list[Any]) -> None:
        headers = [cell.value for cell in ws[1]]
        if not headers or headers[0] != "ID":
            return
        id_col = 1
        found = None
        for r in range(2, ws.max_row + 1):
            if str(ws.cell(r, id_col).value or "") == rec.id:
                found = r
                break
        if found is None:
            ws.append(values)
        else:
            for c, val in enumerate(values, start=1):
                # preserve notes/status on type sheets too
                col_name = ALL_OPPORTUNITIES_COLUMNS[c - 1] if c <= len(ALL_OPPORTUNITIES_COLUMNS) else ""
                if col_name in PRESERVE_ON_UPDATE:
                    existing = ws.cell(found, c).value
                    if existing not in (None, ""):
                        val = existing
                ws.cell(found, c).value = val

    def _upsert_contact(self, ws, rec: OpportunityRecord) -> None:
        email = (rec.contact_email or "").strip().lower()
        if not email:
            return
        found = None
        for r in range(2, ws.max_row + 1):
            if str(ws.cell(r, 5).value or "").strip().lower() == email:
                found = r
                break
        row = [
            make_opportunity_id("contact", rec.company, rec.contact_name or email, email),
            rec.contact_name,
            rec.contact_position,
            rec.company,
            rec.contact_email,
            rec.email_status or "PUBLIC_UNVERIFIED",
            rec.linkedin_url,
            rec.company_website,
            rec.source_url,
            rec.evidence,
            date.today().isoformat(),
            "",
        ]
        if found is None:
            ws.append(row)
        else:
            notes = ws.cell(found, 12).value or ""
            for c, val in enumerate(row[:-1], start=1):
                ws.cell(found, c).value = val
            ws.cell(found, 12).value = notes

    def _refresh_statistics(self, wb: Workbook) -> None:
        ws_all = wb["All Opportunities"]
        headers = [c.value for c in ws_all[1]]
        today = date.today().isoformat()
        total = new_today = grade_a = jobs = contracts = explicit = founders = clients = recruiters = emails = phones = 0
        type_idx = headers.index("Opportunity Type") + 1
        grade_idx = headers.index("Grade") + 1
        disc_idx = headers.index("Discovered Date") + 1
        intent_idx = headers.index("Intent Classification") + 1
        email_idx = headers.index("Contact Email") + 1
        phone_idx = headers.index("Contact Phone") + 1 if "Contact Phone" in headers else None
        for r in range(2, ws_all.max_row + 1):
            if not ws_all.cell(r, 1).value:
                continue
            total += 1
            otype = str(ws_all.cell(r, type_idx).value or "").lower()
            if otype == "job":
                jobs += 1
            elif otype in ("contract", "freelance"):
                contracts += 1
            elif otype == "client":
                clients += 1
            elif otype == "founder":
                founders += 1
            elif otype == "recruiter":
                recruiters += 1
            if str(ws_all.cell(r, grade_idx).value or "") == "A":
                grade_a += 1
            if str(ws_all.cell(r, disc_idx).value or "")[:10] == today:
                new_today += 1
            if str(ws_all.cell(r, intent_idx).value or "") == "EXPLICIT_DEMAND":
                explicit += 1
            if str(ws_all.cell(r, email_idx).value or "").strip():
                emails += 1
            if phone_idx and str(ws_all.cell(r, phone_idx).value or "").strip():
                phones += 1
        stats = wb["Agent Statistics"]
        metrics = {
            "total_opportunities": total,
            "new_today": new_today,
            "grade_a": grade_a,
            "jobs": jobs,
            "contracts": contracts,
            "clients": clients,
            "explicit_demands": explicit,
            "founders": founders,
            "recruiters": recruiters,
            "public_phones": phones,
            "public_emails": emails,
            "last_excel_update": now_iso(),
        }
        # rebuild simple key/value
        existing: dict[str, int] = {}
        for r in range(2, stats.max_row + 1):
            key = str(stats.cell(r, 1).value or "")
            if key:
                existing[key] = r
        for key, value in metrics.items():
            if key in existing:
                stats.cell(existing[key], 2).value = value
                stats.cell(existing[key], 3).value = now_iso()
            else:
                stats.append([key, value, now_iso()])

    def record_source_run(
        self,
        source_name: str,
        *,
        success: bool,
        new_records: int = 0,
        duplicates: int = 0,
        error: str = "",
    ) -> None:
        self.ensure_workbook()
        lock = self._lock()
        if lock:
            with lock:
                self._record_source_unlocked(source_name, success, new_records, duplicates, error)
        else:
            self._record_source_unlocked(source_name, success, new_records, duplicates, error)

    def _record_source_unlocked(
        self,
        source_name: str,
        success: bool,
        new_records: int,
        duplicates: int,
        error: str,
    ) -> None:
        wb = load_workbook(self.path)
        ws = wb["Source Performance"]
        found = None
        for r in range(2, ws.max_row + 1):
            if str(ws.cell(r, 1).value or "") == source_name:
                found = r
                break
        if found is None:
            ws.append(
                [
                    source_name,
                    1,
                    1 if success else 0,
                    0 if success else 1,
                    new_records,
                    duplicates,
                    now_iso() if success else "",
                    error if not success else "",
                    "yes",
                ]
            )
        else:
            ws.cell(found, 2).value = int(ws.cell(found, 2).value or 0) + 1
            if success:
                ws.cell(found, 3).value = int(ws.cell(found, 3).value or 0) + 1
                ws.cell(found, 7).value = now_iso()
            else:
                ws.cell(found, 4).value = int(ws.cell(found, 4).value or 0) + 1
                ws.cell(found, 8).value = error[:500]
            ws.cell(found, 5).value = int(ws.cell(found, 5).value or 0) + new_records
            ws.cell(found, 6).value = int(ws.cell(found, 6).value or 0) + duplicates
        # mark last discovery on stats
        if "Agent Statistics" in wb.sheetnames and success:
            stats = wb["Agent Statistics"]
            for r in range(2, stats.max_row + 1):
                if stats.cell(r, 1).value == "last_discovery":
                    stats.cell(r, 2).value = now_iso()
                    stats.cell(r, 3).value = now_iso()
                    break
        self._atomic_save(wb)

    def record_search_query(
        self,
        *,
        query_id: str,
        engine: str,
        query_text: str,
        hits: int = 0,
        new_hits: int = 0,
        notes: str = "",
        enabled: str = "yes",
    ) -> None:
        """Upsert a row on the Search Queries sheet for intelligent pack tracking."""
        self.ensure_workbook()
        lock = self._lock()
        if lock:
            with lock:
                self._record_search_query_unlocked(
                    query_id, engine, query_text, hits, new_hits, notes, enabled
                )
        else:
            self._record_search_query_unlocked(
                query_id, engine, query_text, hits, new_hits, notes, enabled
            )

    def _record_search_query_unlocked(
        self,
        query_id: str,
        engine: str,
        query_text: str,
        hits: int,
        new_hits: int,
        notes: str,
        enabled: str,
    ) -> None:
        wb = load_workbook(self.path)
        if "Search Queries" not in wb.sheetnames:
            ws = wb.create_sheet("Search Queries")
            ws.append(
                [
                    "Query ID",
                    "Engine",
                    "Query Text",
                    "Last Run",
                    "Hits",
                    "New Hits",
                    "Enabled",
                    "Notes",
                ]
            )
            self._style_header(ws)
        else:
            ws = wb["Search Queries"]
        found = None
        for r in range(2, ws.max_row + 1):
            if str(ws.cell(r, 1).value or "") == query_id:
                found = r
                break
        stamp = now_iso()
        if found is None:
            ws.append(
                [
                    query_id,
                    engine,
                    query_text[:500],
                    stamp,
                    hits,
                    new_hits,
                    enabled,
                    notes[:300],
                ]
            )
        else:
            ws.cell(found, 2).value = engine
            ws.cell(found, 3).value = query_text[:500]
            ws.cell(found, 4).value = stamp
            prev_hits = int(ws.cell(found, 5).value or 0)
            prev_new = int(ws.cell(found, 6).value or 0)
            ws.cell(found, 5).value = prev_hits + hits
            ws.cell(found, 6).value = prev_new + new_hits
            ws.cell(found, 7).value = enabled
            if notes:
                ws.cell(found, 8).value = notes[:300]
        self._atomic_save(wb)

    def expire_stale_opportunities(
        self,
        *,
        max_age_days: int | None = None,
        backup: bool = True,
        also_block_india: bool = True,
    ) -> dict[str, int]:
        """Mark rows older than ``max_age_days`` (default 90 / 3 months) as expired.

        Also expires India / India-primary listings when ``also_block_india`` is True.
        Infers posted date from Posted Date, LinkedIn activity URL, or relative age text.
        """
        from agent.quality.freshness import MAX_LISTING_AGE_DAYS

        ceiling = MAX_LISTING_AGE_DAYS if max_age_days is None else max_age_days
        self.ensure_workbook()
        if backup:
            self.backup("pre_expire_stale")
        lock = self._lock()
        if lock:
            with lock:
                return self._expire_stale_unlocked(ceiling, also_block_india=also_block_india)
        return self._expire_stale_unlocked(ceiling, also_block_india=also_block_india)

    def _expire_stale_unlocked(
        self,
        max_age_days: int,
        *,
        also_block_india: bool = True,
    ) -> dict[str, int]:
        from agent.quality.freshness import enrich_posted_date, is_too_old
        from agent.quality.geo_gate import geo_drop_reason

        wb = load_workbook(self.path)
        ws = wb["All Opportunities"]
        headers = [c.value for c in ws[1]]
        if "ID" not in headers or "Status" not in headers:
            wb.close()
            return {"expired": 0, "enriched_posted": 0, "scanned": 0, "expired_india": 0}

        id_col = headers.index("ID") + 1
        status_col = headers.index("Status") + 1
        posted_col = headers.index("Posted Date") + 1 if "Posted Date" in headers else None
        notes_col = headers.index("Notes") + 1 if "Notes" in headers else None
        hist = wb["Discovery History"] if "Discovery History" in wb.sheetnames else None

        expired = enriched = scanned = expired_india = 0
        for r in range(2, ws.max_row + 1):
            if not ws.cell(r, id_col).value:
                continue
            scanned += 1
            values = [ws.cell(r, c).value for c in range(1, len(headers) + 1)]
            data = _row_to_record([str(h or "") for h in headers], values)
            if not data.get("id"):
                continue
            rec = OpportunityRecord.from_row(data)
            status = (rec.status or "").strip().lower()
            if status in ("expired", "closed", "rejected", "withdrawn"):
                continue
            before = rec.posted_date
            enrich_posted_date(rec)
            if rec.posted_date and rec.posted_date != before and posted_col:
                ws.cell(r, posted_col).value = rec.posted_date
                enriched += 1

            why = ""
            if also_block_india:
                why = geo_drop_reason(rec)
                if why:
                    expired_india += 1
            if not why:
                too_old, why = is_too_old(rec, max_age_days=max_age_days)
                if not too_old:
                    continue
            ws.cell(r, status_col).value = "expired"
            if notes_col:
                prev = str(ws.cell(r, notes_col).value or "")
                tag = f"[auto-expired {why}]"
                if tag not in prev:
                    ws.cell(r, notes_col).value = (prev + " " + tag).strip()
            if hist is not None:
                hist.append([now_iso(), rec.id, "expired", why, rec.source_name])
            # Mirror status on type sheet
            type_sheet = TYPE_TO_SHEET.get((rec.opportunity_type or "").lower())
            if type_sheet and type_sheet in wb.sheetnames:
                tws = wb[type_sheet]
                theaders = [c.value for c in tws[1]]
                if "ID" in theaders and "Status" in theaders:
                    tid = theaders.index("ID") + 1
                    tstatus = theaders.index("Status") + 1
                    tposted = theaders.index("Posted Date") + 1 if "Posted Date" in theaders else None
                    for tr in range(2, tws.max_row + 1):
                        if str(tws.cell(tr, tid).value or "") == rec.id:
                            tws.cell(tr, tstatus).value = "expired"
                            if tposted and rec.posted_date:
                                tws.cell(tr, tposted).value = rec.posted_date
                            break
            expired += 1

        self._refresh_statistics(wb)
        self._atomic_save(wb)
        return {
            "expired": expired,
            "expired_india": expired_india,
            "enriched_posted": enriched,
            "scanned": scanned,
        }

    def update_opportunity_fields(
        self,
        opportunity_id: str,
        *,
        status: str | None = None,
        notes_append: str = "",
        next_action: str | None = None,
    ) -> bool:
        """Update Status / Notes / Next Action for one row by ID. Returns True if found."""
        self.ensure_workbook()
        lock = self._lock()
        if lock:
            with lock:
                return self._update_opportunity_fields_unlocked(
                    opportunity_id,
                    status=status,
                    notes_append=notes_append,
                    next_action=next_action,
                )
        return self._update_opportunity_fields_unlocked(
            opportunity_id,
            status=status,
            notes_append=notes_append,
            next_action=next_action,
        )

    def _update_opportunity_fields_unlocked(
        self,
        opportunity_id: str,
        *,
        status: str | None,
        notes_append: str,
        next_action: str | None,
    ) -> bool:
        oid = (opportunity_id or "").strip()
        if not oid:
            return False
        wb = load_workbook(self.path)
        ws = wb["All Opportunities"]
        headers = [c.value for c in ws[1]]
        if "ID" not in headers:
            wb.close()
            return False
        id_col = headers.index("ID") + 1
        status_col = headers.index("Status") + 1 if "Status" in headers else None
        notes_col = headers.index("Notes") + 1 if "Notes" in headers else None
        next_col = headers.index("Next Action") + 1 if "Next Action" in headers else None
        found = None
        for r in range(2, ws.max_row + 1):
            if str(ws.cell(r, id_col).value or "").strip() == oid:
                found = r
                break
        if found is None:
            wb.close()
            return False
        if status is not None and status_col:
            ws.cell(found, status_col).value = status
        if notes_append and notes_col:
            prev = str(ws.cell(found, notes_col).value or "")
            tag = notes_append.strip()
            if tag and tag not in prev:
                ws.cell(found, notes_col).value = (prev + " " + tag).strip()
        if next_action is not None and next_col:
            ws.cell(found, next_col).value = next_action
        # Mirror to type sheet
        otype = ""
        if "Opportunity Type" in headers:
            otype = str(ws.cell(found, headers.index("Opportunity Type") + 1).value or "").lower()
        type_sheet = TYPE_TO_SHEET.get(otype)
        if type_sheet and type_sheet in wb.sheetnames:
            tws = wb[type_sheet]
            theaders = [c.value for c in tws[1]]
            if "ID" in theaders:
                tid = theaders.index("ID") + 1
                for tr in range(2, tws.max_row + 1):
                    if str(tws.cell(tr, tid).value or "").strip() == oid:
                        if status is not None and "Status" in theaders:
                            tws.cell(tr, theaders.index("Status") + 1).value = status
                        if notes_append and "Notes" in theaders:
                            tnotes = theaders.index("Notes") + 1
                            prev = str(tws.cell(tr, tnotes).value or "")
                            tag = notes_append.strip()
                            if tag and tag not in prev:
                                tws.cell(tr, tnotes).value = (prev + " " + tag).strip()
                        if next_action is not None and "Next Action" in theaders:
                            tws.cell(tr, theaders.index("Next Action") + 1).value = next_action
                        break
        if "Discovery History" in wb.sheetnames:
            wb["Discovery History"].append(
                [now_iso(), oid, status or "updated", notes_append or next_action or "field update", "dashboard"]
            )
        self._atomic_save(wb)
        return True

    def get_statistics(self) -> dict[str, Any]:
        self.ensure_workbook()
        wb = load_workbook(self.path, read_only=True, data_only=True)
        try:
            ws = wb["Agent Statistics"]
            out: dict[str, Any] = {}
            for row in ws.iter_rows(min_row=2, values_only=True):
                if row and row[0]:
                    out[str(row[0])] = row[1]
            return out
        finally:
            wb.close()
