"""Daily tick: scout → labeler → analyst → executor (armed only) → strategist.

The orchestration logic is deterministic — agents run only where judgment is
needed. Fired by launchd each market morning (see orchestrator/schedule.py) or
run manually:

    python -m orchestrator.daily            # full tick
    python -m orchestrator.daily --dry-run  # show what would run, launch nothing
"""

from __future__ import annotations

import argparse
from datetime import date, timedelta

from engine.arming import arm_status
from engine.config import Config
from engine.store import Store

from . import launcher

STRATEGIST_MIN_NEW_OUTCOMES = 3


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
        # -- labeler: paper close-outs + pass counterfactuals -----------------
        due = store.due_closes(today.isoformat())
        passes = store.due_pass_labels(today.isoformat())
        if due or passes:
            jobs = []
            if due:
                jobs.append("close paper positions: "
                            + ", ".join(sorted({r["symbol"] for r in due})))
            if passes:
                jobs.append("label pass counterfactuals (decision_id symbol): "
                            + ", ".join(f"#{r['id']} {r['symbol']}" for r in passes))
            job = "; ".join(jobs)
            print(f"labeler: {job}")
            if not dry_run:
                print(f"labeler exit {launcher.run_role('labeler', symbol=job, model=model)}")
        else:
            print("labeler: nothing due")

        # -- analyst: events entering the decision window ----------------------
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

        # -- executor: live orders, only while the operator's arm is active ----
        arm, why = arm_status()
        pending = store.pending_executions()
        live_closes = store.due_live_closes(today.isoformat())
        if arm and (pending or live_closes):
            jobs = []
            if pending:
                jobs.append("buy (decision_id symbol $size @ref): " + ", ".join(
                    f"#{r['id']} {r['symbol']} ${r['size_usd']:,.0f} @{r['entry_price']}"
                    for r in pending))
            if live_closes:
                jobs.append("sell to close (decision_id symbol): " + ", ".join(
                    f"#{r['id']} {r['symbol']}" for r in live_closes))
            job = "; ".join(jobs)
            print(f"executor (ARMED until {arm.expires}): {job}")
            if not dry_run:
                print(f"executor exit {launcher.run_role('executor', symbol=job, model=model)}")
        elif pending or live_closes:
            print(f"executor: {len(pending)} pending buy(s), {len(live_closes)} due "
                  f"close(s), but {why} — nothing executes")
        else:
            print("executor: nothing pending")

        # -- strategist: self-improvement once enough new outcomes exist -------
        n = store.outcome_count()
        last = int(store.meta_get("strategist_outcome_count", "0") or 0)
        fresh = n - last
        if fresh >= STRATEGIST_MIN_NEW_OUTCOMES:
            print(f"strategist: {fresh} new labeled outcomes — running policy review")
            if not dry_run:
                rc = launcher.run_role("strategist", model=model)
                print(f"strategist exit {rc}")
                store.meta_set("strategist_outcome_count", str(n))
        else:
            print(f"strategist: {fresh} new outcomes since last review "
                  f"(<{STRATEGIST_MIN_NEW_OUTCOMES}) — skip")
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
