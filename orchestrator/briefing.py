"""Operator briefing - the human-alignment mechanism.

Deterministic (no LLM, no cost, can't hallucinate): built straight from the
store. The morning tick writes reports/BRIEFING.md and commits it, so the
operator can read system state, plans, and trade history anywhere (including
GitHub mobile). On demand: `python -m orchestrator.main report`.

The reverse channel is DIRECTIVES.md at the repo root: the operator writes
plain-English standing instructions there and every agent sees them in the
context pack on its next run.
"""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta, timezone

from engine.arming import arm_status
from engine.config import Config
from engine.store import Store

from .daily import analyst_due, edge_rank, next_trading_day

ML_TRAINING_THRESHOLD = 50  # labeled trade outcomes before a sidecar model is worth fitting


def _fmt_money(v: float) -> str:
    return f"${v:,.2f}"


def build_briefing(cfg: Config, store: Store) -> str:
    today = date.today()
    arm, arm_why = arm_status()
    md: list[str] = [
        f"# Operator Briefing - {today.isoformat()}",
        f"_Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')} "
        "(deterministic; built from the store, not model output)._",
    ]
    # Alerts first — the operator reads this on a phone; anything that needs a
    # human must be the first thing on screen, not buried in System health.
    reconcile = store.meta_get("exit_reconcile_needed", "")
    tick_err = store.meta_get("last_tick_error", "")
    if reconcile:
        md += ["", f"> 🚨 **ACTION NEEDED - live exits unreconciled: {reconcile}.** "
                   "A real position may be unsold or its fill unrecorded; check "
                   "the broker and the morning log."]
    if tick_err:
        md += ["", f"> ⚠️ **Last tick error**: {tick_err}"]
    md += [
        "",
        "## Account & risk",
    ]
    if arm:
        days_left = (date.fromisoformat(arm.expires) - today).days
        md.append(f"- **LIVE - armed until {arm.expires}** ({days_left}d left); live caps "
                  f"{_fmt_money(arm.per_position_cap_usd)}/position, "
                  f"{_fmt_money(arm.daily_cap_usd)}/day")
        if days_left <= 7:
            md.append(f"- ⚠️ **Arm expires in {days_left} day(s)** - re-arm deliberately: "
                      "`python -m orchestrator.main arm-live --confirm ...`")
    else:
        md.append(f"- **PAPER** ({arm_why}) - no real orders")
    snap = store.meta_get("account_snapshot", "")
    if snap:
        import json
        s = json.loads(snap)
        cash = float(s.get("cash_usd", 0))
        bp = float(s.get("buying_power_usd", 0))
        md.append(f"- Account (executor-reported {s.get('reported_at', '?')}): "
                  f"equity {_fmt_money(float(s.get('equity_usd', 0)))}, "
                  f"cash {_fmt_money(cash)}, buying power {_fmt_money(bp)}")
        if cash - bp > 0.01:
            md.append(f"- ⏳ Unsettled proceeds: {_fmt_money(cash - bp)} - "
                      "tradeable next trading day (T+1); capital cycles every "
                      "other day on this cash account")
    else:
        md.append("- Account: no snapshot yet (first executor run reports it)")
    acct = store.meta_get("account_number", "")
    if acct:
        acct_type = store.meta_get("account_type", "cash")
        shorting = ("shorting ENABLED" if store.meta_get("short_capable", "") == "1"
                    else "shorting not enabled")
        rule = ("PDT-guarded" if acct_type == "margin"
                else "T+1/GFV-guarded, no PDT")
        md.append(f"- Designated account: ••••{acct[-4:]} ('Agentic', {acct_type} - "
                  f"{rule}; {shorting})")
    md.append(f"- Live closes today: {store.live_closes_today()} | "
              f"same-day round trips this week: {store.day_trades_last_5d()}")
    md.append(f"- Today's new exposure: {_fmt_money(store.today_new_exposure())}")

    md += ["", "## Open positions"]
    open_pos = store.open_positions()
    if open_pos:
        for p in open_pos:
            md.append(f"- #{p['id']} {p['symbol']} {p['action']} "
                      f"{_fmt_money(p['size_usd'])} @ {p['entry_price']} "
                      f"[{p['status']}] since {p['created_at']}")
    else:
        md.append("- none - holding cash")

    md += ["", "## Trade history & dataset"]
    history = store.trade_history()
    closed = [h for h in history if h["status"] in ("closed_paper", "closed_live")
              and h["pnl_usd"] is not None]
    live_closed = [h for h in closed if h["status"] == "closed_live"]
    if closed:
        total = sum(h["pnl_usd"] for h in closed)
        wins = sum(1 for h in closed if h["pnl_usd"] > 0)
        md.append(f"- Closed trades: {len(closed)} ({len(live_closed)} live) | "
                  f"wins {wins}/{len(closed)} | total P&L {_fmt_money(total)}")
    else:
        md.append("- Closed trades: none yet")
    perf = store.performance_summary()
    md.append(f"- Decisions by action: {perf['decisions_by_action'] or '{}'} | "
              f"labeled passes: {perf['labeled_passes']} | "
              f"rejected: {perf['rejected']} | exec failures: {perf['exec_failed']}")
    for h in history[:12]:
        outcome = ""
        if h["pnl_usd"] is not None:
            move = f"{h['outcome_move_pct']:+.2f}%" if h["outcome_move_pct"] is not None else "n/a"
            outcome = f" → exit {h['exit_price']} ({move}, P&L {_fmt_money(h['pnl_usd'])})"
        md.append(f"  - #{h['id']} {h['symbol']} {h['action']} "
                  f"[{h['status']}] conv {h['conviction']} policy {h['policy_version']}"
                  f"{outcome}")

    # Plan: show the plan the SYSTEM will actually execute, not the raw
    # calendar. Post-market-wide-expansion the old per-event list ran 250+
    # lines of undifferentiated names (unreadable on mobile, where this is
    # read); the tick itself only analyzes the top edge-ranked candidates per
    # session. So: next session in full, edge-ranked with the projected
    # analyst slots flagged, and everything further out as per-date counts.
    md += ["", "## Plan - next 14 days (and why)"]
    events = store.upcoming_events(days=14)
    if not events:
        md.append("- No universe earnings in the next 14 days. Ticks keep running: "
                  "scout refreshes the calendar daily; nothing enters without an event.")
    max_runs = int(os.environ.get("EARNINGS_MAX_ANALYST_RUNS", "6"))
    planned = 0
    next_session: list[tuple] = []
    later: dict[str, dict] = {}
    detail_cutoff = today if analyst_due(today.isoformat(), "amc", today) else None
    detail_cutoff = detail_cutoff or next_trading_day(today)
    for e in events:
        if e["symbol"] in cfg.macro_watch:
            continue  # context only; the gate blocks trading them regardless
        d = date.fromisoformat(e["report_date"])
        entry_day = d if e["timing"] == "amc" else None
        if e["timing"] != "amc":
            probe = d - timedelta(days=4)
            while probe < d:
                if next_trading_day(probe) == d and probe.weekday() < 5:
                    entry_day = probe
                    break
                probe += timedelta(days=1)
        if entry_day is None or entry_day < today:
            continue
        core = e["symbol"] in cfg.universe
        eligible = core or bool(e["screened"])
        if entry_day <= detail_cutoff and not eligible:
            continue  # unscreened non-core: can't be analyzed this session
        planned += 1
        if entry_day <= detail_cutoff:
            already = store.decisions_for_event(e["id"])
            decided = bool(already and any(
                x["action"] != "pass" or x["policy_version"] == cfg.policy_version
                for x in already))
            next_session.append((entry_day, e, core, decided))
        else:
            b = later.setdefault(entry_day.isoformat(),
                                 {"n": 0, "screened": 0, "core": []})
            b["n"] += 1
            if core:
                b["core"].append(e["symbol"])
            elif e["screened"]:
                b["screened"] += 1
    if next_session:
        entry_day = min(t[0] for t in next_session)
        batch = [t for t in next_session if t[0] == entry_day]
        ranked = sorted(batch, key=lambda t: edge_rank(store, t[1], t[2]))
        md.append(f"- **Next entry session {entry_day.isoformat()} ~15:45-15:58 ET** - "
                  f"{len(batch)} eligible candidate(s); top {min(max_runs, len(batch))} "
                  "by edge rank get the analyst slots:")
        for _, e, core, decided in ranked[:max_runs]:
            d = e["report_date"]
            exit_desc = ("exit same-day ~16:50 if PDT allows, else next open"
                         if e["timing"] == "amc"
                         else f"exit post-report open {d} 09:31")
            tag = "core" if core else "screened"
            md.append(f"  - **{e['symbol']}** ({tag}) reports {d} {e['timing']}: "
                      f"{exit_desc}" + (" - already decided" if decided else ""))
        rest = ranked[max_runs:]
        if rest:
            md.append("  - below the slot line: "
                      + ", ".join(t[1]["symbol"] for t in rest))
    if later:
        md.append("- Further out (slots edge-ranked on the day):")
        for day in sorted(later):
            b = later[day]
            parts = [f"{b['n']} candidate(s)"]
            if b["core"]:
                parts.append("core: " + ", ".join(sorted(b["core"])))
            if b["screened"]:
                parts.append(f"{b['screened']} screened")
            md.append(f"  - entry {day}: " + " | ".join(parts))
    if events and planned == 0:
        md.append("- Events tracked but none enterable (timing/weekend constraints).")

    md += ["", "## System health"]
    for ph in ("morning", "afternoon", "evening"):
        last = store.meta_get(f"tick_{ph}_last", "")
        md.append(f"- {ph} tick last ran: {last or 'never'}")
    err = store.meta_get("last_tick_error", "")
    if err:
        md.append(f"- ⚠️ **Last tick error**: {err}")
    from engine import ml as _ml
    md.append(f"- ML sidecar: {_ml.brief_status(store)}")
    if arm and snap:
        try:
            import json as _json
            eq = float(_json.loads(snap).get("equity_usd", 0))
            if eq > 0 and eq >= arm.daily_cap_usd * 1.5:
                md.append(f"- 💡 Equity ({_fmt_money(eq)}) has outgrown the live caps "
                          f"({_fmt_money(arm.per_position_cap_usd)}/pos, "
                          f"{_fmt_money(arm.daily_cap_usd)}/day) - consider re-arming "
                          "with higher caps to keep stacking.")
        except (ValueError, TypeError):
            pass

    md += [
        "",
        "## Longer-term roadmap status",
        f"- Dataset: {perf['closed_trades']} closed trades + {perf['labeled_passes']} "
        f"labeled passes | backtests: {store.backtest_summary()['events']} historical events",
        f"- **ML sidecar (Phase 4)**: pipeline BUILT and self-activating - trains "
        f"automatically each morning; advisory until ~{ML_TRAINING_THRESHOLD} labeled rows",
        "- Phase 2 (deterministic indicators): BUILT - compute_indicators / "
        "compute_implied_move run server-side",
        "- Strategy is STOCKS-ONLY (operator decision): live capital goes long "
        "equity; bearish theses are paper-only dataset legs (options L2 exists "
        "on the account but is deliberately unused)",
        "- Strategist: reviews policy after every 3 new labeled outcomes (auto)",
        "",
        "## Steering",
        "- Write standing instructions in **DIRECTIVES.md** - every agent sees them "
        "in its context pack on the next run.",
        "- `python -m orchestrator.main report` regenerates this briefing anytime; "
        "the morning tick commits it daily.",
    ]
    text = "\n".join(md) + "\n"
    # Operator style rule (2026-07-07): never em dashes in human-facing
    # output; render-time so model-written lines are covered too.
    return (text.replace(" \u2014 ", " - ").replace("\u2014", " - ")
                .replace(" \u2013 ", " - ").replace("\u2013", "-"))
