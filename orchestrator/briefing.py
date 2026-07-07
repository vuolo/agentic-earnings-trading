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

from datetime import date, datetime, timedelta, timezone

from engine.arming import arm_status
from engine.config import Config
from engine.store import Store

from .daily import analyst_due, next_trading_day

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

    md += ["", "## Plan - next 14 days (and why)"]
    events = store.upcoming_events(days=14)
    if not events:
        md.append("- No universe earnings in the next 14 days. Ticks keep running: "
                  "scout refreshes the calendar daily; nothing enters without an event.")
    planned = 0
    for e in events:
        d = date.fromisoformat(e["report_date"])
        entry_day = d if e["timing"] == "amc" else None
        if e["timing"] != "amc":
            probe = d - timedelta(days=4)
            while probe < d:
                if next_trading_day(probe) == d and probe.weekday() < 5:
                    entry_day = probe
                    break
                probe += timedelta(days=1)
        if entry_day is None:
            continue
        planned += 1
        exit_desc = ("same-day after-hours ~16:50 if PDT allows, else next open"
                     if e["timing"] == "amc" else f"post-report open {d.isoformat()} 09:31")
        already = store.decisions_for_event(e["id"])
        state = " (already decided)" if already and any(
            x["action"] != "pass" or x["policy_version"] == cfg.policy_version
            for x in already) else ""
        md.append(f"- **{e['symbol']}** reports {e['report_date']} {e['timing']}: "
                  f"analyst+entry {entry_day.isoformat()} ~15:40-15:58 ET, "
                  f"exit {exit_desc}{state} - window per backtest gap stats "
                  "(see `get_backtest_summary`)")
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
