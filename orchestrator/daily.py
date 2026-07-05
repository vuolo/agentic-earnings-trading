"""Daily tick: scout → labeler (due closes) → analyst (due events).

The orchestration logic is deterministic — agents run only where judgment is
needed. Fired by launchd each market morning (see orchestrator/schedule.py) or
run manually:

    python -m orchestrator.daily            # full tick
    python -m orchestrator.daily --dry-run  # show what would run, launch nothing
"""

from __future__ import annotations

import argparse
from datetime import date, timedelta

from engine.config import Config
from engine.store import Store

from . import launcher


def analyst_due(report_date: str, timing: str, today: date) -> bool:
    """Is the analyst decision window open for this event?

    bmo/unknown: the day before the report (the report lands before the next
    open, so T-1 is the last chance). amc: the day before or the report day
    itself (the report lands after that day's close).
    """
    d = date.fromisoformat(report_date)
    if timing == "amc":
        return today in (d, d - timedelta(days=1))
    return today == d - timedelta(days=1)


def tick(*, run_scout: bool = True, dry_run: bool = False,
         model: str = launcher.DEFAULT_MODEL) -> int:
    today = date.today()
    print(f"=== daily tick {today.isoformat()} (model={model}"
          + (", DRY RUN" if dry_run else "") + ") ===")

    if run_scout:
        if dry_run:
            print("scout: would run")
        else:
            print(f"scout exit {launcher.run_role('scout', model=model)}")

    cfg = Config.from_env()
    store = Store(cfg.db_path)
    try:
        due = store.due_closes(today.isoformat())
        if due:
            symbols = sorted({r["symbol"] for r in due})
            print(f"labeler: due closes → {', '.join(symbols)}")
            if not dry_run:
                rc = launcher.run_role("labeler", symbol=", ".join(symbols), model=model)
                print(f"labeler exit {rc}")
        else:
            print("labeler: no positions due for close")

        ran = 0
        for e in store.upcoming_events(days=3):
            if not analyst_due(e["report_date"], e["timing"], today):
                continue
            if store.decisions_for_event(e["id"]):
                print(f"analyst: {e['symbol']} {e['report_date']} already decided — skip")
                continue
            ran += 1
            print(f"analyst: {e['symbol']} {e['report_date']} ({e['timing']}) is due")
            if not dry_run:
                rc = launcher.run_role("analyst", symbol=e["symbol"], model=model)
                print(f"analyst({e['symbol']}) exit {rc}")
        if ran == 0:
            print("analyst: no events in the decision window")
    finally:
        store.close()
    print("tick complete")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="orchestrator.daily")
    parser.add_argument("--no-scout", action="store_true", help="skip the scout run")
    parser.add_argument("--dry-run", action="store_true", help="print plan, launch no agents")
    parser.add_argument("--model", default=launcher.DEFAULT_MODEL)
    args = parser.parse_args(argv)
    return tick(run_scout=not args.no_scout, dry_run=args.dry_run, model=args.model)


if __name__ == "__main__":
    raise SystemExit(main())
