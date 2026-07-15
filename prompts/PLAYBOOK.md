# Per-Symbol Playbook (evidence-based; updated 2026-07-15)

Per-name signatures from 90 events (6 quarters, daily) + 15 recent events
(5-min/hourly/AH/premarket), plus labeled live outcomes as they land. These
are priors, not laws — weigh them in your snapshot and thesis; cite the
playbook line when it moves your decision.
Source: reports/research/2026-07-05-* studies; labeled decisions #2-#7.

- **TSM** (bmo, reports ~2am ET): small up-gaps (5/6, +2 to +6%), day-0 drift
  NEGATIVE 6/6, and the fade starts in premarket (Apr: only 4:30–5am beat the
  open). Best risk-adjusted long in the book, but capture ends at the open —
  exit with zero delay.
- **NVDA**: barely gaps on earnings now (|gap|<3% in 5/6) and drifts down
  day-0 6/6. Weak gap edge — demand more than usual before going long into
  its print; a documented pass is often right.
- **ORCL**: day-0 drift POSITIVE 5/6 regardless of gap direction — the one
  consistent extender. Note it in the thesis; hold-to-close variants remain
  unauthorized (policy v0.7.2) until labeled evidence spans several events.
- **MRVL**: drift followed the gap 6/6 — momentum name both directions.
- **HPE**: gap-up faded 4/4; drift NEVER followed the gap (0/6); June: +34%
  gap bled to +4.7% within 3 days. Great gaps, terrible holds — never
  daydream about riding HPE.
- **CRDO**: gap-up faded 3/3; wide whippy AH sessions (June: −14.5% at 16:10,
  −3.1% by open). Overnight completes reversals here — don't panic-read its
  early AH prints.
- **COHR**: bounce-back name: big gap-downs recovered (−15.1% gap → +16.8%
  drift Feb; May: −4.6% gap then +10% over 2 days). Tail risk both ways
  (worst gap −20%) — respect the sizing check.
- **SMCI**: last two quarters extended after up-gaps (+2.5%, +10.2% drifts;
  May: +13% gap → +27% by d+2). Momentum recently, but 25-02 faded −7.1 —
  regime-dependent.
- **AMD**: recent beats extended for days (May: +15.3% open → +28% d+2).
  Strong prints here are candidates for the strategist's future runner rules.
- **DELL**: monster gaps (+31.8%, +13.1% recently) that HELD or extended
  d+1 (+47% peak). AH price discovery is slow (only 28% priced at 16:20).
- **MU**: fades hard post-open (June: −7.8% from open in 30 min) and gave
  back for days after. Exit discipline matters most here.
- **AVGO**: post-open bounces gave way to multi-day bleeds both recent
  quarters; day-after strength is not trustworthy.
- **ALAB**: whipsaw in both directions (June: +6.5% gap, −10.3% from open by
  10:00; d+1 −9.3%). Wide error bars — smaller size, stronger evidence.
- **ANET**: losers keep losing — followed the down-gap for 3+ days (−10.1%
  open → −19.9% d+3). Bearish paper legs here have been right.
- **VRT** (bmo): gap-up faded 3/4 day-0, but last event ran +5.5% the NEXT
  day. Premarket exit ~8am beat the open in April (n=1).

Cross-cutting (all 90 events): moderate up-gaps (+2–10%) fade day-0 (−2.2 to
−2.6% avg); moderate down-gaps (5–10%) bounce slightly (+0.7%); giant gaps
(>10%) are name-specific — use the lines above, not the average.

Cross-cutting (labeled live outcomes, n=6, updated 2026-07-15):
- **An n ≤ 6 backtest gap DIRECTION is a variance estimate, not an edge.** It
  has now been wrong 6 of 6 (#2 PEP up_rate 0.67 → down; #3 LEVI mean +3.32%
  → down; #4 SMPL up_rate 0.33 → +17.06% UP; #5 DAL up_rate 0.83 → down;
  #6 ERIC mean +2.94% → −11.10%; #7 CAG up_rate 0.80 → down). Read `up_rate`
  and `mean_pct` as "how wide is this name's distribution," and source your
  DIRECTION from a concrete forward catalyst, guidance, sentiment, or a
  playbook line. Conviction is capped at 0.60 on a weak-basis lean (policy
  v0.7.2).
- **Longs are 0-for-4; cheapness / beats / momentum are NOT up-catalysts.**
  Every failed long rested on a backward-looking leg and gapped down: #2 PEP
  (cheap + target cuts) −3.93%; #3 LEVI (6 beats near 52w high) −4.17%;
  #5 DAL (6-for-6 beats + rising trend) −0.61%; #6 ERIC (de-rated + pre-print
  pop) −11.10%. 5 of 6 labeled events down-gapped — a risk-off tendency in
  this sample. The lone live win was #7 CAG, a bearish leg sourced from a
  concrete negative catalyst (imminent dividend cut, new CEO, −17.9% YoY EPS),
  which overrode its own bullish backtest (up_rate 0.80). Name the forward
  catalyst; do not default bearish (small sample, shorts are paper-only).
- **The implied move beats the historical tail as a risk estimate.** Realized
  gaps breached the 6-quarter extreme in 3 of 6 events; implied was the closer
  or safer number each time (#4 SMPL: implied 16.97% vs realized 17.06%,
  historical tail 11.23%. #2 PEP: implied 3.29% vs realized 3.93%, worst
  2.78%. #6 ERIC: realized −11.10% breached the −10.39% worst; max()+$75 floor
  still capped the loss at −$8.33). Size against `max(implied, |hist tail|)`.
- **The opening auction is the capture.** SMPL printed 15.03 in the auction
  and traded 13.47 by 09:39 ET, −10.4% in nine minutes.

## Screened candidates (backtest priors; realized outcomes noted)

Realized (labeled outcomes):

- **SMPL** (bmo 7/9) — **traded bearish paper, WRONG, gap +17.06%** (#4).
  The old "DANGER / strong pass candidate" line described VARIANCE (worst gap
  −27%, std 14%, implied 17%), not direction, and was read as a bearish edge.
  Its 0.33 up-rate on n=6 predicted nothing. Implied move called the magnitude
  to 0.1pp. Treat SMPL as a wide-tailed coin flip: floor size, both directions
  respected, and never let the −27% tail masquerade as a short thesis.
- **PEP** (bmo 7/9) — **traded long, WRONG, gap −3.93%** (#2, −$2.95). Not the
  "tight, boring" name the std 2.2% implied: the realized gap was ~1.8σ and
  breached the 6-quarter worst (−2.78%). Cheap-into-the-print (−16% off high,
  cut estimates, target cuts) did NOT produce a relief pop. Exploration size
  only, and widen your dispersion prior beyond the backtest std.
- **LEVI** (amc 7/8) — **traded long, WRONG, gap −4.17%** (#3, −$3.06).
  Beat-and-fade at the 52w high, the exact risk the thesis named. Six straight
  EPS beats and a +21.4% avg surprise still leave the gap up-rate at 0.50 —
  **beats do not produce up-gaps in LEVI**. Proximity to the 52w high raises
  the bar for good news; it is not momentum confirmation.
- **DAL** (bmo 7/10) — **traded long, WRONG (barely), gap −0.61%** (#5,
  −$0.46). The week's best paper setup (up-rate 0.83, mean +5.8%) and the
  direction still missed — the n=6 up-rate class is now 0-for-4. Two
  corroborating legs (rising trend + 6-for-6 beats) did NOT save the long;
  the 0.60 cap and $75 floor kept the miss trivial, which is the system
  working. Backward-looking beats/trend are not a forward catalyst here.
- **ERIC** (bmo 7/14) — **traded long, WRONG, gap −11.10%** (#6, −$8.33).
  A de-rated telecom (−17% off high) with a pre-print +4% pop and a 4/6 beat
  record gapped hard DOWN into flat-RAN/job-cut guidance. Cheapness + momentum
  were not a catalyst; the falling SMA50 / −6% rel-strength were the truer
  read. Realized breached both the implied (7.86%) and worst-gap (−10.39%)
  estimates — wide-tailed, floor size only, and treat a de-rating as a reason
  to demand a forward catalyst, not as one.
- **CAG** (bmo 7/15) — **traded bearish paper, RIGHT, gap −2.54%** (#7,
  +$1.91). The only live WIN. Direction came from a concrete negative catalyst
  (imminent dividend cut at a 10% yield, new CEO, −17.9% YoY EPS, distressed
  tape) and correctly OVERRODE the bullish backtest (up_rate 0.80). The
  template for a catalyst-sourced lean: exploration size, forward catalyst
  named, backtest direction ignored.

Backtest priors (no labeled trade yet):

- **WDFC** (amc): post-open drift fades 5/6 (mean −3.7%) — if held, the
  auction exit is non-negotiable here.
- **PENG** (amc): AI/HPC-adjacent but wide-tailed (worst −17.8%,
  up-rate ~0.5) — minimum size only despite the thematic fit.
- **EPAC / PSMT / AZZ**: coin-flip direction, −10 to −12% tails, modest
  liquidity — exploration size, and a named disqualifier is respectable.