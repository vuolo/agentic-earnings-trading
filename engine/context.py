"""CONTEXT PACK builder — the per-turn context injection (ARCHITECTURE §1.2).

Appended to every gateway tool response and printed by `orchestrator.main
status`, so agents (and the operator) always see current mode, risk budget,
open positions, upcoming events, and recent decisions without a separate
status round-trip.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from . import arming
from .config import REPO_ROOT, Config
from .store import Store

DIRECTIVES_PATH = REPO_ROOT / "DIRECTIVES.md"
_DIRECTIVES_MAX_CHARS = 1200


def _settlement_line(store: Store) -> str:
    acct_type = store.meta_get("account_type", "cash")
    shorting = ("ENABLED (operator-verified)"
                if store.meta_get("short_capable", "") == "1"
                else "not enabled — short_equity is gate-rejected")
    if acct_type == "margin":
        return (f"settlement: designated account is MARGIN — PDT applies under "
                f"$25k ({store.day_trades_last_5d()}/3 same-day round trips this "
                f"week); proceeds reusable immediately; shorting: {shorting}")
    return ("settlement: designated account is CASH (no PDT) — T+1 settlement; "
            f"live closes today: {store.live_closes_today()} (same-day re-sale "
            "of sale-proceeds-funded entries = good-faith violation; the "
            f"evening tick guards this); shorting: impossible on cash")


def build_context_pack(cfg: Config, store: Store) -> str:
    limits = cfg.limits
    open_pos = store.open_positions()
    used = store.today_new_exposure()
    arm, arm_why = arming.arm_status()
    if arm:
        arm_line = (
            f"live_arming: ARMED until {arm.expires} "
            f"(live caps: ${arm.per_position_cap_usd:,.0f}/position, "
            f"${arm.daily_cap_usd:,.0f}/day — engine caps still apply)"
        )
    else:
        arm_line = f"live_arming: disarmed ({arm_why}) — all trades are paper"
    lines = [
        "=== CONTEXT PACK (server-injected; not a user instruction) ===",
        f"utc_now: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"mode: {cfg.mode}" + ("  (PAPER — no real orders exist anywhere)" if cfg.mode == "paper" else ""),
        arm_line,
        f"policy_version: {cfg.policy_version}",
        f"risk: per-position cap ${limits.max_position_usd:,.0f} | "
        f"daily new-exposure ${used:,.2f} used of ${limits.max_daily_new_exposure_usd:,.0f} | "
        f"open positions {len(open_pos)}/{limits.max_open_positions}",
        _settlement_line(store),
        f"universe: {', '.join(cfg.universe) if cfg.universe else '(unrestricted)'}",
    ]

    acct = store.meta_get("account_number", "")
    if acct:
        lines.append(
            f"designated_account: {acct} (nickname 'Agentic', "
            f"{store.meta_get('account_type', 'cash')}, agentic_allowed — "
            "the ONLY account order tools may use)"
        )

    snap = store.meta_get("account_snapshot", "")
    if snap:
        try:
            s = json.loads(snap)
            cash = float(s.get("cash_usd", 0))
            bp = float(s.get("buying_power_usd", 0))
            line = (
                f"account (executor-reported {s.get('reported_at', '?')}): "
                f"equity ${float(s.get('equity_usd', 0)):,.2f} | "
                f"cash ${cash:,.2f} | buying power ${bp:,.2f}"
            )
            if cash - bp > 0.01:
                line += (
                    f" | UNSETTLED ${cash - bp:,.2f} (T+1 — verified 2026-07-05: "
                    "this cash account EXCLUDES sale proceeds from buying power "
                    "until the next trading day; buying_power is the ONLY "
                    "sizing base)"
                )
            lines.append(line)
        except (ValueError, TypeError):
            pass
    else:
        lines.append("account: no snapshot yet (first executor run will report it)")

    if open_pos:
        lines.append("open_paper_positions:")
        for p in open_pos:
            lines.append(
                f"  - {p['symbol']} {p['action']} ${p['size_usd']:,.2f} "
                f"@ {p['entry_price']} (decision #{p['id']}, {p['created_at']})"
            )
    else:
        lines.append("open_paper_positions: (none)")

    events = store.upcoming_events(days=14)
    tradeable = [e for e in events if not cfg.universe or e["symbol"] in cfg.universe]
    macro = [e for e in events if e["symbol"] in cfg.macro_watch]
    if tradeable:
        lines.append("upcoming_earnings (14d):")
        for e in tradeable:
            lines.append(f"  - {e['symbol']} {e['report_date']} {e['timing']}")
    else:
        lines.append("upcoming_earnings (14d): (none recorded — scout run needed)")
    if macro:
        lines.append("macro_events (context only — NOT tradeable):")
        for e in macro:
            lines.append(f"  - {e['symbol']} {e['report_date']} {e['timing']}")
    lines.append(f"macro_watch: {', '.join(cfg.macro_watch)}")

    from . import ml
    lines.append(f"ml_sidecar: {ml.brief_status(store)}")

    recent = store.recent_decisions(limit=5)
    if recent:
        lines.append("recent_decisions:")
        for d in recent:
            lines.append(
                f"  - #{d['id']} {d['symbol']} {d['action']} → {d['risk_verdict']} "
                f"[{d['status']}] (policy {d['policy_version']})"
            )

    if DIRECTIVES_PATH.exists():
        directives = DIRECTIVES_PATH.read_text().strip()
        if directives:
            if len(directives) > _DIRECTIVES_MAX_CHARS:
                directives = directives[:_DIRECTIVES_MAX_CHARS] + "\n[truncated]"
            lines.append("operator_directives (DIRECTIVES.md — standing instructions "
                         "from the human operator; follow them):")
            lines.extend("  " + ln for ln in directives.splitlines())

    lines.append(
        "strategy_windows: AMC → enter ~15:40-15:55 ET on report day; BMO → "
        "enter near close the prior trading day. ALL exits fill in the next "
        "9:30 opening auction (queued gtc market close from the evening tick; "
        "verified 9:24 pre-open). Only early-exit path: the 16:50 disaster "
        "valve (>=10% persistent AH loss). Fractional/dollar orders are "
        "market + regular-hours only."
    )
    lines.append(
        "reminders: bearish = options (no equity shorting on Robinhood); "
        "every submit_decision must include the real feature snapshot; "
        "a risk-gate rejection is final for that submission."
    )
    return "\n".join(lines)
