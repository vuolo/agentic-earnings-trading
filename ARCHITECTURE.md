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

## 1.5 The breathing loop (operating model)

The system is designed to run, learn, and trade autonomously:

```
        ┌──────────────────────────────────────────────────────┐
        │                 daily tick (launchd)                 │
        │  scout → labeler → analyst → executor → strategist   │
        └──────────────────────────────────────────────────────┘
 scout:      keeps the earnings calendar fresh
 labeler:    closes due paper positions; labels PASS counterfactuals
             (passes teach the dataset too — what was avoided or missed)
 analyst:    one decision per event entering its window, full snapshot
 executor:   REAL orders — runs only while the operator's arm switch is on
 strategist: every ≥3 new labeled outcomes, reviews the dataset and revises
             POLICY.md itself (version bump + git commit = audit trail)
```

**What never becomes autonomous** (the grip points):

1. `engine/risk.py` caps and the gateway's enforcement — code, not policy text.
   The strategist rewrites policy; the gate still rejects at the caps.
2. **The arm switch** (`engine/arming.py`): live orders require an unexpired
   `.arm-live.json` written only by the operator via
   `python -m orchestrator.main arm-live --confirm` — time-boxed (default 7
   days), with live caps *tighter* than engine caps (defaults $200/position,
   $400/day). No agent has any tool that can create or modify it. Disarm is
   instant. When it expires, the system degrades safely back to paper.
3. Role tool allowlists: only the executor carries order tools, and the tick
   launches it only while armed, with the exact approved jobs in its kickoff.
4. Dataset integrity: decisions are never edited or deleted; policy changes
   land as git commits stamped with rationale.

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

## 3.5 Live strategy (operator-directed, 2026-07-05 — policy v0.2.0)

Real capital (~$150 account, live caps $120/position, $140/day). Event-window
gap capture, cash-first:

- **AMC**: decide + enter on the afternoon tick (fills ~15:45–15:58 ET before
  the close); exit same-day after-hours on the evening tick when the PDT
  budget allows, else next open. Minutes-to-hours exposure.
- **BMO**: decide + enter T-1 afternoon; exit at the post-report open on the
  morning tick. Overnight exposure through the print — higher evidence bar.
- **Backtest alignment**: the backtests table stores per-event pre_close /
  post_open / post_close for past reports; `get_backtest_summary` turns that
  into gap and drift stats the analyst must weigh (up_rate, worst gap vs.
  sizing) before entering.
- **Balance-aware**: the executor reports a real account snapshot
  (equity/cash/buying power) at the start of every run; it sizes down to
  buying power, never up. The context pack shows the snapshot and the PDT
  budget to every agent.
- **Settlement (not PDT)**: the designated account (••••8223 'Agentic') is a
  CASH account — PDT does not apply. The binding rule is T+1 settlement /
  good-faith violations: the evening tick refuses a same-day exit whenever a
  live close already happened that day (the entry would have been funded by
  unsettled proceeds); positions ride to the open, where the proceeds have
  settled.
- **Order mechanics (verified against the API 2026-07-05)**: fractional /
  dollar-notional orders are market + regular-hours only; extended hours is
  whole-share limit only; shorting is impossible (cash account + API rejects
  fractional shorts). Entries prefer whole shares (marketable limit) when the
  price fits the size — those can exit after-hours — else dollar-notional
  market. All order tools use the designated account only.

Tick schedule (launchd, local = ET): **09:31** morning (exits at the open,
labeling, scout, strategist) · **15:40** afternoon (analysis + entries) ·
**16:50** evening (authorized AMC after-hours exits).

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
- **Phase 2 — Deterministic feature engine (built 2026-07-05).**
  `engine/indicators.py` (RSI-14, ATR%, realized vol, volume z-score, SMA
  trend, distance from high/low, relative strength, implied move) exposed via
  the gateway's `compute_indicators` / `compute_implied_move` — agents pass
  raw bars, the server does the math, outputs embed verbatim in snapshots
  (standard keys the ML trains on). Analyst sentiment now uses the WebSearch
  builtin with cited headlines. Labeler feeds realized events back into the
  backtests table; Monday morning refresh completes them.
- **Phase 3 — Scheduler (built 2026-07-05).** `orchestrator/daily.py` is a
  deterministic tick: scout → labeler (closes positions whose report date has
  passed) → analyst (events entering the decision window: T-1 for bmo/unknown,
  T-1 or report day for amc; skipped if the event already has a decision).
  `orchestrator/schedule.py` installs it as a launchd user agent
  (`com.earnings.daily`, default 09:45 local — just after the open so quotes
  are live). Aqua-session-only: the tick needs the user's `claude` login and
  Robinhood OAuth. PATH is baked into the plist (stake repo lesson: launchd
  strips PATH and dud runs follow).
- **Phase 4 — ML sidecar (pipeline built 2026-07-05, self-activating).**
  `engine/ml.py`: logistic regression on standardized snapshot features →
  P(post-event move up), CV-scored, saved as plain JSON (pure-Python
  inference, no pickle). The morning tick retrains daily — a no-op below 25
  usable labeled rows, ADVISORY until ~50. `get_ml_prediction` is in the
  analyst's toolset from day one and reports its own untrained state
  honestly. Graduation from advisory to primary signal is a strategist +
  operator decision based on CV accuracy vs. base rate.
- **Phase 5a — Live execution scaffolding (built 2026-07-05, DISARMED).**
  Executor role (equity only: buy limit with 1% price guard, sell-to-close,
  review-before-place, real fills reported back), `pending_live → open_live →
  closed_live` lifecycle, arm switch + arm-aware risk gate. Bearish stays a
  paper leg until live options execution exists. Arming is the operator's
  single release lever; off by default, forever.
- **Phase 5b — Live options execution (SHELVED by operator decision,
  2026-07-05).** The strategy is stocks-only: live capital goes long equity,
  bearish theses stay paper-only dataset legs. The Agentic account has option
  level 2 (upgraded 2026-07-05), so this phase is unblocked if the operator
  ever changes the strategy — but it is not on the roadmap.

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

- **2026-07-05** — Repo scaffolded; risk gate + store covered by 17 passing
  tests; `status` CLI and gateway server verified locally.
- **2026-07-05** — **Headless OAuth reuse verified**: `claude -p` with a
  strict MCP config pointing at the Robinhood trading URL reused the OAuth
  established interactively in Claude Code (`get_earnings_calendar` returned
  28 entries, Haiku 4.5, one tool call). The orchestrator's launch path is
  viable as designed.
- **2026-07-05** — **First live agent cycle** (Sonnet 5): scout found one
  universe event in window (TSM 2026-07-16 bmo, verified) and recorded it;
  analyst assembled the full snapshot (implied move 9.58% via ATM straddle vs.
  6-quarter mean abs reaction 2.75%) and submitted decision #1: **pass**,
  conviction 0.3 — implied move 3.5x historical realized makes long premium
  poor value. Noted structural gap: policy v0.1 cannot express vol-selling
  structures; revisit after 7/16 realized move is known.
- **2026-07-05** — Phase 3 scheduler installed (`com.earnings.daily`, 09:45
  local). 23 tests passing. Dry-run tick verified correct due/skip logic.
- **2026-07-05** — Breathing loop built: strategist (policy self-improvement,
  gateway-validated + git-committed), pass counterfactual labeling, live
  execution scaffolding behind the arm switch (disarmed). Migration of the
  live DB to the v2 decisions schema verified (1 row preserved). Found and
  fixed a real upsert bug the dry-run exposed: an event link from
  `submit_decision` downgraded TSM's timing bmo→unknown; upserts now never
  overwrite known timing with 'unknown'. 39 tests passing.
- **2026-07-05** — **ARMED for live trading** (operator instruction): caps
  $120/position, $140/day, expires 2026-08-04. Policy v0.2.0 (operator-
  directed): event-window strategy, $100 base size, backtest alignment
  required. Three-phase tick installed (09:31/15:40/16:50). Backtester role
  added; historical gap/drift backfill run started. 46 tests passing. First
  live-eligible event: TSM 2026-07-16 bmo (entry window 7/15 ~15:45 ET) —
  its 0.1.0 pass will be re-analyzed under v0.2.0 (pass-from-older-policy
  re-analysis rule in daily.py).
- **2026-07-05** — **Intraday exit study** (5-min + hourly bars, all 15
  Apr–Jun reactions; see reports/research/2026-07-05-intraday-exit-study.md):
  exit@open captures +4.72% avg vs +2.69% by 10:00; gap-up winners fade
  −2.7% from the open within 30 min (MU −7.8%, ALAB −10.3%). Morning tick
  reordered — live exits now run before monitor/scout; executor sells before
  snapshotting. Policy v0.4.2 marks open exits time-critical. Research
  hypothesis parked for the strategist: fading gap-ups averaged +2.7% (n=7,
  needs shorting + more data).
- **2026-07-05** — **Exit execution hardened** (operator questions drove
  both): (1) morning fire moved 9:31→9:24 and the evening tick now QUEUES a
  gtc market close after the reaction-day close — exits fill in the 9:30
  opening auction (the exact backtested `post_open` print) and survive a
  dead Mac. (2) Stop-losses analyzed and rejected as resting broker orders
  (don't execute AH/overnight, gap-through, whipsaw harvest — CRDO −11.75%
  @16:20 → −3.12% @open); replaced with a 16:50-only persistence-checked
  disaster valve (≥10% AH loss on two quotes, GFV permitting). Policy
  v0.5.0.
- **2026-07-05** — **API mechanics verified** (schemas + live tradability
  calls): all 15 universe names fractional-tradable; fractional/dollar orders
  are market+regular-hours only (tool-level, regardless of instrument flags);
  extended hours = whole-share limits; equity shorting impossible (designated
  'Agentic' account ••••8223 is CASH — also has no option level yet, a
  prerequisite for Phase 5b). PDT gating replaced with cash-account GFV
  guard. NYSE 2026 holiday/half-day calendar added to the tick's trading-day
  logic.
- **2026-07-05** — **Backtest backfill complete** (Sonnet 5): 90 events, all
  15 universe symbols × 6 quarters (2025-02 → 2026-06). Universe gap
  (T-1 close → post-open): mean +1.77%, std 11.51%, up-rate 0.52, worst
  −20.1% (COHR). Drift (post-open → close): mean −0.64%, up-rate 0.37 —
  **the exit-at-open discipline is empirically right; holding the reaction
  day destroys value on average**. Standouts: TSM bmo gap up-rate 0.83 /
  std 2.39% / worst −1.66% (best risk-adjusted in universe; drift fades
  6/6). Tail-risk names for $100–120 sizing: COHR (−20%), HPE (−15%),
  ORCL (−14.5%).
