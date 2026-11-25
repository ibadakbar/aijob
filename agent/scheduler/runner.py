"""Background agent runner — independent of Streamlit dashboard."""

from __future__ import annotations

import json
import logging
import os
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from agent.discovery.agencies.collect import run_agency_discovery
from agent.discovery.clients.hunt import run_client_discovery
from agent.discovery.clients.ingest import ingest_leads_store, run_leads_discover
from agent.discovery.companies.careers import run_ats_deep_crawl
from agent.discovery.founders.collect import run_founder_discovery
from agent.discovery.jobs.ingest import run_job_discovery
from agent.discovery.recruiters.collect import run_recruiter_discovery
from agent.storage.excel_store import ExcelStore

ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = ROOT / "logs" / "agent_state.json"
PID_PATH = ROOT / "logs" / "agent.pid"
CONTROL_PATH = ROOT / "logs" / "agent_control.json"
CONFIG_PATH = ROOT / "agent" / "config" / "default.yaml"


def read_pid() -> int | None:
    if not PID_PATH.is_file():
        return None
    try:
        return int(PID_PATH.read_text(encoding="utf-8").strip().split()[0])
    except (ValueError, OSError):
        return None


def pid_is_alive(pid: int | None) -> bool:
    """True if OS process exists. Avoid os.kill(pid, 0) on Windows (WinError 87)."""
    if not pid or pid <= 0:
        return False
    if sys.platform == "win32":
        try:
            import ctypes

            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            handle = ctypes.windll.kernel32.OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION, 0, int(pid)
            )
            if handle:
                ctypes.windll.kernel32.CloseHandle(handle)
                return True
            # Fallback: tasklist (OpenProcess can fail for protected/access denied)
            out = subprocess.check_output(
                ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                text=True,
                stderr=subprocess.DEVNULL,
                timeout=5,
            )
            return str(pid) in out and "INFO:" not in out
        except Exception:  # noqa: BLE001
            return False
    try:
        os.kill(pid, 0)
        return True
    except (OSError, SystemError):
        return False


def is_agent_alive() -> bool:
    return pid_is_alive(read_pid())


def live_status() -> dict[str, Any]:
    """Authoritative status for dashboard — process alive beats stale state file."""
    state = load_state()
    control = load_control()
    pid = read_pid()
    alive = pid_is_alive(pid)
    cmd = str(control.get("command") or "run")
    if not alive:
        status = "stopped"
    elif cmd == "pause" or state.get("status") == "paused":
        status = "paused"
    else:
        status = "running"
    return {
        "status": status,
        "alive": alive,
        "pid": pid if alive else None,
        "control": cmd,
        "state_file": state.get("status"),
        "last_runs": state.get("last_runs") or {},
    }


def start_agent_process() -> dict[str, Any]:
    """Spawn detached background worker. Idempotent if already running."""
    ROOT.joinpath("logs").mkdir(parents=True, exist_ok=True)
    if is_agent_alive():
        set_control("run")
        state = load_state()
        state["status"] = "running"
        save_state(state)
        return {"ok": True, "already_running": True, "pid": read_pid()}

    set_control("run")
    py = sys.executable
    venv_py = ROOT / ".venv" / "Scripts" / "python.exe"
    if venv_py.is_file():
        py = str(venv_py)

    stdout_path = ROOT / "logs" / "agent_stdout.log"
    stdout_fh = open(stdout_path, "a", encoding="utf-8")  # noqa: SIM115 — kept for process life
    creationflags = 0
    if sys.platform == "win32":
        # Detach so Streamlit reruns never kill the worker
        creationflags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]

    proc = subprocess.Popen(
        [py, str(ROOT / "agent" / "cli.py"), "start"],
        cwd=str(ROOT),
        stdout=stdout_fh,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        creationflags=creationflags,
        close_fds=sys.platform != "win32",
    )
    # Seed pid; the child overwrites with os.getpid() once the loop starts
    # (Windows DETACHED_PROCESS may use a different child pid than Popen.pid).
    PID_PATH.write_text(str(proc.pid), encoding="utf-8")
    real_pid = proc.pid
    for _ in range(40):
        time.sleep(0.25)
        candidate = read_pid()
        if candidate and pid_is_alive(candidate):
            real_pid = candidate
            break
    state = load_state()
    state["status"] = "running"
    state["started_at"] = datetime.now().isoformat()
    state["pid"] = real_pid
    save_state(state)
    return {
        "ok": True,
        "already_running": False,
        "pid": real_pid,
        "alive": pid_is_alive(real_pid),
    }


def request_stop_agent(*, force: bool = False) -> dict[str, Any]:
    """Signal stop; optionally force-kill after grace period."""
    set_control("stop")
    pid = read_pid()
    if not pid_is_alive(pid):
        state = load_state()
        state["status"] = "stopped"
        save_state(state)
        if PID_PATH.exists():
            PID_PATH.unlink(missing_ok=True)
        return {"ok": True, "stopped": True, "forced": False}

    # Give the loop a few seconds to exit cleanly
    for _ in range(20):
        time.sleep(0.25)
        if not pid_is_alive(pid):
            state = load_state()
            state["status"] = "stopped"
            save_state(state)
            if PID_PATH.exists():
                PID_PATH.unlink(missing_ok=True)
            return {"ok": True, "stopped": True, "forced": False}

    if force and pid:
        try:
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True, timeout=10)
            else:
                os.kill(pid, signal.SIGTERM)
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": str(exc), "pid": pid}
        state = load_state()
        state["status"] = "stopped"
        save_state(state)
        if PID_PATH.exists():
            PID_PATH.unlink(missing_ok=True)
        return {"ok": True, "stopped": True, "forced": True, "pid": pid}

    return {"ok": True, "stopped": False, "pid": pid, "note": "stop signaled; process still exiting"}


def _setup_logging(log_dir: Path) -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("opportunity_agent")
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        fh = logging.FileHandler(log_dir / "agent.log", encoding="utf-8")
        fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(fh)
        sh = logging.StreamHandler()
        sh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(sh)
    return logger


def load_yaml_config() -> dict[str, Any]:
    if not CONFIG_PATH.is_file():
        return {}
    try:
        import yaml

        return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    except Exception:  # noqa: BLE001
        return {}


def load_control() -> dict[str, Any]:
    if CONTROL_PATH.is_file():
        try:
            return json.loads(CONTROL_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"command": "run", "updated": None}


def set_control(command: str) -> None:
    CONTROL_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONTROL_PATH.write_text(
        json.dumps({"command": command, "updated": datetime.now().isoformat()}, indent=2),
        encoding="utf-8",
    )


def load_state() -> dict[str, Any]:
    if STATE_PATH.is_file():
        try:
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"last_runs": {}, "status": "stopped"}


def save_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
    tmp.replace(STATE_PATH)


class AgentRunner:
    def __init__(self, intervals: dict[str, int] | None = None) -> None:
        self.log = _setup_logging(ROOT / "logs")
        self.store = ExcelStore()
        self.cfg = load_yaml_config()
        mins = (self.cfg.get("intervals_minutes") or {}) if self.cfg else {}
        self.intervals = intervals or {
            "jobs": int(mins.get("jobs_feeds", 15)) * 60,
            "ats": int(mins.get("ats_jobs", 30)) * 60,
            "leads": int(mins.get("clients_projects", 45)) * 60,
            "clients": int(mins.get("clients_projects", 45)) * 60,
            "founders": int(mins.get("founders", 60)) * 60,
            "recruiters": int(mins.get("recruiters", 60)) * 60,
            "agencies": int(mins.get("agencies", 60)) * 60,
            "stats": int(mins.get("excel_stats_refresh", 30)) * 60,
        }
        self._stop = threading.Event()
        self._engines = (self.cfg.get("engines") or {}) if self.cfg else {}
        self._quality = (self.cfg.get("quality") or {}) if self.cfg else {}

    def _engine_on(self, name: str, default: bool = True) -> bool:
        block = self._engines.get(name)
        if isinstance(block, dict):
            return bool(block.get("enabled", default))
        return default

    def _due(self, key: str, interval_sec: int, state: dict[str, Any]) -> bool:
        last = (state.get("last_runs") or {}).get(key)
        if not last:
            return True
        try:
            ts = datetime.fromisoformat(last)
        except ValueError:
            return True
        return (datetime.now() - ts).total_seconds() >= interval_sec

    def _mark(self, key: str, state: dict[str, Any]) -> None:
        state.setdefault("last_runs", {})[key] = datetime.now().isoformat()
        save_state(state)

    def run_once(self, engine: str = "all") -> dict[str, Any]:
        self.store.ensure_workbook()
        results: dict[str, Any] = {}
        # Always enforce 3-month ceiling on existing Excel rows
        try:
            results["expire_stale"] = self.store.expire_stale_opportunities(backup=False)
        except Exception as exc:  # noqa: BLE001
            self.log.warning("expire_stale failed: %s", exc)
            results["expire_stale"] = {"ok": False, "error": str(exc)}
        jobs_cfg = self._engines.get("jobs") or {}
        if engine in ("all", "jobs") and self._engine_on("jobs", True):
            self.log.info("Running job discovery (gated)")
            results["jobs"] = run_job_discovery(
                self.store,
                limit=int(jobs_cfg.get("limit", 25)),
                since=str(jobs_cfg.get("since", "2d")),
                volume=bool(jobs_cfg.get("volume", True)),
            )
        if engine in ("all", "ats", "jobs") and self._engine_on("companies", True):
            self.log.info("Running ATS/careers deep crawl")
            results["ats"] = run_ats_deep_crawl(
                self.store,
                limit=int((self._engines.get("companies") or {}).get("limit", 25)),
                since=str((self._engines.get("companies") or {}).get("since", "7d")),
                harvest=bool((self._engines.get("companies") or {}).get("harvest", False)),
            )
        if engine in ("all", "leads") and self._engine_on("leads_bridge", True):
            self.log.info("Running leads bridge")
            prompt = str(
                (self._engines.get("leads_bridge") or {}).get("prompt")
                or (
                    "Find React OR Next.js OR TypeScript full-stack SaaS roles "
                    "remote-international or visa sponsorship for DE/NL/UK/IE/AU/NZ/CA/US/EU/UAE/PK. "
                    "Include New Zealand. Exclude India / Bangalore / Mumbai roles."
                )
            )
            results["leads_discover"] = run_leads_discover(prompt=prompt, store=self.store)
            results["leads_ingest"] = ingest_leads_store(self.store)
        if engine in ("all", "clients") and self._engine_on("clients", True):
            self.log.info("Running client hunter")
            ccfg = self._engines.get("clients") or {}
            results["clients"] = run_client_discovery(
                self.store,
                limit=int(ccfg.get("limit", 50)),
                discover=bool(ccfg.get("discover", True)),
                prompt=str(ccfg.get("prompt") or ""),
            )
        if engine in ("all", "founders") and self._engine_on("founders", True):
            results["founders"] = run_founder_discovery(self.store)
        if engine in ("all", "recruiters") and self._engine_on("recruiters", True):
            results["recruiters"] = run_recruiter_discovery(self.store)
        if engine in ("all", "agencies") and self._engine_on("agencies", True):
            results["agencies"] = run_agency_discovery(self.store)
        if engine in ("all", "ingest_only"):
            results["leads_ingest"] = ingest_leads_store(self.store)
        return results

    def loop(self) -> None:
        self.store.ensure_workbook()
        ROOT.joinpath("logs").mkdir(parents=True, exist_ok=True)
        PID_PATH.write_text(str(os.getpid()), encoding="utf-8")
        state = load_state()
        state["status"] = "running"
        state["pid"] = os.getpid()
        save_state(state)
        self.log.info("Agent started pid=%s (Excel store=%s)", os.getpid(), self.store.path)

        def _handle_sig(*_args):
            self.log.info("Shutdown signal received")
            self._stop.set()

        try:
            signal.signal(signal.SIGINT, _handle_sig)
            signal.signal(signal.SIGTERM, _handle_sig)
        except Exception:
            pass

        try:
            self.run_once("jobs")
            state = load_state()
            self._mark("jobs", state)
        except Exception as exc:  # noqa: BLE001
            self.log.exception("Initial jobs run failed: %s", exc)

        while not self._stop.is_set():
            ctrl = load_control().get("command", "run")
            if ctrl == "stop":
                self.log.info("Stop command received")
                break
            if ctrl == "pause":
                state = load_state()
                state["status"] = "paused"
                save_state(state)
                time.sleep(2)
                continue
            if ctrl == "run_now":
                set_control("run")
                try:
                    self.run_once("all")
                except Exception as exc:  # noqa: BLE001
                    self.log.exception("run_now failed: %s", exc)
                state = load_state()
                now = datetime.now().isoformat()
                state.setdefault("last_runs", {})
                for k in ("jobs", "ats", "leads", "clients", "founders", "recruiters", "agencies"):
                    state["last_runs"][k] = now
                state["status"] = "running"
                save_state(state)
                continue

            state = load_state()
            state["status"] = "running"
            workers = [
                ("jobs", self.intervals["jobs"], "jobs", lambda: run_job_discovery(self.store)),
                ("ats", self.intervals["ats"], "companies", lambda: run_ats_deep_crawl(self.store)),
                ("leads", self.intervals["leads"], "leads_bridge", lambda: ingest_leads_store(self.store)),
                ("clients", self.intervals["clients"], "clients", lambda: run_client_discovery(self.store, discover=False)),
                ("founders", self.intervals["founders"], "founders", lambda: run_founder_discovery(self.store)),
                ("recruiters", self.intervals["recruiters"], "recruiters", lambda: run_recruiter_discovery(self.store)),
                ("agencies", self.intervals["agencies"], "agencies", lambda: run_agency_discovery(self.store)),
            ]
            for key, interval, eng_name, fn in workers:
                if not self._engine_on(
                    eng_name,
                    eng_name
                    in ("jobs", "leads_bridge", "companies", "clients", "founders", "recruiters", "agencies"),
                ):
                    continue
                if self._due(key, interval, state):
                    try:
                        r = fn()
                        self.log.info("%s result: %s", key, r)
                    except Exception as exc:  # noqa: BLE001
                        self.log.exception("%s worker failed: %s", key, exc)
                    self._mark(key, state)
            save_state(state)
            time.sleep(5)

        state = load_state()
        state["status"] = "stopped"
        save_state(state)
        if PID_PATH.exists():
            PID_PATH.unlink(missing_ok=True)
        self.log.info("Agent stopped")


def main() -> None:
    AgentRunner().loop()


if __name__ == "__main__":
    main()
