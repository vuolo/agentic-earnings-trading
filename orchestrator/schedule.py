"""launchd management for the daily tick (pattern: stake-synthetics schedule.py).

Installs a user LaunchAgent that runs `python -m orchestrator.daily` each
morning. Runs only while the user is logged in (Aqua session) because the
`claude` CLI login and the Robinhood MCP OAuth live in the user session.

    python -m orchestrator.schedule show                 # print plist, no install
    python -m orchestrator.schedule install              # default 09:45 local
    python -m orchestrator.schedule install --hour 10 --minute 0
    python -m orchestrator.schedule status
    python -m orchestrator.schedule run-now              # real tick, immediately
    python -m orchestrator.schedule uninstall
"""

from __future__ import annotations

import argparse
import os
import plistlib
import shutil
import subprocess
import sys
from pathlib import Path

from .launcher import DEFAULT_MODEL, REPO_ROOT

LABEL = "com.earnings.daily"
PLIST_PATH = Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"
CAF_LABEL = "com.earnings.caffeinate"
CAF_PLIST_PATH = Path.home() / "Library" / "LaunchAgents" / f"{CAF_LABEL}.plist"
LOGS = REPO_ROOT / "logs"
VENV_PY = REPO_ROOT / ".venv" / "bin" / "python"


def _path_env() -> str:
    """PATH for the launchd job — launchd strips the user PATH, and the tick
    needs the `claude` CLI (stake repo lesson: a stripped PATH produced dud
    runs). Bake in the resolved claude dir plus the standard locations."""
    parts = ["/opt/homebrew/bin", "/usr/local/bin", "/usr/bin", "/bin", "/usr/sbin", "/sbin"]
    claude = shutil.which("claude")
    if claude:
        d = str(Path(claude).resolve().parent)
        if d not in parts:
            parts.insert(0, d)
    return ":".join(parts)


# Market-phase fire times (local = ET). Morning fires at 9:24 so exit orders
# are placed BEFORE 9:30 and fill IN the opening auction — the exact
# `post_open` print every backtest measures (no pipeline latency, no
# first-minutes drift). Afternoon entries land just before the close; the
# evening fires are the (default-off) AMC after-hours path.
FIRE_TIMES = ((9, 24), (15, 40), (16, 20), (16, 50))


def _plist(hour: int, minute: int, model: str) -> dict:
    intervals = [{"Hour": h, "Minute": m} for h, m in FIRE_TIMES]
    if (hour, minute) not in FIRE_TIMES:
        intervals.append({"Hour": hour, "Minute": minute})
    return {
        "Label": LABEL,
        "ProgramArguments": [
            str(VENV_PY), "-m", "orchestrator.daily", "--model", model,
        ],
        "WorkingDirectory": str(REPO_ROOT),
        "EnvironmentVariables": {"PATH": _path_env()},
        "StartCalendarInterval": intervals,
        "RunAtLoad": False,
        "StandardOutPath": str(LOGS / "launchd_stdout.log"),
        "StandardErrorPath": str(LOGS / "launchd_stderr.log"),
        "LimitLoadToSessionType": "Aqua",
    }


def _caffeinate_plist() -> dict:
    """Hold the system awake through market hours. The operator's Mac sleeps
    after 1 idle minute; the only guaranteed-awake moment is the existing
    07:55 wakepoweron (used by another schedule). Firing at 08:05 rides that
    window and `caffeinate -i` then prevents idle sleep until ~17:10, covering
    all four ticks. No sudo needed; weekdays only."""
    return {
        "Label": CAF_LABEL,
        "ProgramArguments": ["/usr/bin/caffeinate", "-i", "-t", "32700"],
        "StartCalendarInterval": [
            {"Weekday": wd, "Hour": 8, "Minute": 5} for wd in range(1, 6)
        ],
        "RunAtLoad": False,
        "LimitLoadToSessionType": "Aqua",
    }


def _gui_target() -> str:
    return f"gui/{os.getuid()}"


def install(hour: int, minute: int, model: str) -> int:
    if not VENV_PY.exists():
        print(f"error: {VENV_PY} not found — create the venv first (README).",
              file=sys.stderr)
        return 1
    LOGS.mkdir(exist_ok=True)
    PLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    PLIST_PATH.write_bytes(plistlib.dumps(_plist(hour, minute, model)))
    subprocess.run(["launchctl", "bootout", f"{_gui_target()}/{LABEL}"],
                   capture_output=True)  # ok if not loaded
    rc = subprocess.run(["launchctl", "bootstrap", _gui_target(), str(PLIST_PATH)]).returncode
    CAF_PLIST_PATH.write_bytes(plistlib.dumps(_caffeinate_plist()))
    subprocess.run(["launchctl", "bootout", f"{_gui_target()}/{CAF_LABEL}"],
                   capture_output=True)
    caf_rc = subprocess.run(
        ["launchctl", "bootstrap", _gui_target(), str(CAF_PLIST_PATH)]
    ).returncode
    if rc == 0:
        times = ", ".join(f"{h:02d}:{m:02d}" for h, m in FIRE_TIMES)
        print(f"installed {LABEL}: fires daily at {times} local "
              f"(model={model})\nplist: {PLIST_PATH}\nlogs:  {LOGS}/launchd_*.log")
        print("installed com.earnings.caffeinate: weekdays 08:05, holds the "
              "system awake ~9h (rides the existing 07:55 wake)"
              if caf_rc == 0 else
              f"warning: caffeinate agent failed to load (rc={caf_rc})")
        print("note: keep the Mac plugged in + logged in during market hours; "
              "belt-and-braces on AC: `sudo pmset -c sleep 0`.")
    else:
        print(f"launchctl bootstrap failed (rc={rc})", file=sys.stderr)
    return rc


def uninstall() -> int:
    for label, path in ((LABEL, PLIST_PATH), (CAF_LABEL, CAF_PLIST_PATH)):
        subprocess.run(["launchctl", "bootout", f"{_gui_target()}/{label}"],
                       capture_output=True)
        if path.exists():
            path.unlink()
            print(f"removed {path}")
        print(f"{label} unloaded")
    return 0


def status() -> int:
    r = subprocess.run(["launchctl", "print", f"{_gui_target()}/{LABEL}"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(f"{LABEL}: not loaded")
    else:
        for line in r.stdout.splitlines():
            s = line.strip()
            if any(k in s for k in ("state =", "last exit", "runs =", "program =")):
                print(s)
    err = LOGS / "launchd_stderr.log"
    if err.exists():
        tail = err.read_text().splitlines()[-5:]
        if tail:
            print("--- stderr tail ---")
            print("\n".join(tail))
    return 0


def run_now() -> int:
    return subprocess.run(
        ["launchctl", "kickstart", f"{_gui_target()}/{LABEL}"]
    ).returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="orchestrator.schedule")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_install = sub.add_parser("install")
    p_install.add_argument("--hour", type=int, default=9)
    p_install.add_argument("--minute", type=int, default=45)
    p_install.add_argument("--model", default=DEFAULT_MODEL)
    p_show = sub.add_parser("show")
    p_show.add_argument("--hour", type=int, default=9)
    p_show.add_argument("--minute", type=int, default=45)
    p_show.add_argument("--model", default=DEFAULT_MODEL)
    sub.add_parser("uninstall")
    sub.add_parser("status")
    sub.add_parser("run-now")
    args = parser.parse_args(argv)

    if args.cmd == "install":
        return install(args.hour, args.minute, args.model)
    if args.cmd == "show":
        print(plistlib.dumps(_plist(args.hour, args.minute, args.model)).decode())
        return 0
    if args.cmd == "uninstall":
        return uninstall()
    if args.cmd == "status":
        return status()
    if args.cmd == "run-now":
        return run_now()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
