# CLAUDE.md — session primer

You are working on **agentic-earnings-trading**: Claude-orchestrated trading
around earnings events (BMO/AMC), AI/data-center universe first. Read
`ARCHITECTURE.md` for full design; this file is the fast orientation.

## The 30-second orientation

Headless agent runs (`claude -p`) analyze upcoming earnings using **read-only**
Robinhood MCP tools and submit decisions to a **local gateway MCP server**. The
gateway runs a **server-side risk gate** and records everything — decisions
with their full feature snapshots, then labeled outcomes — into SQLite. That
dataset will train an ML sidecar (Phase 4). Currently **paper mode only**.

## Critical rules — memorize before touching anything

1. **Capital rules live in `engine/risk.py`, never in prompts.** Prompts guide
   quality; the gate enforces safety. Never soften, bypass, or duplicate gate
   logic in a prompt, and never widen a role's tool allowlist to include
   `place_*_order` / `cancel_*` tools in v1.
2. **Paper mode is the only mode.** The gate rejects non-paper. Live trading is
   Phase 5, opt-in per run, and requires explicit operator instruction to build.
3. **Dataset integrity outranks convenience.** Every `submit_decision` —
   including `pass` — must carry the real feature snapshot and gets stamped
   with the policy version. Don't backfill, edit, or delete decision rows;
   corrections go in as new rows or outcome notes.
4. **Policy changes bump the version.** `prompts/POLICY.md` carries a
   `Version:` line; the launcher stamps it onto decisions. Changing thresholds
   or sizing without bumping the version corrupts outcome analysis.
5. **Bearish = options, never equity shorts.** Robinhood doesn't support
   shorting. v1 paper tracks bearish as inverse delta-one notional on the
   underlying — a known simplification, documented in ARCHITECTURE §4.

## Key files

    engine/config.py         Config/RiskLimits + EARNINGS_* env overrides
    engine/risk.py           RiskGate — position cap, daily budget, max open,
                             universe, duplicate, paper-only
    engine/store.py          SQLite: events / decisions / outcomes (UTC ISO)
    engine/context.py        CONTEXT PACK builder (gateway + CLI `status`)
    gateway/mcp_server.py    FastMCP stdio: get_context_pack,
                             record_earnings_event, submit_decision,
                             close_paper_position
    orchestrator/launcher.py Role defs (scout/analyst), tool allowlists,
                             temp MCP config, claude -p invocation
    orchestrator/main.py     CLI: scout | analyze SYMBOL | status | close
    prompts/POLICY.md        Versioned trading policy (parse: "Version: X.Y.Z")
    prompts/scout.md         Scout mission
    prompts/analyst.md       Analyst mission
    datasets/                SQLite + exports (gitignored)

## Common commands

    # One-time setup
    python3 -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"

    # Tests (run before any commit touching engine/ or gateway/)
    python -m pytest -q

    # Show current context pack (no agent, no cost)
    python -m orchestrator.main status

    # Agent runs (headless claude -p; needs Robinhood MCP OAuth done in Claude Code)
    python -m orchestrator.main scout                    # sync earnings calendar → store
    python -m orchestrator.main analyze NVDA             # analyst run for one symbol
    python -m orchestrator.main analyze NVDA --model claude-fable-5

    # Manual paper close / labeling (the daily tick's labeler handles this too)
    python -m orchestrator.main close NVDA --price 187.50 --notes "T+1 open"

    # Daily automation (launchd; installed 2026-07-05 at 09:45 local)
    python -m orchestrator.daily --dry-run       # what would the tick do
    python -m orchestrator.daily                 # full tick now
    python -m orchestrator.schedule status       # loaded state + stderr tail
    python -m orchestrator.schedule install --hour 10 --minute 0   # reschedule
    python -m orchestrator.schedule uninstall

## Env overrides (read by Config.from_env)

    EARNINGS_MODE            paper (default; gate rejects anything else in v1)
    EARNINGS_DB              path to sqlite (default datasets/earnings.sqlite3)
    EARNINGS_UNIVERSE        CSV of symbols (default: AI/data-center list in config.py)
    EARNINGS_MAX_POSITION_USD / EARNINGS_MAX_DAILY_USD / EARNINGS_MAX_OPEN_POSITIONS

## Working with the operator

- Terse, decisive answers; show tradeoffs, give a recommendation.
- Confirm before anything that spends money, places real orders, or publishes.
- Tests must pass before committing engine/gateway changes.
- Record verified run findings (dated) in ARCHITECTURE §8 — never undated claims.
