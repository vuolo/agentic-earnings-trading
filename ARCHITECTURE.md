# Agentic Earnings Trading — Architecture & Roadmap

> Claude-orchestrated trading around earnings events (BMO / AMC), starting with an
> AI / data-center stock universe. Agent analysts gather statistics, indicators,
> and news/sentiment through the Robinhood MCP server; a **server-side risk gate**
> decides whether any proposed trade is accepted; every decision is captured with
> its full feature snapshot so the accumulated dataset can train an ML sidecar
> that eventually becomes the primary signal source.

---

## 1. Design principles

These are load-bearing; don't erode them.

1. **Enforced beats observed.** Any rule that protects capital lives in code the
   model cannot argue with — the risk gate inside the gateway MCP server, not
   the prompt. Prompts state policy for *quality*; the gate enforces it for
   *safety*. (Pattern proven in the stake-synthetics repo: its server-side
   claim guard was un-promptable; its advisory max-loss floor relied on model
   compliance. Here, every capital rule is the enforced kind.)
2. **Heavy context injection.** Every gateway tool response ends with a fresh
   **CONTEXT PACK**: mode, policy version, risk budget remaining, open paper
   positions, upcoming earnings events, recent decisions. The agent never
   operates on stale state and never needs a "check status" round-trip.
3. **Deterministic core, judgmental agents.** Statistics and feature math belong
   in tested Python (`engine/`), not in a language model's arithmetic. Claude's
   job is judgment: weighing stats against sentiment, sizing conviction,
   spotting the weird cases. (Phase 2 moves feature computation from
   agent-gathered to engine-computed.)
4. **Dataset-first.** Every decision — including `pass` — is recorded with the
   feature snapshot the agent saw and the policy version in force. Outcomes are
   labeled after the event. This is the ML sidecar's training set; its
   integrity outranks convenience.
5. **Paper until proven.** The system starts in paper mode. Live order placement
   is not implemented in v1 and the risk gate rejects any non-paper mode. When
   live trading arrives (Phase 5), it will be opt-in per run, budget-capped,
   and off by default — the same "default-safe, flag to arm" posture as the
   reference repo's guard during scaffolding.

## 2. System shape

```
orchestrator/main.py  (CLI: scout | analyze SYMBOL | status | close)
   │  builds temp MCP config + role tool allowlist + prompt (mission + POLICY.md)
   ▼
claude -p  (headless Claude Code, per-role mission prompt)
   │
   ├── mcp: robinhood-trading (remote HTTP, OAuth) — READ-ONLY tools per allowlist
   │       quotes · historicals · fundamentals · earnings calendar/results ·
   │       option chains/quotes · search
   │       (place_*_order / cancel_* are NEVER in an agent allowlist in v1)
   │
   └── mcp: earnings gateway (local stdio, gateway/mcp_server.py)
           get_context_pack · record_earnings_event · submit_decision ·
           close_paper_position
           │  submit_decision runs the RISK GATE server-side; approved
           │  decisions become paper positions; everything lands in the store
           ▼
       engine/  (deterministic, unit-tested)
           config.py  — mode, limits, universe, policy version (env-overridable)
           risk.py    — RiskGate: position cap, daily budget, max open,
                        universe membership, duplicate check, paper-only
           store.py   — SQLite: events, decisions (+feature snapshots), outcomes
           context.py — CONTEXT PACK builder (shared by gateway + CLI status)
```

### Agent roles (v1)

| Role | Mission | Robinhood tools | Gateway tools |
|---|---|---|---|
| **scout** | Sync the next ~14 days of earnings events for the universe into the store | `get_earnings_calendar`, `search`, `get_equity_quotes` | `get_context_pack`, `record_earnings_event` |
| **analyst** | Deep-dive one symbol's upcoming event; build the feature snapshot; submit a decision (`long_equity` / `bearish_option` / `pass`) | read-only market-data set | `get_context_pack`, `submit_decision` |

Later roles: **labeler** (post-event outcome labeling), **executor** (live orders,
Phase 5 only), **portfolio reviewer**.

## 3. Data model (SQLite, `datasets/earnings.sqlite3`)

- **events** — `(symbol, report_date)` unique; `timing ∈ {bmo, amc, unknown}`;
  raw calendar payload kept as JSON.
- **decisions** — one row per agent verdict: action
  (`long_equity | bearish_option | pass`), size, entry price, conviction,
  thesis, **features JSON** (the snapshot the agent saw), policy version,
  risk verdict, status (`pass | rejected | open_paper | closed_paper`).
- **outcomes** — exit price, realized move %, P&L, notes; labeled after the
  event. Joined to decisions, this is the training table.

Timestamps are UTC ISO-8601. "Today" for the daily risk budget is the UTC day.

## 4. Trading constraints & simplifications

- **No equity shorting on Robinhood.** The bearish action is `bearish_option`
  (long puts / put spreads). In v1 paper mode, bearish positions are tracked as
  **delta-one notional on the underlying** (inverse sign) — a stated
  simplification. Real option P&L modeling (premium, IV crush, greeks) is
  Phase 2/4 work; until then bearish paper P&L overstates what puts would do.
- **Paper fills at agent-quoted reference price.** The analyst passes the quote
  it just fetched; the gateway fills at that price. Good enough for dataset
  bootstrapping; slippage modeling comes later.
- **Risk limits (defaults, env-overridable):** $1,000 per position ·
  $2,500 new exposure per UTC day · 5 open positions max · universe allowlist.

## 5. Policy

`prompts/POLICY.md` is the versioned trading policy (entry requirements,
conviction threshold, sizing, exit discipline, universe). The launcher parses
its `Version:` line and stamps every decision with it, so outcome analysis can
be sliced by policy version. Change the policy → bump the version.

## 6. Roadmap

- **Phase 0 — Scaffold (this commit).** Engine + gateway + orchestrator +
  prompts + tests. Paper-only, agent-gathered features.
- **Phase 1 — Live agent loop.** Run scout + analyst against real market data
  daily; accumulate decisions across a few earnings cycles; manual `close` /
  labeling via CLI. Verify headless OAuth reuse of the Robinhood MCP.
- **Phase 2 — Deterministic feature engine.** Move feature computation into
  `engine/features.py`: historical earnings reaction distributions (last 8–12
  quarters), implied move from ATM straddle vs. realized-move stats, trend /
  momentum indicators. Agents consume computed features instead of assembling
  them. Automated post-event **labeler** run.
- **Phase 3 — Scheduler.** Market-calendar-driven automation (launchd or
  `claude` scheduled routines): pre-market scout, analyst runs T-1 before each
  event, labeler T+1. The stake repo's `schedule.py` is the reference pattern.
- **Phase 4 — ML sidecar.** Train on the decisions⋈outcomes table (features →
  post-earnings move / P&L). Model output becomes a feature in the context
  pack first (advisory), then the primary signal with Claude as orchestrator
  and sanity layer.
- **Phase 5 — Live capital (gated).** Executor role with `place_equity_order` /
  `place_option_order`, armed per-run by explicit flag, hard budget caps in the
  gate, order review via `review_*_order` before placement. Off by default,
  forever.

## 7. Repo layout

```
agentic-earnings-trading/
├── ARCHITECTURE.md          ← this document
├── CLAUDE.md                ← session primer (auto-loaded by Claude Code)
├── README.md                ← overview + quick start
├── .mcp.json                ← Robinhood MCP (project scope, for interactive sessions)
├── pyproject.toml
├── engine/                  ← deterministic core (unit-tested)
│   ├── config.py            ← Config / RiskLimits, env overrides
│   ├── risk.py              ← RiskGate
│   ├── store.py             ← SQLite store (events / decisions / outcomes)
│   └── context.py           ← CONTEXT PACK builder
├── gateway/
│   └── mcp_server.py        ← FastMCP stdio server; risk gate lives here
├── orchestrator/
│   ├── launcher.py          ← role defs, MCP config, claude -p invocation
│   └── main.py              ← CLI entry point
├── prompts/
│   ├── POLICY.md            ← versioned trading policy
│   ├── scout.md             ← scout mission prompt
│   └── analyst.md           ← analyst mission prompt
├── tests/                   ← pytest (risk gate + store)
├── datasets/                ← SQLite + exports (gitignored)
└── logs/                    ← run logs (gitignored)
```

## 8. Verified findings (dated)

Keep this section honest — dated entries only, from real runs.

- **2026-07-05** — Repo scaffolded; risk gate + store covered by tests.
  Robinhood MCP OAuth established interactively in Claude Code. Headless
  (`claude -p`) reuse of that OAuth is **assumed but not yet verified** — first
  Phase 1 task.
