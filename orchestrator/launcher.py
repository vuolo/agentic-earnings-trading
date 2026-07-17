"""Launcher: run a role agent via `claude -p` (headless Claude Code).

Wires one agent run together, following the pattern proven in the
stake-synthetics launcher:

1. Read the role's mission prompt + POLICY.md (parsing its Version: line).
2. Write a temp MCP config: the remote Robinhood trading server (read-only
   tools only, enforced by the allowlist) + our local earnings gateway
   (spawned with EARNINGS_* env so config flows server-side).
3. Shell `claude -p` with the mission system prompt, strict MCP config, and
   the role's exact tool allowlist. Order-placement tools are never listed.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import re
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PROMPTS = REPO_ROOT / "prompts"
ROBINHOOD_URL = "https://agent.robinhood.com/mcp/trading"
DEFAULT_MODEL = "claude-fable-5"
# Fallback when the primary is unavailable/overloaded OR when the primary's
# per-account usage limit is exhausted. Two DIFFERENT failure classes: the CLI's
# own --fallback-model flag covers only server overload/unavailability; a usage
# limit ("You've reached your Fable 5 limit") is NOT caught by that flag and
# exits 1 with the message on stdout, so run_role detects it and re-runs on the
# fallback itself. See _USAGE_LIMIT_RE and the model-chain loop below.
FALLBACK_MODEL = "claude-opus-4-8"

# Signature of a per-account usage/quota exhaustion on stdout (exit 1). Distinct
# from server overload (which --fallback-model handles automatically mid-stream).
_USAGE_LIMIT_RE = re.compile(r"reached your .*\blimit\b|/usage-credits", re.I)

# Read-only market-data tools an analyst may use. place_*_order / cancel_* are
# deliberately absent and must stay absent in v1 (CLAUDE.md rule 1).
ANALYST_RB_TOOLS = (
    "get_equity_quotes", "get_equity_historicals", "get_equity_fundamentals",
    "get_earnings_calendar", "get_earnings_results", "get_equity_tradability",
    "get_option_chains", "get_option_instruments", "get_option_quotes",
    "get_index_quotes", "search",
)


@dataclass(frozen=True)
class Role:
    prompt_file: str
    rb_tools: tuple[str, ...]
    gw_tools: tuple[str, ...]
    kickoff: str
    builtin_tools: tuple[str, ...] = ()   # Claude Code builtins, e.g. WebSearch
    model: str | None = None              # role default; explicit --model wins
    include_playbook: bool = False        # append prompts/PLAYBOOK.md to the mission


ROLES: dict[str, Role] = {
    "scout": Role(
        prompt_file="scout.md",
        rb_tools=("get_earnings_calendar", "search", "get_equity_quotes",
                  "get_equity_fundamentals", "get_equity_tradability"),
        gw_tools=("get_context_pack", "record_earnings_event"),
        kickoff=(
            "Sync the upcoming earnings calendar per your instructions. "
            "Start by calling get_context_pack."
        ),
    ),
    "analyst": Role(
        prompt_file="analyst.md",
        rb_tools=ANALYST_RB_TOOLS,
        gw_tools=(
            "get_context_pack", "submit_decision", "get_backtest_summary",
            "compute_indicators", "compute_implied_move", "get_ml_prediction",
            "compute_position_size",
        ),
        builtin_tools=("WebSearch",),  # news/sentiment
        include_playbook=True,
        kickoff=(
            "Analyze the upcoming earnings event for {symbol} and submit a "
            "decision per your instructions. Start by calling get_context_pack."
        ),
    ),
    "labeler": Role(
        prompt_file="labeler.md",
        rb_tools=("get_equity_quotes", "get_equity_historicals"),
        gw_tools=(
            "get_context_pack", "close_paper_position", "label_pass_outcome",
            "record_backtest_result",
        ),
        kickoff=(
            "Work exactly these labeling jobs, then stop — {symbol}. "
            "Start by calling get_context_pack."
        ),
    ),
    # Cheap daily account/position reconciliation — no order tools.
    "monitor": Role(
        prompt_file="monitor.md",
        rb_tools=("get_accounts", "get_portfolio", "get_equity_positions"),
        gw_tools=("get_context_pack", "report_account_snapshot"),
        model="claude-sonnet-5",
        kickoff=(
            "Report the current account snapshot and reconcile broker "
            "positions against the context pack per your instructions."
        ),
    ),
    # The ONLY role that may carry order tools, and the tick launches it only
    # while the operator's arm switch is active (CLAUDE.md rule 1).
    "executor": Role(
        prompt_file="executor.md",
        rb_tools=(
            "get_accounts", "get_portfolio", "get_equity_tradability",
            "get_equity_quotes", "get_equity_positions", "get_equity_orders",
            "review_equity_order", "place_equity_order", "cancel_equity_order",
        ),
        gw_tools=(
            "get_context_pack", "get_pending_executions",
            "report_execution", "report_live_close", "report_account_snapshot",
        ),
        kickoff=(
            "Execute exactly these jobs, then stop — {symbol}. "
            "Start by calling get_context_pack, then get_pending_executions."
        ),
    ),
    "mlbackfill": Role(
        prompt_file="ml-backfill.md",
        rb_tools=("get_equity_historicals",),
        gw_tools=("get_context_pack", "compute_indicators",
                  "record_training_row", "get_backtest_summary"),
        kickoff=(
            "Reconstruct ML training rows per your instructions for: {symbol}. "
            "Start by calling get_context_pack."
        ),
    ),
    "backtester": Role(
        prompt_file="backtester.md",
        rb_tools=("get_earnings_results", "get_equity_historicals", "search"),
        gw_tools=("get_context_pack", "record_backtest_result", "get_backtest_summary"),
        kickoff=(
            "Backfill backtest data per your instructions for: {symbol}. "
            "Start by calling get_context_pack."
        ),
    ),
    "strategist": Role(
        prompt_file="strategist.md",
        rb_tools=(),
        gw_tools=(
            "get_context_pack", "get_performance_summary",
            "get_labeled_decisions", "get_backtest_summary",
            "propose_policy_update", "propose_playbook_update",
        ),
        include_playbook=True,
        kickoff=(
            "Run a policy review per your instructions. Start by calling "
            "get_context_pack, then get_performance_summary."
        ),
    ),
}


def policy_text_and_version() -> tuple[str, str]:
    text = (PROMPTS / "POLICY.md").read_text()
    m = re.search(r"(?m)^Version:\s*(\S+)", text)
    return text, (m.group(1) if m else "0.0.0")


def _gateway_env(policy_version: str) -> dict[str, str]:
    env = {
        "PYTHONPATH": str(REPO_ROOT),
        "EARNINGS_POLICY_VERSION": policy_version,
    }
    for key, val in os.environ.items():
        if key.startswith("EARNINGS_"):
            env[key] = val
    env["EARNINGS_POLICY_VERSION"] = policy_version  # POLICY.md wins
    return env


def _write_mcp_config(policy_version: str) -> Path:
    config = {
        "mcpServers": {
            "robinhood-trading": {"type": "http", "url": ROBINHOOD_URL},
            "earnings": {
                "command": sys.executable,
                "args": ["-m", "gateway.mcp_server"],
                "env": _gateway_env(policy_version),
            },
        }
    }
    fd, path = tempfile.mkstemp(prefix="mcp-earnings-", suffix=".json")
    with os.fdopen(fd, "w") as fh:
        json.dump(config, fh)
    return Path(path)


def _model_chain(primary: str) -> list[str]:
    """Ordered models to try. On a usage-limit exhaustion of one, run_role
    advances to the next. FALLBACK_MODEL is always the tail so a limited Fable
    run degrades to Opus rather than failing the whole tick."""
    chain = [primary]
    if FALLBACK_MODEL not in chain:
        chain.append(FALLBACK_MODEL)
    return chain


def _run_capturing(cmd: list[str], *, timeout: int) -> tuple[int, str]:
    """Run cmd, tee its combined output live to our stdout, and also return it
    so the caller can inspect for the usage-limit signature. Hard-kills at
    `timeout` (returns 124), matching the launchd per-run cap."""
    proc = subprocess.Popen(
        cmd, cwd=str(REPO_ROOT), text=True, bufsize=1,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    buf: list[str] = []

    def _pump() -> None:
        assert proc.stdout is not None
        for line in proc.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            buf.append(line)

    pump = threading.Thread(target=_pump, daemon=True)
    pump.start()
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
        pump.join(timeout=5)
        return 124, "".join(buf)
    pump.join(timeout=5)
    return proc.returncode, "".join(buf)


def run_role(role_name: str, *, symbol: str | None = None,
             model: str | None = None) -> int:
    if shutil.which("claude") is None:
        print("error: `claude` CLI not found on PATH.", file=sys.stderr)
        return 127
    role = ROLES[role_name]
    model = model or role.model or DEFAULT_MODEL
    if "{symbol}" in role.kickoff and not symbol:
        print(f"error: role {role_name!r} requires a symbol.", file=sys.stderr)
        return 2

    policy, version = policy_text_and_version()
    mission = (PROMPTS / role.prompt_file).read_text() + "\n\n---\n\n" + policy
    if role.include_playbook and (PROMPTS / "PLAYBOOK.md").exists():
        mission += "\n\n---\n\n" + (PROMPTS / "PLAYBOOK.md").read_text()
    kickoff = role.kickoff.format(symbol=symbol or "")

    allowed = (
        [f"mcp__robinhood-trading__{t}" for t in role.rb_tools]
        + [f"mcp__earnings__{t}" for t in role.gw_tools]
        + list(role.builtin_tools)
    )
    mcp_config = _write_mcp_config(version)
    chain = _model_chain(model)
    try:
        for i, active in enumerate(chain):
            cmd = ["claude", "-p", kickoff, "--model", active]
            # Keep the CLI's own overload/unavailable fallback pointed at the
            # models we haven't tried yet (comma-separated list). This is the
            # OTHER failure class; our loop handles usage-limit exhaustion.
            downstream = chain[i + 1:]
            if downstream:
                cmd += ["--fallback-model", ",".join(downstream)]
            cmd += [
                "--mcp-config", str(mcp_config),
                "--strict-mcp-config",
                "--append-system-prompt", mission,
                "--allowedTools", *allowed,
            ]
            print(f"launching {role_name} (model={active}, policy v{version}"
                  + (f", symbol={symbol}" if symbol else "") + ")\n")
            # Hard cap per agent run: launchd drops a fire while the same label
            # is still running, so a hung 16:20 run would silently eat the 16:50
            # disaster-valve run. 22 minutes guarantees the next fire always
            # gets its slot. A killed run is safe: queued/placed orders live at
            # the broker and the next run reconciles via get_equity_orders.
            rc, out = _run_capturing(cmd, timeout=1320)
            if rc == 124:
                print(f"error: {role_name} run exceeded 22min and was killed — "
                      "next tick will reconcile", file=sys.stderr)
                return 124
            if rc != 0 and _USAGE_LIMIT_RE.search(out) and i + 1 < len(chain):
                print(f"notice: {active} usage-limited — falling back to "
                      f"{chain[i + 1]} for {role_name}", file=sys.stderr)
                continue
            return rc
        return rc  # all models usage-limited; return the last rc (non-zero)
    finally:
        mcp_config.unlink(missing_ok=True)
