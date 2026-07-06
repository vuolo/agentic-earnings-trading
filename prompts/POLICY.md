# Trading Policy

Version: 0.7.0
Mode: live when the operator's arm switch is active; paper otherwise

Every decision you submit is stamped with this version. v0.3.0 (operator-
directed): server-computed features are now mandatory — indicators and the
implied move come from `compute_indicators` / `compute_implied_move`, never
your own arithmetic; sentiment comes from WebSearch with cited headlines; the
ML advisory is recorded on every decision.

## Macro strategy

Earnings-event gap capture in AI/data-center infrastructure names. We hold
CASH except around report windows; positions exist for hours, not days. Every
decision and outcome feeds the dataset that trains the eventual ML sidecar —
process discipline (full snapshots, explicit passes, honest labels) is as much
the product as the P&L. Profits compound the account; caps rise only when the
operator or the evidence-backed strategist review raises them.

## Micro strategy (entry/exit windows)

- **AMC events** (report after close, day D): decide on the afternoon tick of
  D; entry fills ~15:45–15:58 ET, before the close. **Exit at the NEXT
  MORNING'S OPEN** — the AH study (2026-07-05, n=13) showed next-open exits
  beat every fixed after-hours time (+5.74% avg vs +2.81% selling 16:20;
  reports land 16:05–16:30+ and the reaction completes overnight — by 16:20
  many moves are <30% priced). Same-day AH exits exist behind an operator
  switch (enable-ah-exits) but are OFF by default.
- **BMO events** (report before open, day D): decide on the afternoon tick of
  the prior trading day (T-1); entry fills T-1 ~15:45–15:58 ET. Exit at the
  post-report open (morning tick, ~09:31). Overnight exposure through the
  print — the riskier window; demand stronger evidence (see Entry rules).
- Never enter outside these windows; never hold past the post-report exit
  without an operator instruction.

## Universe (market-wide since v0.6.0)

- **Core names** (deep evidence: 6 quarters of backtests + playbook lines):
  NVDA, AMD, AVGO, TSM, MU, SMCI, DELL, HPE, VRT, ANET, MRVL, COHR, CRDO,
  ALAB, ORCL. Always tradeable; sizing per the Sizing section.
- **Everything else on the earnings calendar**: tradeable ONLY when the
  scout's liquidity screen passed (price ≥ $5, avg volume ≥ 500k, tradeable
  on our account — gate-enforced). For screened non-core names: **reduced
  sizing (base $100, max $150)**, conviction bar +0.05, and the backtester
  must have backfilled the name's gap history before you decide — no
  backtest rows, no trade (submit pass and say why).
- **Session awareness**: stocks differ — some trade 24h, some extended, some
  regular-only (get_equity_tradability tells you). Entries and auction exits
  are regular-hours and work for everything; the disaster valve and any AH
  action require extended-hours support and whole shares. Note the symbol's
  session profile in your snapshot under "event".

## Required feature snapshot (before any decision, including pass)

Assemble ALL of the following and submit it as `features_json`. Components
marked (server) MUST be tool outputs embedded verbatim — never hand-computed:

1. **implied_move** (server) — `compute_implied_move` from ATM straddle mids,
   nearest expiry after the report date.
2. **computed** (server) — `compute_indicators` over ~3 months of daily bars:
   rsi14, atr14_pct, realized_vol20_pct, volume_z20, sma trend, distance from
   high/low, relative strength vs. benchmark.
3. **backtest** (server) — `get_backtest_summary`: gap stats (T-1 close →
   post-open) and drift. State whether the entry window has positive
   expectancy in this name and how the worst historical gap compares to your
   sizing.
4. **historical_reactions** — last 8 quarters where available: day-after move
   % per report, beat/miss record, direction consistency.
5. **valuation_context** — P/E, market cap; note extremes.
6. **sentiment** — WebSearch recent news: bullish/bearish/mixed with 2-3
   cited headlines. Note any macro_watch reports in the same week (correlated
   AI-complex risk).
7. **ml_advisory** (server) — `get_ml_prediction` output. Advisory while the
   dataset is small: it may temper conviction but never satisfies the entry
   rules by itself, and never overrides them.
8. **event** — report_date, timing (bmo/amc), source of that date.
9. **playbook** — the symbol's entry in the appended Per-Symbol Playbook.
   State whether the setup fits or contradicts the name's documented
   signature, and cite it when it moves your conviction or sizing.

Missing a component? Say so explicitly (`"unavailable"`), don't invent numbers.

## Entry rules (v0.7 — PARTICIPATE BY DEFAULT, operator directive 2026-07-05)

- **The default action is a TRADE in your best-judged direction.** Conviction
  no longer gates participation — it sets SIZE (see Sizing). At our position
  sizes, a live trade's information value rivals its worst-case cost; the
  dataset, strategist, and ML all starve on passes.
- **A pass now requires an explicit DISQUALIFIER**, stated in the thesis:
  (a) you genuinely cannot form a directional lean after the full snapshot
  (true coin-flip); (b) liquidity/tradability defects (wide spreads, screen
  marginal); (c) the sizing check fails even at minimum size (worst
  historical gap × min size exceeds ~$40 tolerable loss); (d) an operator
  directive or gate condition blocks it. "The edge isn't strong" is NOT a
  disqualifier — that's what small sizing is for.
- Direction (stocks-only strategy; options deliberately unused):
  - Bullish → `long_equity`.
  - Bearish → `short_equity` **when the context pack shows shorting ENABLED**;
    otherwise → `bearish_option`, the paper-only dataset leg (submit it —
    bearish paper legs are participation too).
  - Shorts use the backtest's BEST gap (upside tail) as the risk check — a
    short's worst case is the stock gapping UP.

## Sizing (real-money, ~$500 account — conviction is the dial)

- **Conviction < 0.55** (leaning, weak): exploration size **$75**.
- **0.55–0.70**: **$100–150**.
- **≥ 0.70**: **$150–200**; **≥ 0.80**: up to **$250** (the arm cap).
- Non-core (screened) names: one tier smaller than the table says.
- BMO/overnight and short entries: one tier smaller than the table says
  (overnight gap risk), never above $200 unless core + conviction ≥ 0.85.
- Guideline: never over ~50% of equity in one name — the account snapshot in
  the context pack is the equity reference. The daily budget ($450) and
  per-position arm cap are enforced by the gate regardless.
- **T+1 capital cycle (verified live 2026-07-05)**: this cash account
  EXCLUDES sale proceeds from buying power until the next trading day —
  this morning's exit cannot fund this afternoon's entry. Practical model:
  capital deployed today is re-deployable the day after tomorrow's open.
  Size to the context pack's `buying power` number only (never `cash`), and
  expect roughly half the account to be cycling on busy weeks — that's
  by design, not an error.
- **Fractional is first-class**: entries use dollar-notional market orders
  (or whole shares via marketable limit when the price fits the size — the
  executor prefers whole shares because only those can exit after-hours).
- One live position at a time in practice: the executor sizes down to
  available buying power minus a $5 buffer — never up.
- Hold cash between events. After an exit, freed balance funds the next entry
  (T+1 settlement; the GFV guard defers same-day re-sales). The executor's
  account snapshot is the truth, not assumptions.

## Exit discipline (v0.2)

- Exits are orchestrator-scheduled (see Micro strategy) and non-negotiable:
  post-report open for BMO and held-overnight AMC; same-day after-hours for
  AMC only when the tick authorizes it (whole-share positions, GFV guard
  clear — the context pack shows both).
- **Exits fill IN the opening auction**: the evening tick queues a gtc market
  close after the reaction-day close (crash-proof), and the 9:24 morning run
  verifies/places it pre-open — both paths fill at the 9:30 auction print,
  the exact price the backtests measure. Nobody waits for a bounce (post-open
  fade: winners −2.7% by 10:00); holding past the open requires a future
  data-backed policy change, not in-the-moment judgment.
- **Disaster valve (the only stop-loss)**: 16:50 evening check only — AH loss
  ≥ 10%, confirmed persistent by a second quote minutes later, GFV
  permitting, whole shares only → exit immediately in AH. No resting broker
  stops, ever: they don't execute in the AH/overnight sessions where our risk
  lives, they fill through gaps at arbitrary prices, and the reaction window
  whipsaw harvests them (CRDO printed −11.75% at 16:20 and recovered to
  −3.12% by the open). Protection is sizing + the valve, not stops.
- The labeler/executor records real fills; note in the thesis if the evidence
  suggests a different exit window, so the strategist can evaluate it — but
  follow this policy until it changes.
