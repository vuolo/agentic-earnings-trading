"""Market-phase ticks: morning (exits) / afternoon (entries) / evening (AMC exits).

The orchestration logic is deterministic — agents run only where judgment is
needed. launchd fires three times per trading day (orchestrator/schedule.py):

    09:24 ET  morning    executor FIRST (exit orders placed pre-open, filling
                         in the 9:30 opening auction) · monitor · scout ·
                         labeler (paper closes + pass labels) · strategist
    15:30 ET  afternoon  analysts in PARALLEL (x4, deadline-aware) · executor
                         dispatched so orders PLACE inside 15:45-15:58
    16:50 ET  evening    executor (same-day after-hours AMC exits — only when
                         the PDT budget allows; otherwise positions ride to
                         the next open)

Every phase is safe to re-fire (wake-from-sleep replays, RunAtLoad catch-up
after a reboot/login): morning is verify-only once completed, afternoon
refuses to run outside its 15:25-15:58 window, evening re-verifies queued
exits idempotently.

    python -m orchestrator.daily [--phase morning|afternoon|evening|auto] [--dry-run]
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import threading
import time as time_mod
from datetime import date, datetime, time as dtime, timedelta, timezone
from pathlib import Path

from engine.arming import arm_status
from engine.config import Config
from engine.store import Store

from . import launcher

STRATEGIST_MIN_NEW_OUTCOMES = 3
# Ceiling on the Monday realized-backtest refresh. One agent run has a 22-min
# hard timeout; an unbounded list silently blows it (295 symbols -> exit 124,
# 2026-07-27) and refreshes nothing at all.
BACKTEST_REFRESH_MAX = 40

# Afternoon entry clock (local wall clock = ET on this host). The window is
# hard: orders must be PLACED inside the policy's 15:45-15:58 entry window.
# Sequential analyst runs (~5 min each) put the executor at ~16:05-16:09 on
# every multi-event day — 9 straight days of exec_failed live entries,
# 2026-07-13..07-22 — hence parallel analysts + deadline-aware dispatch.
ANALYST_WORKERS = 4
ENTRY_PIPELINE_OPEN = dtime(15, 25)    # entry pipeline runs only inside
ENTRY_PIPELINE_CLOSE = dtime(15, 58)   # [OPEN, CLOSE) — late wake-refire skips
BACKFILL_CUTOFF = dtime(15, 38)        # a backtester run later than this eats the window
ANALYST_START_CUTOFF = dtime(15, 50)   # an analyst STARTING later can't land in time
EXEC_NOT_BEFORE = dtime(15, 43)        # boot+quote ≈ 2 min → first order ~15:45
EXEC_VALVE = dtime(15, 50)             # dispatch what's pending even if analysts lag
EXEC_LAST_LAUNCH = dtime(15, 54)       # launched later, orders can't beat 15:58


def in_entry_window(now_t: dtime) -> bool:
    return ENTRY_PIPELINE_OPEN <= now_t < ENTRY_PIPELINE_CLOSE

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


def edge_rank(store: Store, event, core: bool) -> tuple:
    """Sort key for the day's capped analyst slots: core names first, then by
    historical mean absolute gap (the payoff proxy for a gap-capture
    strategy), with the screen's avg volume as the tiebreak — raw volume says
    nothing about how far a name moves on its print. Names without gap
    history rank at edge 0 (backfill happens after selection)."""
    vol = 0.0
    if event["screen"]:
        try:
            vol = float(json.loads(event["screen"]).get("avg_volume", 0))
        except (ValueError, TypeError):
            pass
    gap = store.backtest_summary(event["symbol"])["gap_t1close_to_postopen"] or {}
    edge = float(gap.get("mean_abs_pct") or 0.0)
    return (0 if core else 1, -edge, -vol)


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


def _prewarm() -> None:
    """Materialize iCloud-evicted venv/dataset files BEFORE anything is on a
    clock. MaterializeDatalessFiles fixed the hard errno-11 crash but made
    re-download lazy — on freshly-woken Wi-Fi it can exceed the FIXED 60s
    MCP initialize timeout, producing tool-less agents that exit 0 (sibling
    stake-synthetics finding, 2026-07-06). A multi-second prewarm duration
    is the telltale that eviction happened overnight."""
    import subprocess as sp
    import sys
    import time
    t0 = time.monotonic()
    venv_py = str((Path(__file__).resolve().parents[1]) / ".venv" / "bin" / "python")
    try:
        sp.run([venv_py, "-c",
                "import numpy, sklearn.linear_model, pydantic, "
                "mcp.server.fastmcp, engine.store, engine.indicators"],
               capture_output=True, timeout=600)
        db = Path(__file__).resolve().parents[1] / "datasets" / "earnings.sqlite3"
        if db.exists():
            db.read_bytes()
    except Exception as e:
        print(f"prewarm: WARNING — {type(e).__name__}: {e}")
    dur = time.monotonic() - t0
    print(f"prewarm: {dur:.1f}s" + ("  (⚠ slow — iCloud eviction likely re-materialized)"
                                    if dur > 10 else ""))



def _run_with_evidence(store: Store, role: str, *, symbol: str | None = None,
                       model: str | None = None) -> int:
    """run_role + tool-less-run detection: every real agent run boots our
    gateway, which stamps meta gateway_last_boot. No stamp after the run
    started ⇒ the MCP handshake failed (agent had no tools; exit 0 is
    meaningless) ⇒ retry once — everything is warm the second time."""
    start = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rc = launcher.run_role(role, symbol=symbol, model=model)
    if store.meta_get("gateway_last_boot", "") >= start:
        return rc
    print(f"{role}: NO GATEWAY BOOT EVIDENCE (tool-less run, exit {rc}) — "
          "retrying once warm")
    start = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rc = launcher.run_role(role, symbol=symbol, model=model)
    if store.meta_get("gateway_last_boot", "") < start:
        print(f"{role}: retry ALSO produced no gateway boot — giving up "
              "(check MCP/venv health)")
        store.meta_set("last_tick_error",
                       f"{role}: tool-less agent runs (gateway never booted)")
    return rc


def _analyst_job(db_path, event_id: int, symbol: str, model: str | None) -> tuple[int, bool]:
    """One analyst run in a worker thread, with per-run landed-decision
    evidence: the global gateway_last_boot stamp _run_with_evidence uses is
    racy under parallel runs (any sibling's gateway boot would mask this
    run's failure), so the evidence here is a decision row for THIS event
    created after the run started. No row ⇒ retry once (window permitting).
    Opens its own Store — sqlite connections are not shareable across
    threads. Returns (exit code, decision landed)."""
    if datetime.now().time() >= ANALYST_START_CUTOFF:
        return -1, False  # too late to start: could not land before the close
    for attempt in (1, 2):
        start = datetime.now(timezone.utc).isoformat(timespec="seconds")
        rc = launcher.run_role("analyst", symbol=symbol, model=model, quiet=True)
        s = Store(db_path)
        try:
            landed = any((d["created_at"] or "") >= start
                         for d in s.decisions_for_event(event_id))
        finally:
            s.close()
        if landed:
            return rc, True
        if attempt == 1 and datetime.now().time() < ANALYST_START_CUTOFF:
            print(f"analyst({symbol}): NO decision landed (exit {rc}) — retrying once")
            continue
        return rc, False
    return rc, False


def _reconcile_live_fills(store: Store, *, arm, arm_why: str, today: date,
                          model: str | None) -> None:
    """Report auction fills for positions the pre-open run couldn't close.

    Runs late in the morning tick, after the auction. Launches the executor
    with a REPORT-ONLY job (it reads get_equity_orders and calls
    report_live_close for exits that already filled), then re-checks. Anything
    still open_live afterwards is a genuine unfilled exit or a broken run:
    that sets `exit_reconcile_needed` and notifies, because a live position
    riding unhedged is the one failure that must never be silent.
    """
    due = store.due_live_closes(today.isoformat())
    if not due:
        store.meta_set("exit_reconcile_needed", "")
        print("reconcile: no live exits outstanding")
        return
    ids = ", ".join(f"#{r['id']} {r['symbol']}" for r in due)
    if not arm:
        print(f"reconcile: {len(due)} position(s) unreported but {arm_why} "
              "— MANUAL ACTION NEEDED (positions are real)")
        store.meta_set("exit_reconcile_needed", ids)
        _notify(f"earnings: live exits unreported and {arm_why}: {ids}"[:120])
        return

    job = ("RECONCILE FILLS ONLY (the opening auction has passed; place no new "
           "orders unless a position has NO close order at all) — for each: "
           "get_equity_orders, and if its close order shows filled, "
           "report_live_close with the actual average fill price "
           "(decision_id symbol action): "
           + ", ".join(f"#{r['id']} {r['symbol']} {r['action']}" for r in due))
    print(f"reconcile executor (ARMED until {arm.expires}): {ids}")
    print(f"reconcile executor exit "
          f"{_run_with_evidence(store, 'executor', symbol=job, model=model)}")

    still = store.due_live_closes(today.isoformat())
    if still:
        left = ", ".join(f"#{r['id']} {r['symbol']}" for r in still)
        msg = (f"live exits STILL unreported after reconcile: {left} — either "
               "the exit never filled (position is riding unhedged) or the "
               "report failed; needs manual reconciliation")
        print(f"reconcile: ⚠ {msg}")
        # Dedicated key: tick() clears last_tick_error on a clean phase, so it
        # cannot carry this. Persists until a later run records the fills.
        store.meta_set("exit_reconcile_needed", left)
        _notify(f"earnings: {msg[:120]}")
    else:
        store.meta_set("exit_reconcile_needed", "")
        print("reconcile: all live exits recorded")


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

    _prewarm()
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
            # RunAtLoad catch-up fires (reboot/login) can arrive at any hour;
            # a middle-of-the-night morning pass would label outcomes on stale
            # quotes. Anything 07:00+ is fine (exits placed pre-open fill in
            # the same 9:30 auction as the 9:24 fire's would).
            if not dry_run and datetime.now().hour < 7:
                print("morning: before 07:00 — deferring to the scheduled fire")
                return
            if (not dry_run and
                    store.meta_get("tick_morning_last", "")[:10] == today.isoformat()):
                # Backup/re-fires are cheap: today's morning work is done —
                # only re-verify that live exits are handled.
                print("morning already completed today — verify-only pass")
                due_v = store.due_live_closes(today.isoformat())
                if due_v and arm:
                    job = ("close at the open — verify/place (decision_id symbol "
                           "action): " + ", ".join(
                               f"#{r['id']} {r['symbol']} {r['action']}" for r in due_v))
                    print(f"executor exit {_run_with_evidence(store, 'executor', symbol=job, model=model)}")
                else:
                    print("no live exits pending — done")
                return
            # LIVE EXITS FIRST — the intraday study (2026-07-05) showed the
            # post-earnings fade is front-loaded: winners average -2.7% from
            # the open by 10:00. Every minute between 9:31 and the sell costs
            # money; monitor/scout/labeler all wait.
            live_closes = store.due_live_closes(today.isoformat())
            if live_closes and arm:
                job = ("close INTO THE OPENING AUCTION (place market orders "
                       "NOW, pre-open, so they fill in the 9:30 cross) — sell "
                       "for long_equity, buy-to-cover for short_equity "
                       "(decision_id symbol action): "
                       + ", ".join(f"#{r['id']} {r['symbol']} {r['action']}"
                                   for r in live_closes))
                print(f"executor (ARMED until {arm.expires}): {job}")
                if not dry_run:
                    print(f"executor exit {_run_with_evidence(store, 'executor', symbol=job, model=model)}")
            elif live_closes:
                print(f"executor: {len(live_closes)} live close(s) due but {arm_why} "
                      "— MANUAL ACTION NEEDED (positions are real)")
            else:
                print("executor: no live exits due")

            if dry_run:
                print("monitor: would report account snapshot + reconcile")
            else:
                print(f"monitor exit {_run_with_evidence(store, 'monitor')}")

            if run_scout:
                if dry_run:
                    print("scout: would run")
                else:
                    print(f"scout exit {_run_with_evidence(store, 'scout', model=model)}")

            # Monday: refresh backtests for events that just happened, so the
            # realized rows (incl. post_close) stay complete. Scoped to symbols
            # we actually DECIDED on: those are the rows that feed training,
            # the playbook and the strategist. Since the v0.6.0 market-wide
            # expansion the unscoped query returned every calendar name (295 on
            # 2026-07-27), which no single 22-min run can process — it timed
            # out at exit 124, refreshed nothing, and ate the tick's clock.
            if today.weekday() == 0:
                week_ago = (today - timedelta(days=7)).isoformat()
                recent = store._db.execute(
                    """SELECT DISTINCT e.symbol FROM events e
                       JOIN decisions d ON d.event_id = e.id
                       WHERE e.report_date >= ? AND e.report_date < ?
                       ORDER BY e.symbol""",
                    (week_ago, today.isoformat()),
                ).fetchall()
                syms_list = [r["symbol"] for r in recent][:BACKTEST_REFRESH_MAX]
                if syms_list:
                    syms = ", ".join(syms_list)
                    print(f"backtester: refreshing realized events for {syms}")
                    if not dry_run:
                        print(f"backtester exit "
                              f"{_run_with_evidence(store, 'backtester', symbol=syms, model=model)}")
                else:
                    print("backtester: no decided events in the past week — skip")

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
                    print(f"labeler exit {_run_with_evidence(store, 'labeler', symbol=job, model=model)}")
            else:
                print("labeler: nothing due")

            n = store.outcome_count()
            last = int(store.meta_get("strategist_outcome_count", "0") or 0)
            if n - last >= STRATEGIST_MIN_NEW_OUTCOMES:
                print(f"strategist: {n - last} new labeled outcomes — running policy review")
                if not dry_run:
                    print(f"strategist exit {_run_with_evidence(store, 'strategist', model=model)}")
                    store.meta_set("strategist_outcome_count", str(n))
            else:
                print(f"strategist: {n - last} new outcomes since last review "
                      f"(<{STRATEGIST_MIN_NEW_OUTCOMES}) — skip")

            # FILL RECONCILIATION — deterministic, and deliberately LAST.
            # The 9:24 executor runs pre-open: it can place/verify the exit
            # order but cannot report a fill that hasn't happened yet. Asking
            # the agent to block until 9:31 does NOT work: on 2026-07-27 it
            # announced "Timer running; I'll poll once it fires just past 9:31"
            # and the run ended anyway, leaving HOPE/AZN phantom-open exactly
            # like VZ/NEM/EW on 07-24. A `claude -p` run cannot be relied on to
            # sleep for minutes. So the orchestrator owns the timing instead:
            # by the time monitor/scout/labeler/strategist have run, the
            # auction is long past, and THIS run only has to read
            # get_equity_orders and report what already filled.
            if not dry_run:
                _reconcile_live_fills(store, arm=arm, arm_why=arm_why,
                                      today=today, model=model)

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
            # Window guard: the entry pipeline only makes sense just before
            # the close. A late fire (wake-from-sleep replay, RunAtLoad
            # catch-up after a reboot/login) must not analyze at 12:30 or
            # enter at 16:10. Dry runs bypass so the plan can be previewed.
            now_t = datetime.now().time()
            if not dry_run and not in_entry_window(now_t):
                print(f"afternoon: {now_t.strftime('%H:%M')} is outside the "
                      f"entry window {ENTRY_PIPELINE_OPEN.strftime('%H:%M')}-"
                      f"{ENTRY_PIPELINE_CLOSE.strftime('%H:%M')} ET (late "
                      "wake or catch-up fire) — no entries possible; done")
                return
            # Candidate selection (market-wide): core names always; non-core
            # only if screened-in. Core first, then by historical mean |gap|
            # (edge_rank — volume only breaks ties). Hard cap on analyst runs
            # per day (agent cost + entry budget).
            max_runs = int(os.environ.get("EARNINGS_MAX_ANALYST_RUNS", "6"))
            due, seen = [], set()
            for e in store.upcoming_events(days=5):
                if not analyst_due(e["report_date"], e["timing"], today):
                    continue
                if e["symbol"] in seen or e["symbol"] in cfg.macro_watch:
                    continue
                seen.add(e["symbol"])
                core = e["symbol"] in cfg.universe
                if not core and not e["screened"]:
                    continue
                due.append((*edge_rank(store, e, core), e))
            due.sort(key=lambda t: t[:3])
            if len(due) > max_runs:
                dropped = ", ".join(e["symbol"] for *_, e in due[max_runs:])
                print(f"analyst: capping at {max_runs} runs — dropped: {dropped}")
                due = due[:max_runs]

            # Non-core names need gap history before the analyst can align
            # with it — one batched backtester run for any that lack rows.
            need_bt = [e["symbol"] for *_, e in due
                       if e["symbol"] not in cfg.universe
                       and store.backtest_summary(e["symbol"])["events"] == 0]
            if need_bt:
                syms = ", ".join(sorted(set(need_bt)))
                if datetime.now().time() >= BACKFILL_CUTOFF and not dry_run:
                    # A backtester run here (up to 22 min) would eat the entry
                    # window. Un-backfilled names rank at edge 0 anyway; the
                    # morning tick refreshes history for realized events.
                    print(f"backtester: SKIPPED (past "
                          f"{BACKFILL_CUTOFF.strftime('%H:%M')} — window "
                          f"priority) — {syms}")
                else:
                    print(f"backtester: backfilling new names first — {syms}")
                    if not dry_run:
                        print(f"backtester exit {_run_with_evidence(store, 'backtester', symbol=syms, model=model)}")

            jobs = []
            for *_, e in due:
                if _skip_reanalysis(store, e, cfg.policy_version):
                    print(f"analyst: {e['symbol']} {e['report_date']} already decided — skip")
                    continue
                jobs.append(e)
                print(f"analyst: {e['symbol']} {e['report_date']} ({e['timing']}) is due")
            if not jobs:
                print("analyst: no events in the decision window")

            # Stale-pending guard: a pending_live decision from a PRIOR day
            # means a run died between approval and execution. Its entry
            # window is gone — executing a day late is a different trade.
            # Expire it; never execute it.
            pending = store.pending_executions()
            from engine.store import _today as _utc_today
            for r in pending:
                if r["created_at"][:10] != _utc_today():
                    store.mark_execution(
                        r["id"], filled=False,
                        detail="stale — entry window passed without execution "
                               "(prior run died); expired by tick guard",
                    )
                    print(f"expired stale pending #{r['id']} {r['symbol']} "
                          f"(created {r['created_at'][:10]})")

            if dry_run:
                if jobs:
                    print(f"analyst: would run {len(jobs)} in parallel "
                          f"(x{ANALYST_WORKERS}): "
                          + ", ".join(e["symbol"] for e in jobs))
                pending = store.pending_executions()
                if pending and arm:
                    print("executor: would dispatch "
                          + ", ".join(f"#{r['id']} {r['symbol']}" for r in pending))
                elif pending:
                    print(f"executor: {len(pending)} pending buy(s) but "
                          f"{arm_why} — nothing would execute")
                else:
                    print("executor: no entries pending")
                return

            # PARALLEL analysts + deadline-aware executor dispatch. Decisions
            # stream into pending_executions as analysts finish; the executor
            # is dispatched with everything undispatched once analysts are
            # done (or at the 15:50 valve if they lag), never before 15:43,
            # never after 15:54. Disjoint kickoff ID lists keep concurrent
            # executor sweeps from ever double-ordering a decision (the
            # executor hard-rule: only kickoff-named jobs).
            dispatched: set[int] = set()
            exec_threads: list[threading.Thread] = []

            def _undispatched():
                return [r for r in store.pending_executions()
                        if r["id"] not in dispatched]

            def _try_dispatch():
                if not arm:
                    return
                now = datetime.now().time()
                if not (EXEC_NOT_BEFORE <= now <= EXEC_LAST_LAUNCH):
                    return
                rows = _undispatched()
                if not rows:
                    return
                dispatched.update(r["id"] for r in rows)
                job = ("open positions before the close — buy for long_equity, "
                       "sell-short for short_equity (decision_id symbol action "
                       "$size @ref): "
                       + ", ".join(f"#{r['id']} {r['symbol']} {r['action']} "
                                   f"${r['size_usd']:,.0f} @{r['entry_price']}"
                                   for r in rows))
                print(f"executor (ARMED until {arm.expires}): {job}")
                t = threading.Thread(
                    target=lambda: print(
                        f"executor exit "
                        f"{launcher.run_role('executor', symbol=job, model=model, quiet=True)}"))
                t.start()
                exec_threads.append(t)

            if jobs:
                print(f"analyst: launching {len(jobs)} in parallel "
                      f"(x{ANALYST_WORKERS})")
            pool = concurrent.futures.ThreadPoolExecutor(max_workers=ANALYST_WORKERS)
            futs = {pool.submit(_analyst_job, cfg.db_path, e["id"],
                                e["symbol"], model): e["symbol"]
                    for e in jobs}
            not_done = set(futs)
            while not_done:
                done, not_done = concurrent.futures.wait(not_done, timeout=15)
                for f in done:
                    sym = futs[f]
                    try:
                        rc, landed = f.result()
                    except Exception as ex:  # a crashed job must not kill the tick
                        print(f"analyst({sym}) CRASHED: {type(ex).__name__}: {ex}")
                        continue
                    if rc == -1:
                        print(f"analyst({sym}) skipped — past "
                              f"{ANALYST_START_CUTOFF.strftime('%H:%M')} start cutoff")
                    else:
                        print(f"analyst({sym}) exit {rc}"
                              + ("" if landed else " — NO decision landed"))
                now = datetime.now().time()
                if not not_done or now >= EXEC_VALVE:
                    _try_dispatch()
                if not_done and now >= ENTRY_PIPELINE_CLOSE:
                    print(f"analyst: window closed — not waiting on "
                          f"{len(not_done)} straggler(s)")
                    break
            pool.shutdown(wait=False, cancel_futures=True)

            # Wait for the window if analysts finished early, then sweep, and
            # sweep once more for decisions that landed during the first sweep.
            while arm and _undispatched() and datetime.now().time() < EXEC_NOT_BEFORE:
                time_mod.sleep(10)
            _try_dispatch()
            for t in exec_threads:
                t.join()
            _try_dispatch()
            for t in exec_threads:
                t.join()

            # Same-day expiry: whatever is still pending now cannot be placed
            # inside the window (executor failed, landed too late, or not
            # armed). Never let it ride to another day.
            leftover = store.pending_executions()
            for r in leftover:
                store.mark_execution(
                    r["id"], filled=False,
                    detail="entry window closed before execution — expired "
                           "same day by tick guard"
                           + ("" if arm else f" ({arm_why})"),
                )
                print(f"expired pending #{r['id']} {r['symbol']} — not "
                      "executed in window" + ("" if arm else f" ({arm_why})"))
            if not exec_threads and not leftover:
                print("executor: no entries pending")

        elif phase == "evening":
            # Evening runs (16:20 + 16:50) do two jobs per open live position
            # due at the next open:
            #  1. QUEUE the auction exit now — a market sell placed after the
            #     close fills in tomorrow's 9:30 opening cross even if the
            #     morning tick never fires (crash/sleep-proof exits).
            #  2. DISASTER VALVE (16:50 run only; never 16:20 — peak whipsaw,
            #     e.g. CRDO -11.75% at 16:20 recovered to -3.12% by the open):
            #     persistent AH loss >= 10% → exit immediately, GFV/settlement
            #     permitting.
            nxt = next_trading_day(today)
            due = store.due_live_closes(nxt.isoformat())
            if not due:
                print("executor: no open live positions due at the next open")
                return
            if not arm:
                print(f"executor: {len(due)} position(s) due at next open but "
                      f"{arm_why} — nothing queued")
                return
            acct_type = store.meta_get("account_type", "cash")
            gfv_blocked = acct_type == "cash" and store.live_closes_today() > 0
            is_late_run = datetime.now().hour * 60 + datetime.now().minute >= 16 * 60 + 45
            valve = ("DISABLED this run (16:20 window is peak whipsaw — queue only)"
                     if not is_late_run else
                     "UNAVAILABLE (cash-account GFV: a live close already happened today)"
                     if gfv_blocked else "ARMED (>=10% persistent AH loss)")
            job = (f"queue auction exits; disaster valve {valve} "
                   "(decision_id symbol action entry): "
                   + ", ".join(f"#{r['id']} {r['symbol']} {r['action']} @{r['entry_price']}"
                               for r in due))
            print(f"executor (ARMED until {arm.expires}): {job}")
            if not dry_run:
                print(f"executor exit {_run_with_evidence(store, 'executor', symbol=job, model=model)}")
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
