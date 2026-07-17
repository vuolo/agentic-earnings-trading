# Announcement-Anchored Exit Study - 2026-07-16

**Question** (operator): the prior exit studies used fixed clock times and
may not have properly examined after-hours / premarket bars. Is it better to
sell shortly AFTER the print lands - AMC ~16:20 for a 16:15 report, BMO
~07:20 for a 07:15 report - dynamically anchored to the announcement, rather
than at the next 9:30 opening auction?

**Method**: every backtests-table event 2026-04-15..2026-07-16 with recorded
pre_close/post_open (53 events denested to 28 AMC evenings + 24 BMO
premarkets). Real extended-session bars (5-min AH 16:05-17:35 ET; 10-min
premarket 06:10-09:30 ET). The print bar is DETECTED from the tape (first
bar-over-bar move > 0.8%), so exits are anchored to the actual announcement -
exactly the proposed rule, not a fixed clock. Long framing from the
pre-close entry, matching the earlier studies. Script committed alongside
with all bar data embedded.

## Headline: the anchored exit LOSES to next-open on average

AMC, n=20 liquid evenings (avg captured long return from entry):

| Exit | Avg | Better than next-open |
|---|---|---|
| print+5m | +1.41% | 10/20 |
| print+15m | +2.36% | 10/20 |
| print+30m | +2.67% | 10/20 |
| fixed 16:20 | +2.19% | 9/20 |
| fixed 16:50 | +2.99% | 10/20 |
| **next open** | **+3.90%** | - |

Anchoring to the announcement does NOT fix the early-sale problem the
2026-07-05 study found; it just relocates it. At print+15m only ~35-85% of
the eventual overnight move has printed in most names (AMD 35%, AVGO 37%,
DELL 47%, MU 54%, ORCL 28%). Winners keep running overnight: selling AMD at
print+15m gets +5.4% vs +15.3% at the open; DELL +15.1% vs +31.8%; HPE
+28.7% vs +34.2%. The overnight session completes the move - that IS the
edge - and an announcement-anchored sale forfeits the unpriced remainder.

BMO looks better at first glance (print+10m avg +1.87% vs open) but the
entire edge is ONE event: BYRN's "print" was detected off a stale premarket
odd-lot at 6:10, the anchored rule "sold" at +4.9% and the real report
cratered the stock to -21% - selling before the news on a bad detection,
i.e. luck, the exact hazard the 2026-07-05 study documented for NVDA's
16:20. Excluding BYRN: print+10m -0.13%, @07:20 -0.19% vs open (n=12) - a
wash, with premarket detection unreliable (thin 06:00-07:00 tape gives
false prints: ABT, UNH, VRT, SMPL all "detected" at 6:10 regardless of
actual report time).

## Structural infeasibility: a third of the slate cannot exit early at all

- **8 of 28 AMC** evenings had an AH tape too thin to fill even our $75-250
  exits (AZZ x2, SAR x2, EPAC, KRUS, PSMT, SLP): mostly interpolated bars
  and isolated odd-lot prints. An exit you cannot fill is not an exit.
- **10 of 24 BMO** premarkets were unexecutable before ~09:20 (FHN, PGR,
  BNY, CFG, USB, FITB, RF, TFC, HELE x2) - regional banks and small caps
  print a few hundred shares premarket. Robinhood also only opens extended
  hours to us at 07:00, whole shares only, no fractional.
- The auction exit works for every name, every time, at the exact price the
  backtests measure.

## The real finding: loser asymmetry (parked hypothesis)

On the 11 AMC events where next-open was a long loss, early AH exits DID
help: print+15m beat the open by +1.34%/event (7/11), fixed 16:50 by
+0.75%/event (7/11). Winners keep running; losers keep bleeding (ORCL -3.7%
at print+30m -> -10.7% open; AVGO -6.9% -> -14.7%; NFLX -8.2% -> -10.6%).

A conditional rule - hold AH winners to the auction, sell AH losers at
16:50 - would have averaged +4.31%/event vs +3.90% all-auction (+0.41%/event
overall) on this sample. BUT the counterexamples are fat: CRDO printed
-10.7% at 16:50 and recovered to -3.1% by the open (the whipsaw the valve
was designed around); ANET the reverse. n=11 losers, one quarter. This is a
genuine hypothesis for the strategist once more labeled outcomes exist -
NOT policy yet. The existing 16:50 disaster valve (>=10% persistent) already
truncates the extreme tail of exactly these cases.

## Actions

- **Default exit stays the next-open auction** (BMO and AMC). The operator
  hypothesis was tested properly against announcement-anchored AH/premarket
  data and costs 1.2-2.5%/event on AMC; BMO is a wash ex-outlier and
  unexecutable for 10/24 names.
- Loser-asymmetry conditional exit recorded as a parked hypothesis with
  numbers; revisit at the strategist review once labeled AMC outcomes reach
  a decent n (needs armed AMC live cycles - to date all live trades were
  BMO-window).
- No schedule or valve change from this study.

## Caveats

- Bar closes are trade prints, not spreads; real AH/premarket fills would be
  worse than bar prices, which further favors the auction exit.
- One quarter of data, mixed regime (11/20 AMC events down-gapped).
- Print detection at 0.8% bar-over-bar is crude for BMO thin tape; any
  future premarket logic needs a real persistence check.
