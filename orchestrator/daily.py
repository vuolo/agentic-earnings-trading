"""Market-phase ticks: morning (exits) / afternoon (entries) / evening (AMC exits).

The orchestration logic is deterministic — agents run only where judgment is
needed. launchd fires three times per trading day (orchestrator/schedule.py):

    09:24 ET  morning    executor FIRST (exit orders placed pre-open, filling
                         in the 9:30 opening auction) · monitor · scout ·
                         labeler (paper closes + pass labels) · strategist
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
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

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
                              f"{_run_with_evidence(store, 'backtester', symbol=syms, model=model)}")

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
            # Candidate selection (market-wide): core names always; non-core
            # only if screened-in. Core first, then screened by avg volume.
            # Hard cap on analyst runs per day (agent cost + entry budget).
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
                vol = 0.0
                if e["screen"]:
                    try:
                        vol = float(json.loads(e["screen"]).get("avg_volume", 0))
                    except (ValueError, TypeError):
                        pass
                due.append((0 if core else 1, -vol, e))
            due.sort(key=lambda t: (t[0], t[1]))
            if len(due) > max_runs:
                dropped = ", ".join(e["symbol"] for _, _, e in due[max_runs:])
                print(f"analyst: capping at {max_runs} runs — dropped: {dropped}")
                due = due[:max_runs]

            # Non-core names need gap history before the analyst can align
            # with it — one batched backtester run for any that lack rows.
            need_bt = [e["symbol"] for _, _, e in due
                       if e["symbol"] not in cfg.universe
                       and store.backtest_summary(e["symbol"])["events"] == 0]
            if need_bt:
                syms = ", ".join(sorted(set(need_bt)))
                print(f"backtester: backfilling new names first — {syms}")
                if not dry_run:
                    print(f"backtester exit {_run_with_evidence(store, 'backtester', symbol=syms, model=model)}")

            ran = 0
            for _, _, e in due:
                if _skip_reanalysis(store, e, cfg.policy_version):
                    print(f"analyst: {e['symbol']} {e['report_date']} already decided — skip")
                    continue
                ran += 1
                print(f"analyst: {e['symbol']} {e['report_date']} ({e['timing']}) is due")
                if not dry_run:
                    rc = _run_with_evidence(store, "analyst", symbol=e["symbol"], model=model)
                    print(f"analyst({e['symbol']}) exit {rc}")
            if ran == 0:
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
                    print(f"executor exit {_run_with_evidence(store, 'executor', symbol=job, model=model)}")
            elif pending:
                print(f"executor: {len(pending)} pending buy(s) but {arm_why} — nothing executes")
            else:
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
