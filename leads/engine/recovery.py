"""Retry transient source failures, record them, and resume an interrupted run."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Optional

from .incremental import utcnow_iso
from .persist import atomic_write_json

TRANSIENT_MARKERS = (
    "429",
    "500",
    "502",
    "503",
    "504",
    "timeout",
    "timed out",
    "temporarily unavailable",
    "connection reset",
    "connection aborted",
    "connection refused",
)


def is_transient(exc: BaseException) -> bool:
    if isinstance(exc, (TimeoutError, ConnectionError)):
        return True
    code = getattr(exc, "code", None)
    if code in (429, 500, 502, 503, 504):
        return True
    text = str(exc).lower()
    return any(marker in text for marker in TRANSIENT_MARKERS)


def retry_call(
    fn: Callable[[], Any],
    *,
    attempts: int = 3,
    base_delay: float = 0.0,
    sleep: Optional[Callable[[float], None]] = None,
) -> tuple[Any, int]:
    """Call ``fn`` until it succeeds or the error is not transient.

    Returns ``(result, attempts_used)``. ``base_delay`` is seconds and doubles
    each retry. Tests pass ``0`` so retries stay immediate.
    """
    import time

    tries = max(1, attempts)
    sleeper = sleep or time.sleep
    last: BaseException | None = None
    for i in range(tries):
        try:
            return fn(), i + 1
        except Exception as exc:
            last = exc
            if not is_transient(exc) or i + 1 >= tries:
                raise
            delay = base_delay * (2**i)
            if delay > 0:
                sleeper(delay)
    assert last is not None
    raise last


def start_run(runs_dir: Path, *, run_id: str, sources: list[str], query: str) -> dict[str, Any]:
    runs_dir.mkdir(parents=True, exist_ok=True)
    run = {
        "id": run_id,
        "status": "running",
        "sources": list(sources),
        "completed": [],
        "failed": {},
        "query": query,
        "updated": utcnow_iso(),
    }
    save_run(runs_dir, run)
    return run


def run_path(runs_dir: Path, run_id: str) -> Path:
    return runs_dir / f"{run_id}.json"


def load_run(runs_dir: Path, run_id: str) -> Optional[dict[str, Any]]:
    path = run_path(runs_dir, run_id)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    data.setdefault("completed", [])
    data.setdefault("failed", {})
    data.setdefault("sources", [])
    return data


def save_run(runs_dir: Path, run: dict[str, Any]) -> None:
    runs_dir.mkdir(parents=True, exist_ok=True)
    run["updated"] = utcnow_iso()
    atomic_write_json(run_path(runs_dir, str(run["id"])), run)


def mark_completed(run: dict[str, Any], source: str) -> None:
    if source not in run["completed"]:
        run["completed"].append(source)
    run["failed"].pop(source, None)


def mark_failed(run: dict[str, Any], source: str, exc: BaseException, *, attempts: int) -> None:
    run["failed"][source] = {
        "error": str(exc),
        "attempts": attempts,
        "transient": is_transient(exc),
        "at": utcnow_iso(),
    }


def list_failures(runs_dir: Path) -> list[dict[str, Any]]:
    if not runs_dir.is_dir():
        return []
    rows: list[dict[str, Any]] = []
    for path in sorted(runs_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        for source, info in (data.get("failed") or {}).items():
            if not isinstance(info, dict):
                continue
            rows.append({"run_id": data.get("id"), "source": source, **info})
    return rows
