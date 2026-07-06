# After-Hours Exit Study — 2026-07-05

**Question** (operator): the AMC play is buy ~15:55, sell in after-hours
(~16:20) — analyze whether that's right, vs holding to the next open.

**Method**: all 13 AMC universe reactions Apr–Jun 2026. 10-minute
extended-hours bars 16:00–18:00 ET on report evenings (Robinhood historicals),
joined to stored T-1 closes (≈ our 15:55 entry) and next-morning opens.
Script committed alongside.

## Headline (avg captured long P&L from 15:55 entry, n=13)

| Exit | Avg | Better than next-open in |
|---|---|---|
| sell 16:20 | +2.81% | 5/13 |
| sell 16:30 | +4.94% | 6/13 |
| sell 17:00 | +4.27% | 6/13 |
| sell 18:00 | +3.68% | 4/13 |
| **hold → next open** | **+5.74%** | — |

## Findings

1. **The overnight completes the move; selling early truncates it.** Reports
   land anywhere 16:05–16:30+; by 16:20 AMD had priced only 9% of its
   eventual overnight move, ANET 10%, ORCL 11%, DELL 28%, ALAB 27%. DELL
   went +8.97% (16:20) → +31.84% (open); AMD +1.38% → +15.26%.
2. **Selling at 16:20 risks selling BEFORE the print entirely** (NVDA's
   report hit ~16:20; the 16:10–16:20 price was pre-reaction). A clock-timed
   AH exit is structurally unable to "properly analyze and decide."
3. Early AH sells sometimes soften losers (ANET −1.06% vs −10.12% at open) —
   but only because the bad news wasn't priced yet, which is luck, not
   information; CRDO shows the mirror image (−11.75% AH vs −3.12% open).
4. Combined with the intraday open study: the edge's full arc is
   **15:55 entry → overnight reaction → 9:31 exit**. Shorter forfeits the
   move; longer donates it back (post-open fade −2.7% by 10:00 on winners).

## Actions taken

- **Default AMC exit changed to next-open** (policy v0.4.3). Same-day AH
  exits now sit behind an operator switch (`enable-ah-exits`), off by
  default. Evening ticks (16:20/16:50) still fire and report but hold.
- This also sidesteps the extended-hours whole-share constraint and the
  cash-account GFV guard for the common case.

## Caveats

- n=13, one quarter, mostly bullish regime; AH bars show trades, not spreads
  (real AH exit fills would be worse than bar prices — which further favors
  next-open). Refresh after the August cluster.
- A future *reactive* AH exit (detect the print, wait for stabilization,
  compare to typical overnight completion) could in principle beat next-open
  on losers; parked for the strategist once more data exists.
