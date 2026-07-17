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
   exists only behind the operator's time-boxed arm switch; disarmed (or
   expired) means everything degrades safely to paper. Armed live trading
   (since 2026-07-05) still runs under caps tighter than the engine's, and
   re-arming is always a deliberate operator act — never automatic.

## 1.5 The breathing loop (operating model)

The system is designed to run, learn, and trade autonomously:

```
   launchd fires (ET): 09:24 morning · 15:40 afternoon · 16:20 + 16:50 evening
   (com.earnings.caffeinate holds the Mac awake 08:05→~17:10 weekdays)

 morning:   executor FIRST (verify/place exits pre-open → 9:30 auction fills)
            → monitor (real snapshot + RECONCILE) → scout (market-wide sweep)
            → labeler (paper closes, pass counterfactuals, realized backtest
            rows) → strategist (gated) → ML retrain → briefing commit
 afternoon: analyst per due event (core first, screened next, capped/day)
            → executor entries fill 15:45–15:58
 evening:   queue tomorrow's auction exit (gtc market close — crash-proof)
            + disaster valve at 16:50 (≥10% persistent AH loss)

 strategist: every ≥3 new labeled outcomes, revises POLICY.md AND PLAYBOOK.md
             itself (validated tools, version bump / rationale, git commits)
 mlbackfill: reconstructs historical training rows (indicators as-of T-1 +
             realized gap labels) so the ML trains before live rows accumulate
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
orchestrator/daily.py (phased tick) · main.py (operator CLI) · schedule.py (launchd)
   │  temp MCP config + per-role tool allowlist + mission (+ POLICY.md [+ PLAYBOOK.md])
   │  Fable 5 default (fallback Opus 4.8); monitor + clerical on Sonnet 5; 22-min timeout/run
   ▼
claude -p  (headless Claude Code, per-role mission prompt)
   │
   ├── mcp: robinhood-trading (remote HTTP, OAuth) — allowlisted per role;
   │       order tools exist ONLY in the executor role
   │
   └── mcp: earnings gateway (local stdio, gateway/mcp_server.py) — only write path
           context: get_context_pack (appended to every mutating response)
           calendar: record_earnings_event (+ liquidity screen fields)
           deciding: submit_decision (RISK GATE server-side) · get_backtest_summary ·
                     compute_indicators · compute_implied_move · get_ml_prediction
           executing: get_pending_executions · report_execution · report_live_close ·
                     report_account_snapshot
           labeling: close_paper_position · label_pass_outcome · record_backtest_result ·
                     record_training_row
           learning: get_performance_summary · get_labeled_decisions ·
                     propose_policy_update · propose_playbook_update
           ▼
       engine/  (deterministic, unit-tested — no AI in this layer)
           config.py     — mode, limits, universe/macro/screen thresholds (env)
           risk.py       — RiskGate: caps (min of engine+arm), budget, max open,
                           core-or-screened universe, duplicate, short enable
           arming.py     — operator-only live switch (.arm-live.json, time-boxed)
           store.py      — SQLite: events(+screen), decisions, outcomes,
                           backtests, training_rows, meta
           indicators.py — RSI/ATR/vol/z-score/trend/implied-move math
           ml.py         — LogReg sidecar: daily retrain, JSON model, CV-scored
           context.py    — CONTEXT PACK builder (+ DIRECTIVES.md injection)
```

### Agent roles

| Role | Model | Mission | Order tools? |
|---|---|---|---|
| **scout** | Fable→Opus | market-wide calendar sweep + liquidity screening (price/volume/tradability per candidate) | no |
| **analyst** | Fable→Opus | one event per run: server-computed features, WebSearch sentiment, backtest+playbook alignment, ML advisory → submit_decision | no |
| **executor** | Fable→Opus | ONLY armed, ONLY kickoff-named jobs, ONLY the designated account: auction-exit queue/verify, entries, valve, snapshot | **yes (sole role)** |
| **labeler** | Fable→Opus | paper closes, pass counterfactuals, realized backtest rows | no |
| **monitor** | Sonnet | daily snapshot + broker⇄store `RECONCILE: OK/MISMATCH` | no |
| **strategist** | Fable→Opus | gated self-revision of POLICY.md + PLAYBOOK.md | no |
| **backtester** | Fable→Opus | historical + realized gap/drift backfills | no |
| **mlbackfill** | Sonnet (one-off) | reconstructed ML training rows | no |

## 3. Data model (SQLite, `datasets/earnings.sqlite3`)

- **events** — `(symbol, report_date)` unique; `timing ∈ {bmo, amc, unknown}`;
  raw calendar payload as JSON; `screened` + `screen` (price/volume/
  tradability) for the market-wide liquidity gate.
- **decisions** — one row per agent verdict: action (`long_equity |
  short_equity | bearish_option | pass`), size, entry price, conviction,
  thesis, **features JSON**, policy version, risk verdict, status
  (`pass | rejected | open_paper | closed_paper | pending_live | open_live |
  closed_live | exec_failed`), exec detail.
- **outcomes** — exit price, realized move %, P&L, notes; labeled after the
  event (incl. pass counterfactuals). Joined to decisions = live training data.
- **backtests** — per past event: pre_close / post_open / post_close (+ raw);
  self-feeds from every realized event.
- **training_rows** — reconstructed historical ML rows (features as-of T-1,
  label = realized gap); unioned into the ML dataset.
- **meta** — account snapshot/type, designated account, short/strategist
  gates, tick health, last error.

Timestamps are UTC ISO-8601. "Today" for the daily risk budget is the UTC day.

## 3.5 Live strategy (operator-directed, 2026-07-05 — policy v0.6.x)

Real capital ($500 cash account ••••8223 'Agentic'; live caps $250/position,
$450/day, armed to 2026-08-04). Event-window gap capture, cash-first,
market-wide with a screened gate:

- **AMC**: decide + enter on the afternoon tick (fills ~15:45–15:58 ET before
  the close); hold through the print; **exit in the next 9:30 opening
  auction** (AH study: next-open +5.74% beat every fixed AH exit). Only
  early-exit path: the 16:50 disaster valve (≥10% persistent AH loss,
  whole shares, GFV permitting).
- **BMO**: decide + enter T-1 afternoon; exit in the post-report opening
  auction. Overnight exposure through the print — higher evidence bar
  (conviction ≥0.70, worst-gap-vs-sizing check).
- **Exit execution**: the evening tick QUEUES a gtc market close after the
  reaction-day close (fills in tomorrow's auction even if the Mac dies); the
  9:24 morning run verifies/places and reports actual fills.
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

- **Market-wide universe (v0.6.0)**: core 15 AI/data-center names always
  tradeable; any other earnings-calendar name only via the scout-recorded,
  gate-enforced liquidity screen (price ≥ $5, avg vol ≥ 500k, tradeable) with
  reduced sizing, a higher conviction bar, and mandatory backtest backfill.
  Session profiles differ per stock (24h / extended / regular-only) — the
  executor checks tradability before any extended-hours action; entries and
  auction exits are regular-hours and universal.

Tick schedule (launchd, local = ET): **09:24** morning (auction exits first,
then monitor/scout/labeler/strategist/ML/briefing) · **15:40** afternoon
(analysis + entries) · **16:20 + 16:50** evening (exit queueing + disaster
valve). Per-run 22-min timeout; launchd plist hardened
(MaterializeDatalessFiles, Interactive QoS, symlink-safe PATH).

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
  $2,500 new exposure per UTC day · 5 open positions max · core-universe OR
  screened-event requirement — always intersected with the tighter arm caps
  in live mode.
- **Shorting**: built end-to-end (`short_equity`, whole shares, buy-to-cover)
  but gate-blocked until the operator's margin conversion lands AND a broker
  probe passes AND `enable-shorting --confirm` is run (FINRA $2k minimum
  likely blocks at current equity). Until then bearish = paper legs.

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
- **Phase 3 — Scheduler (built 2026-07-05, hardened same day).**
  `orchestrator/daily.py` phased ticks (see §1.5) via launchd
  (`com.earnings.daily`, fires 09:24/15:40/16:20/16:50 ET) +
  `com.earnings.caffeinate` (08:05 weekdays, holds the sleeping-prone Mac
  awake through market hours). Aqua-session-only. Hardening validated by a
  real defanged launchd fire: MaterializeDatalessFiles, Interactive QoS,
  symlink-safe PATH, 22-min per-run timeout, stale-pending expiry,
  holiday/half-day calendar.
- **Phase 4 — ML sidecar (pipeline built 2026-07-05, self-activating).**
  `engine/ml.py`: logistic regression on standardized snapshot features →
  P(post-event move up), CV-scored, saved as plain JSON (pure-Python
  inference, no pickle). The morning tick retrains daily — a no-op below 25
  usable labeled rows, ADVISORY until ~50. `get_ml_prediction` is in the
  analyst's toolset from day one and reports its own untrained state
  honestly. Graduation from advisory to primary signal is a strategist +
  operator decision based on CV accuracy vs. base rate.
- **Phase 5a — Live execution (built 2026-07-05; ARMED same day by operator
  instruction, $250/$450 caps to 2026-08-04).** Executor role (fractional-
  first entries, auction-exit queueing, disaster valve, double-buy guard,
  designated-account-only, UUID idempotency), `pending_live → open_live →
  closed_live` lifecycle, arm switch + arm-aware gate. Re-arming is always a
  deliberate operator act.
- **Phase 6 — Market-wide expansion (built 2026-07-05, policy v0.6.0).**
  Scout sweeps the whole earnings calendar; non-core names pass a
  gate-enforced liquidity screen; per-day analyst cap; auto backtest
  backfill for new names; per-stock session awareness. Strategist now
  maintains PLAYBOOK.md as well as POLICY.md; mlbackfill reconstructs
  historical training rows so the ML sidecar trains ahead of live-row
  accumulation.
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
├── DIRECTIVES.md            ← operator steering (injected into every context pack)
├── .mcp.json                ← Robinhood MCP (project scope, interactive sessions)
├── pyproject.toml           ← deps incl. mcp, scikit-learn, numpy
├── engine/                  ← deterministic core (no AI; unit-tested)
│   ├── config.py            ← Config/RiskLimits/universe/macro/screen thresholds
│   ├── risk.py              ← RiskGate (server-side, un-promptable)
│   ├── arming.py            ← operator-only live switch (.arm-live.json)
│   ├── store.py             ← SQLite: events/decisions/outcomes/backtests/
│   │                          training_rows/meta (+ migrations)
│   ├── indicators.py        ← RSI/ATR/vol/z/trend/implied-move math
│   ├── ml.py                ← LogReg sidecar (daily retrain, JSON model)
│   └── context.py           ← CONTEXT PACK builder + DIRECTIVES injection
├── gateway/mcp_server.py    ← the agents' only write path (all tools + gate)
├── orchestrator/
│   ├── launcher.py          ← role defs/allowlists/models, claude -p, timeout
│   ├── daily.py             ← phased ticks + guards (stale-pending, GFV/PDT,
│   │                          holidays, analyst cap, health, notifications)
│   ├── schedule.py          ← launchd install (daily + caffeinate, hardened)
│   ├── briefing.py          ← deterministic operator briefing
│   └── main.py              ← CLI (see CLAUDE.md for full command list)
├── prompts/
│   ├── POLICY.md            ← versioned trading policy (strategist-maintained)
│   ├── PLAYBOOK.md          ← per-symbol evidence (strategist-maintained)
│   └── *.md                 ← role missions: scout/analyst/executor/labeler/
│                              monitor/strategist/backtester/ml-backfill
├── reports/
│   ├── BRIEFING.md          ← auto-committed daily operator briefing
│   └── research/            ← dated studies + reproducible scripts
├── tests/                   ← pytest (63 tests: gate/store/flows/ml/indicators)
├── datasets/                ← SQLite (gitignored) — the ML's training source
├── models/                  ← model.json (gitignored)
└── logs/                    ← run + launchd logs (gitignored)
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
- **2026-07-06 (morning)** — **Failure modes 6+7 defused, validated on the
  FIRST real 9:24 fire**: (6) lazy iCloud re-materialization can blow the
  fixed 60s MCP handshake → prewarm (imports + db read, duration logged) +
  gateway boot-evidence with retry-once; cold-state fire absorbed a real
  63.0s re-download. (7) **launchd opens Standard*Path in its own context,
  pre-process** — iCloud-evicted log files there fail the open → exit 78
  EX_CONFIG with empty logs (exactly what killed the real 9:24 fire; probe
  label with fresh log files ran perfectly). Fix: launchd logs moved to
  ~/Library/Logs/earnings (non-iCloud) + morning idempotency guard so
  re-fires are verify-only. Recovery tick ran clean: market-wide scout
  recorded 51 events (junk filtered, tentative dates flagged), RECONCILE OK,
  briefing committed; re-fire after the fix: exit 0.
- **2026-07-06 (0315Z)** — **ML backfill complete + first trained model — an
  honest negative result**: 84/90 historical rows reconstructed (Sonnet
  agents; zero fabrication, lookahead-leakage guards held, two API edge
  cases caught and verified rather than skipped). First model: logistic
  regression on 6 indicator features, 5-fold **CV accuracy 0.44 vs base
  rate 0.524** — technical indicators alone do NOT predict earnings-gap
  direction. The pipeline is proven end-to-end; the signal must come from
  live-row features (implied move, sentiment, beat context, playbook fit).
  get_ml_prediction/brief_status now explicitly flag a below-base-rate model
  as noise so no agent quietly leans on it. Retrains daily as live rows
  accumulate.
- **2026-07-07 (evening)** - **Repo relocated out of iCloud sync, validated
  by a defanged real fire**: local dir moved ~/Documents/GitHub/... →
  `~/code/agentic-trading` (symlink at the old path), venv rebuilt, plists
  regenerated. Because the system is armed, the mandatory kickstart was
  defanged by temporarily patching ProgramArguments to `--phase evening
  --dry-run` (procedure now in SETUP §6): real launchd fire from the new
  path ran clean ("DRY RUN ... tick complete", empty stderr), canonical
  plist reinstalled and verified. Rebuilt venv was missing the `[dev]`
  extra (no pytest); reinstalled, 63/63 pass. Claude project memory
  (keyed by absolute path) migrated to the new key. ~/code is not
  iCloud-synced, so eviction failure modes 6+7 should not recur on this
  machine; prewarm 16.1s on this fire was first-touch of the fresh venv.
  Wake chain intact (06:55 wakepoweron; caffeinate 06:57/06:58, 37000s).
  Bonus fix: the `schedule.py` install message still printed the stale
  pre-re-anchor "08:05" caffeinate summary (plist content was always
  correct); message corrected, and stale 08:05 mentions in CLAUDE.md /
  SETUP.md refreshed too.
- **2026-07-05 (late)** — **Full-scale live probes** (operator-directed):
  (1) 1 TSLA share round-tripped in the overnight session @ $396.17→$396.14
  (instant fills, 3¢ spread cost) — 24/5 whole-share execution confirmed at
  real size; buying power dropped to $96.72 (80% of the account locked to
  T+1), the settlement lesson at scale. (2) **Investor-profile second-trade
  blocker discovered and cleared**: Robinhood blocks an agentic account's
  second trade until the investor questionnaire is done — this would have
  silently killed the week's first automated entry; operator completed it
  same night. (3) Fractional $1 order accepted off-hours → queues to the
  next opening auction (never executes overnight); cancel flow verified
  clean. Total probe cost: 4¢ for the whole series; all orders tagged
  placed_agent=agentic.
- **2026-07-05 (late)** — **Live settlement behavior verified with a real $6
  round trip** (operator-directed): bought 1 LCID @ $6.11 and sold @ $6.10 in
  the overnight 24/5 session (instant fills, zero fees, 1¢ spread cost;
  orders tagged placed_agent=agentic). Result: cash returned to $499.99 but
  **buying power stayed at $493.89 — this cash account EXCLUDES unsettled
  sale proceeds from buying power until T+1**. Implications encoded: context
  pack + briefing now surface the unsettled gap (cash − buying_power);
  policy documents the 2-trading-day capital cycle; executor sizing to
  broker buying_power was already mechanically safe. Bonus finding:
  overnight-session support varies per name (LCID/F tradable, PLUG/NIO not)
  — session-awareness validated.
- **2026-07-05** — **launchd-context hardening validated by real fire** (five
  failure modes from the sibling stake-synthetics project audited):
  MaterializeDatalessFiles + ProcessType Interactive added to the plist;
  stale-pending expiry + executor double-buy guard added. The defanged smoke
  fire under REAL launchd caught what every interactive test masked: the
  resolved `claude` symlink dir contains only a version-named binary → PATH
  had no `claude` → monitor exit 127. Fixed (symlink dir); second fire was a
  full clean pass — monitor exit 0 on live OAuth, RECONCILE: OK, sklearn
  import fine, briefing committed. Rule going forward: **any schedule change
  gets a defanged launchctl kickstart validation, never just a shell test.**
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
- **2026-07-16 (evening)** — **Context pack was benching screened names -
  found via real run logs, fixed, regression-tested.** The pack's
  `upcoming_earnings` list still filtered to the core-15 universe (predates
  the v0.6.0 market-wide expansion), so screened non-core events never
  appeared. Fable-run analysts had tolerated the gap (verified events via
  market data and traded DAL/CAG/UAL anyway); on 2026-07-16 Fable was
  usage-limited, all six analysts fell back to Opus 4.8, obeyed the mission's
  step-1 "no recorded event" stop literally, and the day's slate (NFLX, ISRG,
  AA, plus 07-17 bmo entries) went entirely untraded: 0 decisions. Fix:
  pack now lists core plus screened events tagged `(core)`/`(screened)`,
  macro-watch names excluded (2 -> 144 events on the live store). Same
  session: ML training rows enriched with prior-reaction gap features
  (strict pre-event cutoff, no lookahead; CV 52% -> 54.4% on the same 136
  rows) and the capped analyst slots now rank by historical mean |gap|
  instead of raw volume (edge_rank; 07-17 slate correctly kept ACI/RF/TFC/
  FITB over FERG/ALV). 74 tests passing.
- **2026-07-16 (night)** — **Announcement-anchored exit study (operator
  hypothesis) + dynamic sizing overhaul (operator-directed, policy
  v0.8.0).** (1) Tested "sell right after the print" (AMC print+5/15/30m,
  BMO premarket 07:20/08:00) against real extended-session bars for all 52
  Apr-Jul events with detected (not clock-assumed) print bars: anchored
  exits LOSE 1.2-2.5%/event to the next-open auction on AMC (10/20 better,
  avg +1.4-2.7% vs +3.9%), are a wash ex-outlier on BMO (the +1.9% headline
  was one FALSE print detection on BYRN that dodged a -21% crash by luck),
  and are structurally unexecutable on 8/28 AMC + 10/24 BMO tapes (thin AH/
  premarket, platform opens premarket at 07:00, whole shares only). Auction
  exit stands. Real finding PARKED for the strategist: AH losers bleed
  further overnight (sell-losers-at-16:50 beat the open +0.75%/event, 7/11;
  conditional strategy +0.41%/event overall; CRDO whipsaw is the
  counterexample). See reports/research/2026-07-16-announcement-anchored-
  exit-study.md. (2) Sizing is now SERVER-COMPUTED and equity-breathing:
  engine/sizing.py + gateway compute_position_size — risk 1%..3% of CURRENT
  equity by conviction, / adverse_move_pct, haircuts non-core x0.75 and
  overnight x0.8, clamped to arm cap / half-equity / buying power / daily
  budget, $20 participation floor (fractional executes fine; wild names now
  trade small instead of passing). Tiers and the flat $40-loss rule retired;
  verified over stdio JSON-RPC against the live snapshot (DAL-type setup:
  $109.27, max-loss estimate $4.37). RiskGate caps unchanged and still rule.
  83 tests passing.
- **2026-07-16 (night, second study)** — **Exit-horizon study: the 9:30
  auction confirmed as the best statistical exit at every n.** Operator
  asked open vs 10am/11am/3pm/close/next-day. Layer 1 (n=324 backtests):
  open +0.31%/event vs same-day close -0.05%; post-open drift -0.27%,
  positive 48%; up-gaps fade -1.16%, down-gaps bounce +0.60%. Layer 2 (n=52
  Apr-Jul market-wide, 30-min bars): every intraday exit (10:00-16:00)
  costs 0.65-1.05%/event vs the auction, none beats it in >52% of events.
  Layer 3 (n=48 daily): T+1..T+3 never beat open in more than half of
  events; apparent T+2/T+3 mean edge is MRVL's 06-02 catalyst plus bull
  beta, and down-gap events get strictly worse held to T+3. No policy
  change; loser-side AH exit remains the only parked hypothesis. See
  reports/research/2026-07-16-exit-horizon-study.md.
