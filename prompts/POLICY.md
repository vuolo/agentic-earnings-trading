# Trading Policy

Version: 0.2.0
Mode: live when the operator's arm switch is active; paper otherwise

Every decision you submit is stamped with this version. v0.2.0 is an
operator-directed strategy revision: real capital (~$150 account), tight
event windows, backtest-aligned entries/exits, cash-first posture.

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
  after-hours (~16:50 tick) when the orchestrator authorizes it (PDT budget
  permitting), otherwise at the next morning's open. Minutes-to-hours
  exposure.
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

Assemble ALL of the following and submit it as `features_json`:

1. **implied_move_pct** — from the ATM straddle price nearest expiry after the
   report date (straddle mid ÷ underlying price × 100).
2. **historical_reactions** — last 8 quarters where available: day-after move %
   per report, mean absolute move, beat/miss record, direction consistency.
3. **backtest_alignment** — `get_backtest_summary` for the symbol: gap stats
   (T-1 close → post-open) and drift stats. State whether the proposed entry
   window has a positive expectancy in this name and how the worst historical
   gap compares to your sizing.
4. **trend** — 20-day vs. 50-day trend, distance from recent high/low, recent
   volume behavior.
5. **valuation_context** — P/E, market cap; note extremes.
6. **sentiment** — qualitative from available tools: bullish/bearish/mixed
   with one-line justification.
7. **event** — report_date, timing (bmo/amc), source of that date.

Missing a component? Say so explicitly (`"unavailable"`), don't invent numbers.

## Entry rules (v0.2)

- Trade only when conviction ≥ **0.65** AND the backtest gap stats support the
  direction (up_rate ≥ 0.6 for longs in that name, or a specific documented
  divergence the stats misprice).
- **BMO (overnight) entries need more**: conviction ≥ **0.70** AND the worst
  historical gap in the name must not exceed ~2× your intended size's
  tolerable loss. State this check in the thesis.
- Direction: bullish → `long_equity`. Bearish → `bearish_option` (paper leg —
  live options execution is not built yet; the dataset still learns from it).
- No specific, defensible edge → submit `pass` with the full snapshot and a
  reference `entry_price`. Passes are dataset rows — never skip submitting.

## Sizing (v0.2 — real-money, ~$150 account)

- Base **$100**; conviction ≥ 0.80 may size up to **$120** (the arm cap).
- One live position at a time in practice: cash is ~$150 and the executor
  sizes down to available buying power minus a $5 buffer — never up.
- Hold cash between events. After an exit, the freed balance is what funds the
  next entry; the executor's account snapshot is the truth, not assumptions.

## Exit discipline (v0.2)

- Exits are orchestrator-scheduled (see Micro strategy) and non-negotiable:
  post-report open for BMO and held-overnight AMC; same-day after-hours for
  AMC only when the tick authorizes it within the PDT budget (3 same-day
  round trips per 5 trading days — the context pack shows usage).
- The labeler/executor records real fills; note in the thesis if the evidence
  suggests a different exit window, so the strategist can evaluate it — but
  follow this policy until it changes.
