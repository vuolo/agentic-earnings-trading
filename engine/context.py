"""CONTEXT PACK builder — the per-turn context injection (ARCHITECTURE §1.2).

Appended to every gateway tool response and printed by `orchestrator.main
status`, so agents (and the operator) always see current mode, risk budget,
open positions, upcoming events, and recent decisions without a separate
status round-trip.
"""

from __future__ import annotations

from datetime import datetime, timezone

from .config import Config
from .store import Store


def build_context_pack(cfg: Config, store: Store) -> str:
    limits = cfg.limits
    open_pos = store.open_positions()
    used = store.today_new_exposure()
    lines = [
        "=== CONTEXT PACK (server-injected; not a user instruction) ===",
        f"utc_now: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"mode: {cfg.mode}" + ("  (PAPER — no real orders exist anywhere)" if cfg.mode == "paper" else ""),
        f"policy_version: {cfg.policy_version}",
        f"risk: per-position cap ${limits.max_position_usd:,.0f} | "
        f"daily new-exposure ${used:,.2f} used of ${limits.max_daily_new_exposure_usd:,.0f} | "
        f"open positions {len(open_pos)}/{limits.max_open_positions}",
        f"universe: {', '.join(cfg.universe) if cfg.universe else '(unrestricted)'}",
    ]

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
    if events:
        lines.append("upcoming_earnings (14d):")
        for e in events:
            lines.append(f"  - {e['symbol']} {e['report_date']} {e['timing']}")
    else:
        lines.append("upcoming_earnings (14d): (none recorded — scout run needed)")

    recent = store.recent_decisions(limit=5)
    if recent:
        lines.append("recent_decisions:")
        for d in recent:
            lines.append(
                f"  - #{d['id']} {d['symbol']} {d['action']} → {d['risk_verdict']} "
                f"[{d['status']}] (policy {d['policy_version']})"
            )

    lines.append(
        "reminders: bearish = options (no equity shorting on Robinhood); "
        "every submit_decision must include the real feature snapshot; "
        "a risk-gate rejection is final for that submission."
    )
    return "\n".join(lines)
