# Trading Policy

Version: 0.1.0
Mode: paper only

Every decision you submit is stamped with this version. If the operator changes
anything below, the version must be bumped (see CLAUDE.md rule 4).

## Universe

AI / data-center infrastructure names only (mirrors `engine/config.py`):
NVDA, AMD, AVGO, TSM, MU, SMCI, DELL, HPE, VRT, ANET, MRVL, COHR, CRDO, ALAB, ORCL.
The risk gate rejects symbols outside this list — do not analyze others.

## Required feature snapshot (before any decision, including pass)

Assemble ALL of the following and submit it as `features_json`:

1. **implied_move_pct** — from the ATM straddle price nearest expiry after the
   report date (straddle mid ÷ underlying price × 100).
2. **historical_reactions** — last 8 quarters where available: for each prior
   report, the day-after move % (from `get_earnings_results` dates +
   `get_equity_historicals`). Include mean absolute move, beat/miss record,
   and direction consistency.
3. **trend** — 20-day price trend vs. 50-day (rising/falling/flat), distance
   from recent high/low, recent volume behavior.
4. **valuation_context** — from fundamentals: P/E, market cap; note extremes.
5. **sentiment** — qualitative from whatever the tools surface (news headlines
   in fundamentals/search results). State it plainly: bullish/bearish/mixed,
   with one-line justification.
6. **event** — report_date, timing (bmo/amc), source of that date.

Missing a component? Say so in the snapshot explicitly (`"unavailable"`), don't
invent numbers.

## Entry rules (v0.1)

- Trade only when conviction ≥ **0.65** AND you can state a specific edge:
  a divergence between the implied move and the historical reaction pattern,
  a directional consistency the market is underpricing, or a clear
  fundamentals/sentiment setup the statistics support.
- Direction: bullish → `long_equity`. Bearish → `bearish_option` (Robinhood
  has no equity shorting).
- If the edge is not specific and defensible, submit `pass` with the snapshot.
  Passes are valuable dataset rows — never skip submitting.

## Sizing (v0.1)

- Base $500; conviction ≥ 0.80 may size up to the $1,000 per-position cap.
- Never attempt to exceed the caps in the context pack — the risk gate will
  reject and the rejection is final for that submission.

## Exit discipline (v0.1)

- Paper positions are closed on the first trading day after the report
  (operator runs `close` with the T+1 price until the labeler role exists).
- Note in your thesis if you believe the position warrants holding longer —
  it informs future policy versions, but v0.1 closes T+1 regardless.
