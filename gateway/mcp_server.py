"""Earnings gateway MCP server — the agents' only write path.

Agents get market data from the Robinhood MCP server (read-only allowlist) and
submit everything through here. Two jobs:

- **Context injection**: every tool response ends with a fresh CONTEXT PACK
  (mode, risk budget, open positions, upcoming events, recent decisions).
- **Risk enforcement**: submit_decision runs engine.risk.RiskGate server-side.
  A rejection is recorded and final for that submission — it cannot be
  prompted away.

Run as:  python -m gateway.mcp_server   (spawned by orchestrator/launcher.py,
configured via EARNINGS_* env vars; see engine/config.py)
"""

from __future__ import annotations

import json
from datetime import date

from mcp.server.fastmcp import FastMCP

from engine.config import Config
from engine.context import build_context_pack
from engine.risk import TRADE_ACTIONS, VALID_ACTIONS, DecisionRequest, RiskGate
from engine.store import Store

mcp = FastMCP("earnings")

CFG = Config.from_env()
STORE = Store(CFG.db_path)
GATE = RiskGate(CFG, STORE)


def _pack() -> str:
    return build_context_pack(CFG, STORE)


@mcp.tool()
def get_context_pack() -> str:
    """Current trading context: mode, risk budget, open paper positions,
    upcoming earnings events, recent decisions. Call this FIRST, every run."""
    return _pack()


@mcp.tool()
def record_earnings_event(
    symbol: str, report_date: str, timing: str = "unknown", details_json: str = ""
) -> str:
    """Record or refresh an upcoming earnings event.

    report_date: YYYY-MM-DD. timing: 'bmo' (before open), 'amc' (after close),
    or 'unknown'. details_json: the raw calendar payload you saw (JSON string).
    """
    symbol = symbol.strip().upper()
    try:
        date.fromisoformat(report_date)
    except ValueError:
        return f"ERROR: report_date {report_date!r} is not YYYY-MM-DD.\n\n{_pack()}"
    timing = timing.strip().lower()
    coerced = "" if timing in ("bmo", "amc", "unknown") else f" (timing {timing!r} coerced to 'unknown')"
    event_id = STORE.upsert_event(
        symbol, report_date, timing, raw=details_json or None
    )
    return f"Recorded event #{event_id}: {symbol} {report_date}{coerced}.\n\n{_pack()}"


@mcp.tool()
def submit_decision(
    symbol: str,
    report_date: str,
    action: str,
    thesis: str,
    features_json: str,
    size_usd: float = 0.0,
    entry_price: float = 0.0,
    conviction: float = 0.5,
) -> str:
    """Submit your decision for an earnings event. The server-side risk gate
    has the final word; approved trades become paper positions at entry_price.

    action: 'long_equity' | 'bearish_option' | 'pass'. Submit 'pass' explicitly
    when you decide not to trade — passes are dataset rows too.
    features_json: the FULL feature snapshot your decision is based on (JSON:
    implied move, historical reaction stats, indicators, sentiment, etc.).
    entry_price: current underlying reference price (required for trades).
    """
    symbol = symbol.strip().upper()
    if action not in VALID_ACTIONS:
        return f"ERROR: action must be one of {VALID_ACTIONS}.\n\n{_pack()}"

    try:
        json.loads(features_json)
        features = features_json
    except (json.JSONDecodeError, TypeError):
        features = json.dumps({"unparsed": str(features_json)})

    event_id = None
    try:
        date.fromisoformat(report_date)
        event_id = STORE.upsert_event(symbol, report_date)
    except ValueError:
        pass  # decision still recorded, just unlinked

    if action == "pass":
        did = STORE.insert_decision(
            symbol=symbol, action="pass", policy_version=CFG.policy_version,
            risk_verdict="n/a (pass)", status="pass", conviction=conviction,
            thesis=thesis, features=features, event_id=event_id,
        )
        return f"Recorded pass as decision #{did}.\n\n{_pack()}"

    if entry_price <= 0:
        return (
            "ERROR: entry_price (current underlying price) is required for a "
            f"trade decision — fetch a quote and resubmit.\n\n{_pack()}"
        )

    verdict = GATE.evaluate(
        DecisionRequest(symbol=symbol, action=action, size_usd=size_usd, conviction=conviction)
    )
    status = "open_paper" if verdict.approved else "rejected"
    did = STORE.insert_decision(
        symbol=symbol, action=action, policy_version=CFG.policy_version,
        risk_verdict=str(verdict), status=status, size_usd=size_usd,
        entry_price=entry_price, conviction=conviction, thesis=thesis,
        features=features, event_id=event_id,
    )
    if verdict.approved:
        msg = (
            f"Decision #{did} APPROVED — paper position opened: {symbol} {action} "
            f"${size_usd:,.2f} @ {entry_price}."
        )
    else:
        msg = (
            f"Decision #{did} REJECTED by risk gate ({verdict}). This is final "
            "for this submission — do not resubmit a resized variant unless the "
            "rejection reason is a fixable input error."
        )
    return f"{msg}\n\n{_pack()}"


@mcp.tool()
def close_paper_position(symbol: str, exit_price: float, notes: str = "") -> str:
    """Close the open paper position for symbol at exit_price (underlying
    reference price) and record the labeled outcome."""
    result = STORE.close_position(symbol, exit_price, notes)
    if result is None:
        return (
            f"ERROR: no open paper position for {symbol.strip().upper()} "
            f"(or invalid price).\n\n{_pack()}"
        )
    return (
        f"Closed decision #{result['decision_id']}: {result['symbol']} "
        f"{result['action']} {result['entry_price']} → {result['exit_price']} "
        f"({result['move_pct']:+.2f}%), P&L ${result['pnl_usd']:+,.2f}.\n\n{_pack()}"
    )


if __name__ == "__main__":
    mcp.run()
