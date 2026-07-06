# Intraday Exit-Timing Study — 2026-07-05

**Question** (operator): after the post-earnings open, should we exit within
minutes, or hours? Where does the move actually die?

**Method**: all 15 universe earnings reactions Apr–Jun 2026. 5-minute bars
9:30–10:05 ET + hourly closes 11:00–16:00 ET (Robinhood historicals,
split-adjusted, RTH), joined to stored T-1 closes. Perspective: LONG entered
at T-1 close (our BMO/overnight-AMC carrier). Analysis script committed
alongside this file.

## Headline numbers (average captured long P&L, T-1 close → exit)

| Exit | All (n=15) | Gap-up (n=7) | Gap-down (n=8) |
|---|---|---|---|
| **open (9:31)** | **+4.72%** | **+16.94%** | −5.98% |
| 9:45 | +4.29% | +16.61% | −6.49% |
| 10:00 | +2.69% | +13.74% | −6.99% |
| 11:00 | +2.58% | +13.05% | −6.58% |
| 12:00 | +2.76% | +13.86% | −6.96% |
| 14:00 | +2.52% | +13.67% | −7.23% |
| close | +4.00% | +15.83% | −6.34% |

## Findings

1. **Exit at the open wins.** Waiting to 10:00 costs ~2% on average; the
   partial recovery into the close (+4.00%) comes with double the dispersion
   (mean |move from open| grows 2.0% → 4.1% through the day). No exit time
   beats 9:31 on average.
2. **The fade is front-loaded and violent, worst exactly when we're right.**
   Gap-up events average −2.7% from the open by 10:00. MU: +17.7% gap,
   −7.8% from open in 30 min. ALAB: +6.5% gap, −10.3% by 10:00. HPE: +34%
   gap, −7% in 15 minutes. **Minutes matter; hours lose.**
3. **No salvation in waiting on losers**: gap-downs open −5.98% and oscillate
   −6% to −7.3% all day. The first print is as good as it gets, on average.
4. **No reliable open-auction pop to time**: 9:35 averages +0.78% vs open but
   it's noise (CRDO +9.4%, HPE −1.25%); for gap-ups it's −0.01%. Sell
   immediately; don't try to catch a bounce.
5. **Research hypothesis for the strategist** (small n, not actionable
   without shorting): fading the gap-up at the open (short open → cover
   10:00) averaged +2.7% on 7 events. Revisit if/when shorting is enabled
   and n grows.

## Actions taken

- Morning tick reordered: **live exits now run FIRST** (9:31–9:33 fills),
  before monitor/scout/labeler — the prior ordering would have filled ~9:36+,
  measurably worse (finding 2).
- Executor prompt: close jobs execute before the account snapshot (sells
  don't need buying power).
- Policy v0.4.2: exit-at-open discipline confirmed by intraday evidence and
  marked time-critical; holding past the first minutes requires a future
  policy change backed by data, not judgment in the moment.

## Caveats

- n=15, one quarter, one (bullish AI-cycle) regime. Refresh after the August
  cluster — the labeler + Monday backtest refresh accumulate this data
  automatically now.
- Hourly-bar volumes from the source look unreliable in spots (near-zero
  midday bars); closes were price-continuous and cross-checked against the
  5-minute series where they overlap.
