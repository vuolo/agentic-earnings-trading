# Exit-Horizon Study - 2026-07-16 (evening)

**Question** (operator): what is the best statistical exit - market open,
10am, 11am, 3pm, the close, next day, later?

**Method**: three layers, biggest n first. (1) The full backtests table,
n=324 events across 6 quarters, market-wide: open-auction capture vs the
same-day close, straight from the store. (2) Reaction-day 30-minute RTH
bars for all 52 usable Apr-Jul 2026 events (market-wide, the same sample as
the announcement-anchored study): exits at 10:00 / 11:00 / 12:00 / 14:00 /
15:00 / 16:00 ET. (3) Daily bars for T+1 open, T+1/T+2/T+3 closes (n=48;
events since 07-15 not yet labeled). Long framing from the ~15:55 pre-close
entry, as in every prior study. Script + all bar data committed alongside.

## Answer: the 9:30 opening auction. Everything else is worse or noise.

Layer 1 (n=324, the heavyweight): exit@open captures +0.31%/event; holding
to the same-day close captures -0.05%. The post-open drift is -0.27%/event
and positive only 157/324 (48%). Asymmetry: after UP gaps the drift is
-1.16% (positive only 45%) - winners fade hard; after DOWN gaps +0.60%
(positive 52%) - losers bounce a hair, not enough to matter.

Layer 2 (n=52, Apr-Jul, market-wide, mean % captured from entry):

| exit | mean | beats open |
|---|---|---|
| **9:30 auction** | **+1.55%** | - |
| 10:00 | +0.85% | 23/52 |
| 11:00 | +0.58% | 19/52 |
| 12:00 | +0.61% | 23/52 |
| 14:00 | +0.51% | 24/52 |
| 15:00 | +0.55% | 24/52 |
| 16:00 close | +0.90% | 27/52 |

Every intraday checkpoint costs 0.65-1.05%/event vs the auction, and none
beats it in even 55% of events. 10am is the least-bad (the "morning fade"
bottoms out around 14:00), but it is still -0.70%/event. This replicates
the 2026-07-05 intraday study (n=15, core names) at 3.5x the sample,
market-wide: **the fade after the open is real and general.**

Multi-day (n=48): T+1 open +1.33%, T+1 close +0.93%, T+2 close +1.66%,
T+3 +1.63% vs open's +1.55%. The T+2/T+3 "wins" are one event - MRVL's
standalone 06-02 catalyst (+46pts by T+3) - plus bull-tape beta; the
beats-open rate never exceeds 24/48 (a coin flip), and for DOWN-gap events
holding out to T+3 makes things strictly worse (-5.07% -> -5.95%, better
in only 11/24). Multi-day holding adds variance and market beta, not event
edge - and it would also lock capital through T+1 settlement, costing us
the NEXT event's entry (opportunity cost not even counted here).

## Why the auction specifically (mechanics recap)

The overnight session completes the earnings move (07-05 AH study; 07-16
announcement-anchored study); the 9:30 auction is the single deepest
liquidity event of the day, fills whole and fractional shares alike at one
print, and is the exact price the backtests measure (`post_open`) - so our
live results stay comparable to our research. SMPL 07-09 remains the
canonical example: 15.03 at the auction, 13.47 nine minutes later.

## Actions

- **No change: queued gtc-at-open exits remain the policy.** This is now
  confirmed at n=324 (open vs close), n=52 (open vs 6 intraday times,
  market-wide), n=48 (open vs T+1..T+3), n=20 (open vs announcement-
  anchored AH), n=13-15 (prior studies).
- The only exit hypothesis with any life in it stays the LOSER-side early
  AH exit (see 2026-07-16-announcement-anchored-exit-study.md), parked for
  the strategist.

## Caveats

Apr-Jul 2026 is one regime (choppy AI-cycle tape; 28 of 52 events
down-gapped). T+n horizons carry market beta. MRVL T+2/T+3 contaminated by
its 06-02 catalyst (medians reported in the script output for that reason).
Refresh after the August cluster - the labeler keeps feeding backtests, so
layer 1 re-runs for free.
