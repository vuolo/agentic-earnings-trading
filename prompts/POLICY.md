# Trading Policy

Version: 0.4.0
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
  D; entry fills ~15:45–15:58 ET, before the close. Exit: same-day
  after-hours (16:20/16:50 ticks) when the orchestrator authorizes it —
  requires a whole-share position (extended hours rejects fractional) and no
  same-day sale-proceeds funding (cash-account GFV guard) — otherwise at the
  next morning's open. Minutes-to-hours exposure.
- **BMO events** (report before open, day D): decide on the afternoon tick of
  the prior trading day (T-1); entry fills T-1 ~15:45–15:58 ET. Exit at the
  post-report open (morning tick, ~09:31). Overnight exposure through the
  print — the riskier window; demand stronger evidence (see Entry rules).
- Never enter outside these windows; never hold past the post-report exit
  without an operator instruction.

## Universe

AI / data-center infrastructure names only (mirrors `engine/config.py`):
NVDA, AMD, AVGO, TSM, MU, SMCI, DELL, HPE, VRT, ANET, MRVL, COHR, CRDO, ALAB, ORCL.
The risk gate rejects symbols outside this list — do not analyze others.

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

Missing a component? Say so explicitly (`"unavailable"`), don't invent numbers.

## Entry rules (v0.2)

- Trade only when conviction ≥ **0.65** AND the backtest gap stats support the
  direction (up_rate ≥ 0.6 for longs in that name, or a specific documented
  divergence the stats misprice).
- **BMO (overnight) entries need more**: conviction ≥ **0.70** AND the worst
  historical gap in the name must not exceed ~2× your intended size's
  tolerable loss. State this check in the thesis.
- Direction (stocks-only strategy; options deliberately unused):
  - Bullish → `long_equity`.
  - Bearish → `short_equity` **when the context pack shows shorting ENABLED**
    (margin account, operator-verified via broker probe, whole shares only);
    otherwise → `bearish_option`, the paper-only dataset leg. Check the
    context pack's settlement line before choosing.
  - **Short entries carry the BMO-grade evidence bar always** (conviction
    ≥ 0.70), and use the backtest's BEST gap (upside tail) as the risk check
    — a short's worst case is the stock gapping UP.
- No specific, defensible edge → submit `pass` with the full snapshot and a
  reference `entry_price`. Passes are dataset rows — never skip submitting.

## Sizing (real-money, ~$150 cash account)

- Base **$100**; conviction ≥ 0.80 may size up to **$120** (the arm cap).
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
- The labeler/executor records real fills; note in the thesis if the evidence
  suggests a different exit window, so the strategist can evaluate it — but
  follow this policy until it changes.
