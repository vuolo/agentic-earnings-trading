"""Market-phase ticks: morning (exits) / afternoon (entries) / evening (AMC exits).

The orchestration logic is deterministic — agents run only where judgment is
needed. launchd fires three times per trading day (orchestrator/schedule.py):

    09:31 ET  morning    scout · labeler (paper closes + pass labels) ·
                         executor (live exits at the open) · strategist
    15:40 ET  afternoon  analyst (events in the decision window) ·
                         executor (entries land ~15:45-15:58, just before close)
    16:50 ET  evening    executor (same-day after-hours AMC exits — only when
                         the PDT budget allows; otherwise positions ride to
                         the next open)

    python -m orchestrator.daily [--phase morning|afternoon|evening|auto] [--dry-run]
"""

from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta

from engine.arming import arm_status
from engine.config import Config
from engine.store import Store

from . import launcher

STRATEGIST_MIN_NEW_OUTCOMES = 3
MAX_DAY_TRADES_PER_5D = 3  # PDT rule for accounts under $25k


def next_trading_day(d: date) -> date:
    nxt = d + timedelta(days=1)
    while nxt.weekday() >= 5:
        nxt += timedelta(days=1)
    return nxt


def analyst_due(report_date: str, timing: str, today: date) -> bool:
    """Decision window (afternoon tick): AMC events are decided and entered on
    the report day itself (report lands after the close). BMO/unknown events
    are decided the prior trading day (entry T-1 near close, report before the
    next open). Weekends: markets closed, nothing is due."""
    if today.weekday() >= 5:
        return False
    d = date.fromisoformat(report_date)
    if timing == "amc":
        return d == today
    return d == next_trading_day(today)


def resolve_phase(now: datetime) -> str:
    if now.hour < 12:
        return "morning"
    if now.hour < 16 or (now.hour == 16 and now.minute < 15):
        return "afternoon"
    return "evening"


def _skip_reanalysis(store: Store, event, policy_version: str) -> bool:
    """Skip an event that already has a decision — unless every decision on it
    is a pass from an older policy version (strategy changed; re-look)."""
    decisions = store.decisions_for_event(event["id"])
    if not decisions:
        return False
    return any(
        d["action"] != "pass" or d["policy_version"] == policy_version
        for d in decisions
    )


def tick(*, phase: str = "auto", run_scout: bool = True, dry_run: bool = False,
         model: str = launcher.DEFAULT_MODEL) -> int:
    today = date.today()
    if phase == "auto":
        phase = resolve_phase(datetime.now())
    print(f"=== {phase} tick {today.isoformat()} (model={model}"
          + (", DRY RUN" if dry_run else "") + ") ===")

    cfg = Config.from_env()
    store = Store(cfg.db_path)
    arm, arm_why = arm_status()
    try:
        if phase == "morning":
            if run_scout:
                if dry_run:
                    print("scout: would run")
                else:
                    print(f"scout exit {launcher.run_role('scout', model=model)}")

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

            live_closes = store.due_live_closes(today.isoformat())
            if live_closes and arm:
                job = "sell to close at the open (decision_id symbol): " + ", ".join(
                    f"#{r['id']} {r['symbol']}" for r in live_closes)
                print(f"executor (ARMED until {arm.expires}): {job}")
                if not dry_run:
                    print(f"executor exit {launcher.run_role('executor', symbol=job, model=model)}")
            elif live_closes:
                print(f"executor: {len(live_closes)} live close(s) due but {arm_why} "
                      "— MANUAL ACTION NEEDED (positions are real)")
            else:
                print("executor: no live exits due")

            n = store.outcome_count()
            last = int(store.meta_get("strategist_outcome_count", "0") or 0)
            if n - last >= STRATEGIST_MIN_NEW_OUTCOMES:
                print(f"strategist: {n - last} new labeled outcomes — running policy review")
                if not dry_run:
                    print(f"strategist exit {launcher.run_role('strategist', model=model)}")
                    store.meta_set("strategist_outcome_count", str(n))
            else:
                print(f"strategist: {n - last} new outcomes since last review "
                      f"(<{STRATEGIST_MIN_NEW_OUTCOMES}) — skip")

        elif phase == "afternoon":
            if today.weekday() >= 5:
                print("weekend — no entries; done")
                return 0
            ran = 0
            for e in store.upcoming_events(days=5):
                if not analyst_due(e["report_date"], e["timing"], today):
                    continue
                if _skip_reanalysis(store, e, cfg.policy_version):
                    print(f"analyst: {e['symbol']} {e['report_date']} already decided — skip")
                    continue
                ran += 1
                print(f"analyst: {e['symbol']} {e['report_date']} ({e['timing']}) is due")
                if not dry_run:
                    rc = launcher.run_role("analyst", symbol=e["symbol"], model=model)
                    print(f"analyst({e['symbol']}) exit {rc}")
            if ran == 0:
                print("analyst: no events in the decision window")

            pending = store.pending_executions()
            if pending and arm:
                job = ("buy before the close (decision_id symbol $size @ref): "
                       + ", ".join(f"#{r['id']} {r['symbol']} ${r['size_usd']:,.0f} "
                                   f"@{r['entry_price']}" for r in pending))
                print(f"executor (ARMED until {arm.expires}): {job}")
                if not dry_run:
                    print(f"executor exit {launcher.run_role('executor', symbol=job, model=model)}")
            elif pending:
                print(f"executor: {len(pending)} pending buy(s) but {arm_why} — nothing executes")
            else:
                print("executor: no entries pending")

        elif phase == "evening":
            candidates = store.due_amc_same_day_closes(today.isoformat())
            if not candidates:
                print("executor: no same-day AMC exits to consider")
                return 0
            used = store.day_trades_last_5d()
            if used + len(candidates) > MAX_DAY_TRADES_PER_5D:
                print(f"executor: {len(candidates)} AMC exit(s) available but PDT "
                      f"budget is {used}/{MAX_DAY_TRADES_PER_5D} — holding to the "
                      "next open instead (morning tick will exit)")
                return 0
            if not arm:
                print(f"executor: same-day exits due but {arm_why} — positions "
                      "ride to the next open")
                return 0
            job = ("sell to close in after-hours (extended-hours order; "
                   "decision_id symbol): "
                   + ", ".join(f"#{r['id']} {r['symbol']}" for r in candidates))
            print(f"executor (ARMED until {arm.expires}, PDT {used}/{MAX_DAY_TRADES_PER_5D}): {job}")
            if not dry_run:
                print(f"executor exit {launcher.run_role('executor', symbol=job, model=model)}")
        else:
            print(f"unknown phase {phase!r}")
            return 2
    finally:
        store.close()
    print("tick complete")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="orchestrator.daily")
    parser.add_argument("--phase", default="auto",
                        choices=["auto", "morning", "afternoon", "evening"])
    parser.add_argument("--no-scout", action="store_true", help="skip the scout run")
    parser.add_argument("--dry-run", action="store_true", help="print plan, launch no agents")
    parser.add_argument("--model", default=launcher.DEFAULT_MODEL)
    args = parser.parse_args(argv)
    return tick(phase=args.phase, run_scout=not args.no_scout,
                dry_run=args.dry_run, model=args.model)


if __name__ == "__main__":
    raise SystemExit(main())
