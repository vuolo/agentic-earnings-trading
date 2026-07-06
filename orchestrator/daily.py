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
import json
from datetime import date, datetime, timedelta

from engine.arming import arm_status
from engine.config import Config
from engine.store import Store

from . import launcher

STRATEGIST_MIN_NEW_OUTCOMES = 3

# NYSE full-close holidays 2026. Half days (2026-11-27, 2026-12-24) close at
# 13:00 — our 15:40 entry window doesn't exist, so treat them as non-entry too.
MARKET_HOLIDAYS = {
    "2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03", "2026-05-25",
    "2026-06-19", "2026-07-03", "2026-09-07", "2026-11-26", "2026-12-25",
}
HALF_DAYS = {"2026-11-27", "2026-12-24"}


def is_trading_day(d: date, *, full_session: bool = False) -> bool:
    if d.weekday() >= 5 or d.isoformat() in MARKET_HOLIDAYS:
        return False
    return not (full_session and d.isoformat() in HALF_DAYS)


def next_trading_day(d: date) -> date:
    nxt = d + timedelta(days=1)
    while not is_trading_day(nxt):
        nxt += timedelta(days=1)
    return nxt


def analyst_due(report_date: str, timing: str, today: date) -> bool:
    """Decision window (afternoon tick): AMC events are decided and entered on
    the report day itself (report lands after the close). BMO/unknown events
    are decided the prior trading day (entry T-1 near close, report before the
    next open). Non-trading days (and half days, whose 13:00 close removes our
    entry window): nothing is due."""
    if not is_trading_day(today, full_session=True):
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


def _write_briefing(cfg: Config, store: Store) -> None:
    """Regenerate the operator briefing and commit it (best-effort)."""
    import subprocess

    from .briefing import build_briefing
    from .launcher import REPO_ROOT

    out = REPO_ROOT / "reports" / "BRIEFING.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text(build_briefing(cfg, store))
    print(f"briefing → {out}")
    r = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "commit", "-m",
         f"briefing: {date.today().isoformat()}", "--", "reports/BRIEFING.md"],
        capture_output=True, text=True,
    )
    if r.returncode != 0 and "nothing to commit" not in (r.stdout + r.stderr):
        print(f"briefing commit skipped: {(r.stderr or r.stdout).strip()[:120]}")


def tick(*, phase: str = "auto", run_scout: bool = True, dry_run: bool = False,
         model: str | None = None) -> int:
    today = date.today()
    if phase == "auto":
        phase = resolve_phase(datetime.now())
    print(f"=== {phase} tick {today.isoformat()} (model={model or launcher.DEFAULT_MODEL}"
          + (", DRY RUN" if dry_run else "") + ") ===")

    cfg = Config.from_env()
    store = Store(cfg.db_path)
    arm, arm_why = arm_status()
    try:
        _phase_body(phase=phase, run_scout=run_scout, dry_run=dry_run,
                    model=model, today=today, cfg=cfg, store=store,
                    arm=arm, arm_why=arm_why)
        if not dry_run:
            store.meta_set(f"tick_{phase}_last",
                           datetime.now().isoformat(timespec="seconds"))
            store.meta_set("last_tick_error", "")
    except Exception as e:
        msg = f"{phase} tick {today.isoformat()}: {type(e).__name__}: {e}"
        try:
            store.meta_set("last_tick_error", msg)
        except Exception:
            pass
        _notify(f"earnings tick FAILED: {msg[:120]}")
        raise
    finally:
        store.close()
    print("tick complete")
    return 0


def _notify(text: str) -> None:
    """Best-effort macOS notification so tick failures aren't silent."""
    import subprocess
    try:
        subprocess.run(
            ["osascript", "-e",
             f'display notification {json.dumps(text)} with title "agentic-earnings-trading"'],
            capture_output=True, timeout=10,
        )
    except Exception:
        pass


def _phase_body(*, phase, run_scout, dry_run, model, today, cfg, store, arm, arm_why):
    if True:  # keep original indentation depth for the phase blocks below
        if phase == "morning":
            if dry_run:
                print("monitor: would report account snapshot + reconcile")
            else:
                print(f"monitor exit {launcher.run_role('monitor')}")

            if run_scout:
                if dry_run:
                    print("scout: would run")
                else:
                    print(f"scout exit {launcher.run_role('scout', model=model)}")

            # Monday: refresh backtests for events that just happened, so the
            # realized rows (incl. post_close) stay complete.
            if today.weekday() == 0:
                week_ago = (today - timedelta(days=7)).isoformat()
                recent = store._db.execute(
                    "SELECT DISTINCT symbol FROM events WHERE report_date >= ? "
                    "AND report_date < ?", (week_ago, today.isoformat()),
                ).fetchall()
                if recent:
                    syms = ", ".join(r["symbol"] for r in recent)
                    print(f"backtester: refreshing realized events for {syms}")
                    if not dry_run:
                        print(f"backtester exit "
                              f"{launcher.run_role('backtester', symbol=syms, model=model)}")

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
                job = ("close at the open — sell for long_equity, buy-to-cover "
                       "for short_equity (decision_id symbol action): "
                       + ", ".join(f"#{r['id']} {r['symbol']} {r['action']}"
                                   for r in live_closes))
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

            if dry_run:
                print("ml: would attempt training (auto-activates at threshold)")
                print("briefing: would write + commit reports/BRIEFING.md")
            else:
                from engine import ml
                st = ml.train(store)
                if st.get("trained"):
                    print(f"ml: trained on {st['rows']} rows, CV accuracy "
                          f"{st['cv_accuracy']:.0%}")
                else:
                    print(f"ml: {st.get('reason', 'skipped')}")
                _write_briefing(cfg, store)

        elif phase == "afternoon":
            if not is_trading_day(today, full_session=True):
                print("market closed (weekend/holiday/half-day) — no entries; done")
                return
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
                job = ("open positions before the close — buy for long_equity, "
                       "sell-short for short_equity (decision_id symbol action "
                       "$size @ref): "
                       + ", ".join(f"#{r['id']} {r['symbol']} {r['action']} "
                                   f"${r['size_usd']:,.0f} @{r['entry_price']}"
                                   for r in pending))
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
                return
            # Settlement guard, by account type:
            # - cash: GFV — if a live close already happened today, today's
            #   entry was proceeds-funded; re-selling it today is a violation.
            # - margin: PDT — max 3 same-day round trips per 5 trading days
            #   under $25k equity.
            acct_type = store.meta_get("account_type", "cash")
            if acct_type == "cash" and store.live_closes_today():
                print(f"executor: {len(candidates)} AMC exit(s) available but a live "
                      "close already happened today — same-day re-sale of proceeds "
                      "risks a good-faith violation (cash account); holding to the "
                      "next open")
                return
            if acct_type == "margin":
                used = store.day_trades_last_5d()
                if used + len(candidates) > 3:
                    print(f"executor: {len(candidates)} AMC exit(s) available but "
                          f"PDT budget is {used}/3 (margin account under $25k) — "
                          "holding to the next open")
                    return
            if not arm:
                print(f"executor: same-day exits due but {arm_why} — positions "
                      "ride to the next open")
                return
            job = ("sell to close in after-hours (extended-hours LIMIT, whole "
                   "shares only — skip any position with a fractional part; "
                   "decision_id symbol): "
                   + ", ".join(f"#{r['id']} {r['symbol']}" for r in candidates))
            print(f"executor (ARMED until {arm.expires}): {job}")
            if not dry_run:
                print(f"executor exit {launcher.run_role('executor', symbol=job, model=model)}")
        else:
            raise ValueError(f"unknown phase {phase!r}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="orchestrator.daily")
    parser.add_argument("--phase", default="auto",
                        choices=["auto", "morning", "afternoon", "evening"])
    parser.add_argument("--no-scout", action="store_true", help="skip the scout run")
    parser.add_argument("--dry-run", action="store_true", help="print plan, launch no agents")
    parser.add_argument("--model", default=None)
    args = parser.parse_args(argv)
    return tick(phase=args.phase, run_scout=not args.no_scout,
                dry_run=args.dry_run, model=args.model)


if __name__ == "__main__":
    raise SystemExit(main())
