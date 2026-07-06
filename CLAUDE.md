# CLAUDE.md — session primer

You are working on **agentic-earnings-trading**: Claude-orchestrated,
real-money trading around earnings events. Read `ARCHITECTURE.md` for full
design; this file is the fast orientation.

## The 30-second orientation

Headless agent runs (`claude -p`, Opus 4.8 default / Sonnet for clerical
roles) analyze earnings events using read-only Robinhood MCP tools and act
through a **local gateway MCP server** whose **server-side risk gate** has the
final word. Everything — decisions with full feature snapshots, outcomes,
pass counterfactuals, reconstructed training rows — lands in SQLite and feeds
a self-retraining ML sidecar plus a strategist that revises the trading
policy and per-symbol playbook itself (git-committed).

**LIVE since 2026-07-05** (operator-armed; account ••••8223 'Agentic', cash,
$500; caps $250/position, $450/day; arm expires **2026-08-04** — re-arm is a
deliberate operator act, never automatic).

**Strategy (policy v0.6.x, evidence-locked — see reports/research/)**:
earnings-gap capture, market-wide. AMC: enter 15:45–15:58 ET on report day.
BMO: enter 15:45–15:58 the prior trading day. ALL exits fill in the next
9:30 **opening auction** (queued gtc market close from the evening tick;
verified/placed at the 9:24 pre-open run). Only early exit: the 16:50
disaster valve (≥10% persistent AH loss). No resting broker stops (whipsaw
harvest + no AH execution + gap-through). Hold cash between events.

**Ticks (launchd, ET)**: 09:24 morning (exits→monitor→scout→labeler→
strategist→ML→briefing) · 15:40 afternoon (analysis + entries) · 16:20/16:50
evening (exit queueing + valve). `com.earnings.caffeinate` holds the Mac
awake 08:05–17:10 weekdays. Per-run 22-min timeout.

## Critical rules — memorize before touching anything

1. **Capital rules live in `engine/risk.py`, never in prompts.** Only the
   **executor** role carries order tools; it runs only while armed, only on
   the designated account, only on kickoff-named jobs. Never add order tools
   to any other role.
2. **The arm switch is the operator's alone** (`engine/arming.py`,
   `.arm-live.json`, gitignored, time-boxed). No agent tool may touch it;
   never build a path that arms programmatically. Same for
   `enable-shorting` (currently OFF: cash account, margin conversion
   pending, FINRA $2k; bearish = paper legs until the operator clears it).
3. **Dataset integrity outranks convenience.** Every submit_decision —
   including `pass` — carries the real feature snapshot (server-computed
   indicators/implied move embedded verbatim) and the policy version. Never
   backfill/edit/delete decision rows. Training-row reconstruction must
   never include reaction-day bars (lookahead leakage).
4. **Self-improvement is versioned and audited.** The strategist edits
   POLICY.md / PLAYBOOK.md only through the validated gateway tools
   (version bump / rationale enforced, git-committed). It cannot touch
   engine caps, allowlists, arming, or code.
5. **Market-wide, but screened.** Core 15 names always tradeable; any other
   earnings name only when its event passed the scout-recorded liquidity
   screen (gate-enforced), with reduced sizing and mandatory backtest
   backfill. Check per-stock session support before any extended-hours
   action.
6. **Any schedule/launchd change gets a defanged `launchctl kickstart`
   validation** — interactive shells mask launchd failures (proven: the
   claude-PATH bug only appeared under a real fire).

## Key files

    engine/         config · risk (gate) · arming · store (6 tables +
                    migrations) · indicators · ml · context (pack + DIRECTIVES)
    gateway/mcp_server.py   all agent tools + server-side gate + screen
    orchestrator/   launcher (roles/models/allowlists/timeout) · daily
                    (phased ticks + guards) · schedule (launchd, hardened) ·
                    briefing (deterministic) · main (CLI)
    prompts/        POLICY.md (versioned) · PLAYBOOK.md (per-symbol evidence)
                    · 8 role missions
    reports/        BRIEFING.md (auto-committed daily) · research/ (dated
                    studies + scripts)
    DIRECTIVES.md   operator steering — injected into every context pack

## Common commands

    python -m pytest -q                          # 63 tests — run before commits
    python -m orchestrator.main status           # context pack
    python -m orchestrator.main report [--write] # operator briefing
    python -m orchestrator.daily --phase morning|afternoon|evening --dry-run
    python -m orchestrator.main analyze SYM | scout | backtest [SYM] | monitor
    python -m orchestrator.main ml-train | ml-backfill [SYM]
    python -m orchestrator.main close SYM --price X          # manual paper close
    python -m orchestrator.main arm-live ... --confirm | disarm
    python -m orchestrator.main enable-shorting --confirm | disable-shorting
    python -m orchestrator.schedule install | status | uninstall

## Env overrides (Config.from_env)

    EARNINGS_MODE / EARNINGS_DB / EARNINGS_UNIVERSE / EARNINGS_MACRO_WATCH
    EARNINGS_MAX_POSITION_USD / EARNINGS_MAX_DAILY_USD / EARNINGS_MAX_OPEN_POSITIONS
    EARNINGS_MAX_ANALYST_RUNS (default 6/day)

## Working with the operator (Mike)

- Terse, decisive answers; show tradeoffs, give a recommendation.
- Confirm before anything that spends money beyond the armed flow, arms/
  disarms, or publishes externally.
- Tests must pass before committing engine/gateway/orchestrator changes.
- Record verified run findings (dated) in ARCHITECTURE §8 — never undated
  claims. Dated research goes in reports/research/ with reproducible scripts.
- The operator steers via DIRECTIVES.md; read it, it's in every context pack.
