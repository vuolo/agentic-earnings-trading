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
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PROMPTS = REPO_ROOT / "prompts"
ROBINHOOD_URL = "https://agent.robinhood.com/mcp/trading"
DEFAULT_MODEL = "claude-sonnet-5"

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


ROLES: dict[str, Role] = {
    "scout": Role(
        prompt_file="scout.md",
        rb_tools=("get_earnings_calendar", "search", "get_equity_quotes"),
        gw_tools=("get_context_pack", "record_earnings_event"),
        kickoff=(
            "Sync the upcoming earnings calendar per your instructions. "
            "Start by calling get_context_pack."
        ),
    ),
    "analyst": Role(
        prompt_file="analyst.md",
        rb_tools=ANALYST_RB_TOOLS,
        gw_tools=("get_context_pack", "submit_decision"),
        kickoff=(
            "Analyze the upcoming earnings event for {symbol} and submit a "
            "decision per your instructions. Start by calling get_context_pack."
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


def run_role(role_name: str, *, symbol: str | None = None, model: str = DEFAULT_MODEL) -> int:
    if shutil.which("claude") is None:
        print("error: `claude` CLI not found on PATH.", file=sys.stderr)
        return 127
    role = ROLES[role_name]
    if "{symbol}" in role.kickoff and not symbol:
        print(f"error: role {role_name!r} requires a symbol.", file=sys.stderr)
        return 2

    policy, version = policy_text_and_version()
    mission = (PROMPTS / role.prompt_file).read_text() + "\n\n---\n\n" + policy
    kickoff = role.kickoff.format(symbol=symbol or "")

    allowed = [f"mcp__robinhood-trading__{t}" for t in role.rb_tools] + [
        f"mcp__earnings__{t}" for t in role.gw_tools
    ]
    mcp_config = _write_mcp_config(version)
    cmd = [
        "claude", "-p", kickoff,
        "--model", model,
        "--mcp-config", str(mcp_config),
        "--strict-mcp-config",
        "--append-system-prompt", mission,
        "--allowedTools", *allowed,
    ]
    print(f"launching {role_name} (model={model}, policy v{version}"
          + (f", symbol={symbol}" if symbol else "") + ")\n")
    try:
        return subprocess.run(cmd, cwd=str(REPO_ROOT)).returncode
    finally:
        mcp_config.unlink(missing_ok=True)
