# CLAUDE.md — session primer

You are working on **agentic-earnings-trading**: Claude-orchestrated trading
around earnings events (BMO/AMC), AI/data-center universe first. Read
`ARCHITECTURE.md` for full design; this file is the fast orientation.

## The 30-second orientation

Headless agent runs (`claude -p`) analyze upcoming earnings using **read-only**
Robinhood MCP tools and submit decisions to a **local gateway MCP server**. The
gateway runs a **server-side risk gate** and records everything — decisions
with their full feature snapshots, then labeled outcomes — into SQLite. That
dataset will train an ML sidecar (Phase 4).

**LIVE since 2026-07-05** (operator-armed; ~$150 account; caps $120/position,
$140/day; arm expires 2026-08-04 — re-arm consciously, don't auto-renew).
Strategy = policy v0.2.0 event-window gap capture: AMC enter ~15:45 ET report
day / exit after-hours or next open; BMO enter T-1 close / exit post-report
open. Three ticks daily: 09:31 exits · 15:40 entries · 16:50 AMC after-hours
exits (PDT-budgeted).

## Critical rules — memorize before touching anything

1. **Capital rules live in `engine/risk.py`, never in prompts.** Prompts guide
   quality; the gate enforces safety. Never soften, bypass, or duplicate gate
   logic in a prompt. Only the **executor** role carries order tools, and the
   tick launches it only while the arm switch is active — never add order
   tools to scout/analyst/labeler/strategist.
2. **The arm switch is the operator's alone.** Live orders require an
   unexpired `.arm-live.json` (written only by
   `python -m orchestrator.main arm-live --confirm`; gitignored; time-boxed;
   live caps tighter than engine caps). No agent tool may create, modify, or
   read around it. Disarmed ⇒ everything is paper. Never build a path that
   arms programmatically.
3. **Dataset integrity outranks convenience.** Every `submit_decision` —
   including `pass` — must carry the real feature snapshot and gets stamped
   with the policy version. Don't backfill, edit, or delete decision rows;
   corrections go in as new rows or outcome notes. Passes get counterfactual
   labels after their event — that's dataset, not busywork.
4. **Policy self-improvement is versioned and audited.** The strategist may
   rewrite `prompts/POLICY.md` only through `propose_policy_update` (version
   bump + required sections validated server-side, git-committed with
   rationale). It cannot touch engine caps, allowlists, arming, or code.
5. **Bearish = options, never equity shorts.** Robinhood doesn't support
   shorting. Bearish stays a paper leg (inverse delta-one proxy) even in live
   mode, until Phase 5b builds real options execution.

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

    # Daily automation (launchd; fires 09:31 / 15:40 / 16:50 local)
    python -m orchestrator.daily --dry-run                    # auto phase
    python -m orchestrator.daily --phase afternoon --dry-run  # specific phase
    python -m orchestrator.main backtest [SYMBOL]             # backfill gap/drift stats
    python -m orchestrator.schedule status       # loaded state + stderr tail
    python -m orchestrator.schedule install --hour 10 --minute 0   # reschedule
    python -m orchestrator.schedule uninstall

    # Live trading (REAL MONEY) — operator-only release lever
    python -m orchestrator.main arm-live --confirm            # $200/pos, $400/day, 7 days
    python -m orchestrator.main arm-live --per-position 100 --daily 200 --days 3 --confirm
    python -m orchestrator.main disarm                        # instant kill

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
