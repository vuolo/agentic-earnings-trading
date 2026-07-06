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
import re
import subprocess
from datetime import date

from mcp.server.fastmcp import FastMCP

from engine.config import REPO_ROOT, Config
from engine.context import build_context_pack
from engine.risk import TRADE_ACTIONS, VALID_ACTIONS, DecisionRequest, RiskGate
from engine.store import Store

mcp = FastMCP("earnings")

POLICY_PATH = REPO_ROOT / "prompts" / "POLICY.md"
_POLICY_REQUIRED_SECTIONS = (
    "## Universe", "## Required feature snapshot", "## Entry rules",
    "## Sizing", "## Exit",
)

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
            entry_price=entry_price if entry_price > 0 else None,
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
    # Live routing: armed long_equity — and short_equity once the operator has
    # verified+enabled shorting (the gate rejects it otherwise) — go to the
    # executor. bearish_option stays a paper dataset leg.
    if not verdict.approved:
        status = "rejected"
    elif CFG.mode == "live" and action in ("long_equity", "short_equity"):
        status = "pending_live"
    else:
        status = "open_paper"
    did = STORE.insert_decision(
        symbol=symbol, action=action, policy_version=CFG.policy_version,
        risk_verdict=str(verdict), status=status, size_usd=size_usd,
        entry_price=entry_price, conviction=conviction, thesis=thesis,
        features=features, event_id=event_id,
    )
    if status == "pending_live":
        msg = (
            f"Decision #{did} APPROVED — queued for LIVE execution: {symbol} "
            f"{action} ${size_usd:,.2f} (ref {entry_price}). The executor "
            "will place the real order."
        )
    elif verdict.approved:
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


@mcp.tool()
def label_pass_outcome(decision_id: int, exit_price: float, notes: str = "") -> str:
    """Record the counterfactual outcome for a PASS decision after its event:
    what the underlying did (exit_price = current post-event price). P&L is 0
    (no capital was used); the move teaches the dataset what the pass avoided
    or missed."""
    result = STORE.label_pass(decision_id, exit_price, notes)
    if result is None:
        return (
            f"ERROR: decision #{decision_id} is not an unlabeled pass "
            f"(or invalid price).\n\n{_pack()}"
        )
    move = "n/a (no reference price recorded)" if result["move_pct"] is None \
        else f"{result['move_pct']:+.2f}%"
    return (
        f"Labeled pass #{decision_id} ({result['symbol']}): counterfactual "
        f"move {move}.\n\n{_pack()}"
    )


@mcp.tool()
def get_pending_executions() -> str:
    """List decisions queued for LIVE execution (status pending_live). The
    executor may execute ONLY these, exactly as specified."""
    rows = STORE.pending_executions()
    if not rows:
        return f"No pending live executions.\n\n{_pack()}"
    lines = [
        f"#{r['id']} {r['symbol']} {r['action']} ${r['size_usd']:,.2f} "
        f"(ref price {r['entry_price']})"
        for r in rows
    ]
    return "Pending live executions:\n" + "\n".join(lines) + f"\n\n{_pack()}"


@mcp.tool()
def report_execution(
    decision_id: int, filled: bool, fill_price: float = 0.0, detail: str = ""
) -> str:
    """Report the result of executing a pending_live decision. filled=True
    requires the real fill_price; filled=False marks exec_failed with detail
    (e.g. 'order unfilled, cancelled' or 'price moved beyond guard')."""
    row = STORE.mark_execution(
        decision_id, filled=filled,
        fill_price=fill_price if fill_price > 0 else None, detail=detail,
    )
    if row is None:
        return (
            f"ERROR: decision #{decision_id} is not pending_live (or fill_price "
            f"missing).\n\n{_pack()}"
        )
    return f"Decision #{decision_id} → {row['status']}.\n\n{_pack()}"


@mcp.tool()
def report_live_close(decision_id: int, exit_price: float, notes: str = "") -> str:
    """Report the real exit fill for an open_live position — records the
    labeled outcome and closes it."""
    result = STORE.close_live(decision_id, exit_price, notes)
    if result is None:
        return f"ERROR: decision #{decision_id} is not open_live (or invalid price).\n\n{_pack()}"
    return (
        f"Closed live #{decision_id}: {result['symbol']} {result['entry_price']} "
        f"→ {result['exit_price']} ({result['move_pct']:+.2f}%), "
        f"P&L ${result['pnl_usd']:+,.2f}.\n\n{_pack()}"
    )


@mcp.tool()
def compute_indicators(bars_json: str, benchmark_bars_json: str = "") -> str:
    """Deterministic indicator computation (the server does the math, you
    don't). Pass raw daily bars from get_equity_historicals (any JSON shape);
    optionally pass benchmark bars (e.g. an index or SMH proxy) for relative
    strength. Returns: rsi14, atr14_pct, realized_vol20_pct, volume_z20,
    sma20/50 + trend, pct_from_high/low, rel_strength20_pct. Embed the result
    VERBATIM in features_json under "computed"."""
    from engine import indicators
    try:
        bars = indicators.parse_bars(bars_json)
        bench = indicators.parse_bars(benchmark_bars_json) if benchmark_bars_json.strip() else None
    except (ValueError, json.JSONDecodeError) as e:
        return f"ERROR: {e}"
    return json.dumps(indicators.compute(bars, bench), indent=1)


@mcp.tool()
def compute_implied_move(underlying_price: float, call_mid: float, put_mid: float) -> str:
    """Deterministic implied-move computation from ATM straddle mids (nearest
    expiry after the report). Embed the result verbatim in features_json
    under "implied_move"."""
    from engine import indicators
    try:
        return json.dumps(indicators.implied_move(underlying_price, call_mid, put_mid))
    except ValueError as e:
        return f"ERROR: {e}"


@mcp.tool()
def get_ml_prediction(features_json: str, conviction: float = -1.0) -> str:
    """The ML sidecar's read on your feature snapshot: P(post-event move up).
    ADVISORY while the dataset is small — weigh it, don't obey it; record its
    output in your features_json under "ml_advisory". Reports honestly when
    untrained."""
    from engine import ml
    try:
        feats = json.loads(features_json)
    except json.JSONDecodeError:
        return "ERROR: features_json is not valid JSON"
    conv = conviction if 0.0 <= conviction <= 1.0 else None
    return json.dumps(ml.predict(feats, conv), indent=1)


@mcp.tool()
def report_account_snapshot(
    equity_usd: float, cash_usd: float, buying_power_usd: float,
    account_type: str = "",
) -> str:
    """Report the REAL account state (from get_accounts/get_portfolio) so every
    agent sees it in the context pack. The executor/monitor call this at the
    start of every run — balance awareness is mandatory before any order.
    account_type: 'cash' or 'margin' as reported by get_accounts for the
    designated account (drives the settlement/PDT logic)."""
    from datetime import datetime, timezone
    STORE.meta_set("account_snapshot", json.dumps({
        "equity_usd": equity_usd,
        "cash_usd": cash_usd,
        "buying_power_usd": buying_power_usd,
        "reported_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }))
    if account_type.strip().lower() in ("cash", "margin"):
        STORE.meta_set("account_type", account_type.strip().lower())
    return f"Account snapshot recorded.\n\n{_pack()}"


@mcp.tool()
def record_backtest_result(
    symbol: str, report_date: str, timing: str = "unknown",
    pre_close: float = 0.0, post_open: float = 0.0, post_close: float = 0.0,
    details_json: str = "",
) -> str:
    """Record one historical earnings event for backtesting: the last close
    BEFORE the report (pre_close), and the first open and close AFTER it.
    These drive the gap/drift stats that align entries and exits."""
    try:
        bid = STORE.upsert_backtest(
            symbol, report_date, timing,
            pre_close=pre_close or None, post_open=post_open or None,
            post_close=post_close or None, raw=details_json or None,
        )
    except ValueError:
        return f"ERROR: report_date {report_date!r} is not YYYY-MM-DD.\n\n{_pack()}"
    return f"Recorded backtest event #{bid}: {symbol.upper()} {report_date}."


@mcp.tool()
def get_backtest_summary(symbol: str = "") -> str:
    """Backtest stats for one symbol (or all): gap (T-1 close → post-report
    open — what our entry window captures) and drift (post-report open →
    close). Consult this before deciding direction, sizing, and exit timing."""
    return json.dumps(STORE.backtest_summary(symbol or None), indent=1)


@mcp.tool()
def get_performance_summary() -> str:
    """Aggregate performance of the decision dataset: closed trades, win count,
    total P&L, labeled pass counterfactuals, rejections, execution failures."""
    return json.dumps(STORE.performance_summary(), indent=1) + f"\n\n{_pack()}"


@mcp.tool()
def get_labeled_decisions(limit: int = 20) -> str:
    """The most recent labeled decisions with their full feature snapshots,
    theses, and outcomes — the raw material for policy review."""
    rows = STORE.labeled_decisions(limit)
    for r in rows:
        try:
            r["features"] = json.loads(r["features"]) if r["features"] else None
        except json.JSONDecodeError:
            pass
    return json.dumps(rows, indent=1, default=str)


@mcp.tool()
def propose_policy_update(new_policy_markdown: str, rationale: str) -> str:
    """Replace prompts/POLICY.md with a revised version (the strategist's
    self-improvement path). Requirements enforced here: the Version line must
    be bumped, all required sections must be present, and a substantive
    rationale must be given. The change is git-committed for the audit trail.

    This updates trading POLICY only. Engine risk caps and the live arm switch
    are code/operator territory and are not affected by policy text.
    """
    if len(rationale.strip()) < 40:
        return f"ERROR: rationale too thin — explain what the data showed.\n\n{_pack()}"
    old = POLICY_PATH.read_text()
    old_v = re.search(r"(?m)^Version:\s*(\S+)", old)
    new_v = re.search(r"(?m)^Version:\s*(\S+)", new_policy_markdown)
    if not new_v:
        return f"ERROR: new policy has no 'Version:' line.\n\n{_pack()}"
    if old_v and new_v.group(1) == old_v.group(1):
        return f"ERROR: version not bumped (still {new_v.group(1)}).\n\n{_pack()}"
    missing = [s for s in _POLICY_REQUIRED_SECTIONS if s not in new_policy_markdown]
    if missing:
        return f"ERROR: new policy is missing sections: {', '.join(missing)}.\n\n{_pack()}"
    if len(new_policy_markdown) < 800:
        return f"ERROR: new policy suspiciously short — keep it complete.\n\n{_pack()}"

    POLICY_PATH.write_text(new_policy_markdown)
    msg = (
        f"policy: v{old_v.group(1) if old_v else '?'} -> v{new_v.group(1)} (strategist)\n\n"
        f"{rationale}\n\n"
        "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
    )
    r = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "commit", "-m", msg, "--", "prompts/POLICY.md"],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        return (
            f"Policy file updated to v{new_v.group(1)}, but git commit failed:\n"
            f"{r.stderr.strip()}\n\n{_pack()}"
        )
    STORE.meta_set("strategist_outcome_count", str(STORE.outcome_count()))
    return (
        f"Policy updated and committed: v{new_v.group(1)}. It takes effect on "
        f"the next agent launch.\n\n{_pack()}"
    )


if __name__ == "__main__":
    mcp.run()
