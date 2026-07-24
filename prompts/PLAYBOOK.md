# Per-Symbol Playbook (evidence-based; updated 2026-07-24)

Per-name signatures from 90 events (6 quarters, daily) + 15 recent events
(5-min/hourly/AH/premarket), plus labeled live outcomes as they land. These
are priors, not laws — weigh them in your snapshot and thesis; cite the
playbook line when it moves your decision.
Source: reports/research/2026-07-05-* studies; labeled decisions #1-#37.

- **TSM** (bmo, reports ~2am ET): small up-gaps (5/6, +2 to +6%), day-0 drift
  NEGATIVE 6/6, and the fade starts in premarket (Apr: only 4:30–5am beat the
  open). Best risk-adjusted long in the book, but capture ends at the open —
  exit with zero delay. 7/16 live counterfactual (#1 pass): gapped DOWN
  −1.67% after a 6/6-beat record, and the implied 9.58% was 5.7x the realized
  move — the pass beat a long; the up-gap prior is not automatic.
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

Cross-cutting (labeled live outcomes, n=24 events, updated 2026-07-24):
- **The AUCTION PRINT is the label of record, and our labels have not been
  measuring it (policy v0.8.4).** The labeler takes a fresh quote at
  ~09:33-09:36 ET; the strategy exits in the 09:30 auction. Every recent leg
  whose note records both prices moved the same way, because the post-open
  fade flatters short legs: #33 NEE opened 90.655 vs a 90.145 entry (+0.57%,
  a LOSS) and was labeled −1.64% (+$1.65); #28 KMI opened 33.00 (+1.77%) and
  was labeled +0.60%; #29 ELS opened 65.52 (+0.11%) and was labeled −0.27%;
  #30 AAL opened 14.00 (−4.99%) and was labeled −6.85%. Labeled P&L across
  the four is +$5.12 versus about +$0.37 at the auction. Cite the auction
  figure when the note has it, and treat pre-0.8.4 bearish P&L as generous.
- **An n ≤ 6 backtest gap DIRECTION is a variance estimate, not an edge.** It
  was wrong in 6 of the first 6 labeled events (#2 PEP up_rate 0.67 → down;
  #3 LEVI mean +3.32% → down; #4 SMPL up_rate 0.33 → +17.06% UP; #5 DAL
  up_rate 0.83 → down; #6 ERIC mean +2.94% → −11.10%; #7 CAG up_rate 0.80 →
  down), and later batches kept overriding it profitably (#13 RYAAY
  up_rate 0.83 → −5.37%; #20 SCHW up_rate 0.83 → −1.10% counterfactual;
  #25 ONB up-biased 5/6 → −1.03%). Read `up_rate` and `mean_pct` as "how
  wide is this name's distribution," and source your DIRECTION from a
  concrete forward catalyst, guidance, sentiment, or a playbook line.
  Conviction is capped at 0.60 on a weak-basis lean (policy v0.7.2).
- **The high-bar asymmetry lean (template ii) has an edge ONLY within ~4% of
  the 52-week HIGH (policy v0.8.3).** Near the high it is 5-for-5: #18 KEY
  (1.8% off, −1.64%, +$0.68), #11 DX (post-run premium to stale book,
  −1.20%, +$0.58), #23 NLY (3% off at 1.14x book, −1.21%, +$1.44), #25 ONB
  (4.2% off after +14.5%, −1.03%, +$0.28), #20 SCHW (1.5% off, counterfactual
  −1.10%). Away from the high it has NO edge, and on an AUCTION basis it is
  0-for-4 with one flat (policy v0.8.4): #22 T +4.27% and #24 EQT +2.04% at
  the lows; #28 KMI +1.77% at the auction (6.8% off the high); #33 NEE
  +0.57% at the auction (8.65% off); #29 ELS +0.11% at the auction (5.2%
  off), a flat its label scored as a win. A bearish lean off template (ii)
  at >~4% off the high is the mirror of the failed cheapness longs —
  "already fallen" is not a down-catalyst; off-high demand template (i) or
  cap conviction at 0.50 and take FLOOR size (mandatory since v0.8.4).
- **Template (i) — concrete negative forward catalyst — is 3-for-3 and
  LOCATION-INDEPENDENT (policy v0.8.3).** #7 CAG (dividend cut, −2.54%,
  +$1.91), #8 UAL (fuel above cost assumption, −3.07%, +$2.30), #30 AAL (the
  same June fuel shock above the guidance curve, −6.85% labeled / −4.99% at
  the auction print, biggest bearish win); #13 RYAAY (−22% YoY EPS guide,
  −5.37%, +$1.93) is a fourth. AAL won at MID-RANGE location (21.5% off the
  high) because momentum was BREAKING DOWN into the print (−19% in 3 weeks)
  — the discriminator vs the T/EQT losers is momentum DIRECTION, not
  distance-from-high. A concrete forward catalyst into a down-sliding tape
  overrides the near-high requirement; a catalyst-less bearish lean into UP
  momentum off a low is the failure mode. The LONG mirror is real too: a
  live catalyst pushing the tape UP is a reason to participate small on the
  long side rather than pass (#35 SLB, +6.14% missed).
- **Bearish paper legs (template era, post-SMPL) are 10-1-3 net +$9.54 AS
  LABELED, but at minimum 9-1-4 and ~$4.75 lower at the auction print.**
  The UP prints keep piling up (#22 T +4.27%, #24 EQT +2.04%, #28 KMI
  +1.77% at the auction, #33 NEE +0.57% at the auction, #35 SLB +6.14%,
  #21 WBS +1.0% counterfactual). Do NOT default bearish: every bearish loss
  (T, EQT, KMI, NEE) leaned off-template — wrong location, no forward
  catalyst. Template discipline (location + catalyst + momentum direction),
  not a down-tape prior, separates winners from losers.
- **Longs are 0-for-4; cheapness / beats / momentum are NOT catalysts in
  EITHER direction.** Every failed long rested on a backward-looking leg
  and gapped down: #2 PEP (cheap + target cuts) −3.93%; #3 LEVI (6 beats
  near 52w high) −4.17%; #5 DAL (6-for-6 beats + rising trend) −0.61%;
  #6 ERIC (de-rated + pre-print pop) −11.10%. The bearish mirrors (#22 T,
  #24 EQT, #28 KMI, #33 NEE) leaned on de-rated/mid-range beatable-bar
  sentiment and did not gap down. Name the forward catalyst. (#32 VZ,
  #36 NEM, #37 EW entered 7/23 are the first new longs since; unlabeled at
  this review.)
- **The sizing tool prices RISK, not EDGE — off-template leans take the
  floor (policy v0.8.4).** A small adverse move buys a big notional even at
  low conviction: #33 NEE called itself "mid-range NO-EDGE" at conviction
  0.45 and still deployed $100.82 (adverse 2.89%), the largest leg of its
  batch, and #28 KMI $102.60 the same way. Both were wrong at the auction.
  When neither template applies, submit $20-40 with the reason stated and
  keep the T+1 buying power for template setups.
- **The ML sidecar's confident down-band (prob_up < 0.35) is 8-for-12, and
  depth adds no calibration.** Right: #11 DX 0.267, #13 RYAAY 0.244,
  #17 AGNC 0.264, #18 KEY 0.315, #20 SCHW 0.277, #23 NLY 0.175, #25 ONB
  0.213, #29 ELS 0.287. Wrong: #22 T 0.229, #24 EQT 0.199, #21 WBS 0.215
  (counterfactual), #28 KMI 0.289. Its two deepest reads ever (0.175, 0.199)
  split, and #28/#29 (both ~0.288) split — no per-read calibration. Reads
  BETWEEN 0.35 and 0.50 are not corroboration at all: #33 NEE cited 0.425 as
  "above base rate" for a bearish leg and printed UP at the auction; #34
  INTC 0.551 and #35 SLB 0.463 were correctly read as neutral.
  Corroboration only, never a catalyst substitute (policy v0.8.4).
- **The implied move is the safer SIZING number, but it is a DISPERSION
  estimate, not a forecast or a worst case.** Realized breached the
  historical tail in 5 events; implied was closer in 4 of them (#4 SMPL
  16.97% implied vs 17.06%; #6 ERIC −11.10% vs worst −10.39%; #22 T +4.27%
  vs best +3.43%, covered by the 2-DTE implied 5.19%) and was BREACHED
  ITSELF in the 5th (#35 SLB 1-DTE 3.01% vs +6.14% realized, with the
  +2.58% best gap breached too — max() was not conservative). Short-DTE
  weeklies are the best available read (#22 T 5.19 vs 4.27; #24 EQT 4.2 vs
  2.04; #23 NLY 2.45 vs 1.21; #30 AAL 1-DTE 6.31 vs 6.85) but not a
  ceiling; distant monthlies run hot (#13 RYAAY 10.16% on 35-DTE vs 5.37%;
  #18 KEY 6.98% vs 1.64%; #25 ONB 10.8% on 30-DTE vs 1.03%; #29 ELS 6.12%
  on 30-DTE vs 1.58% mean), and high-vol liquid chains can be absurd
  (#34 INTC 12.36% vs 0.58% realized, ~20x). Size against
  `max(implied, |tail|)`; report straddle DTE/strike quality.
- **The opening auction is the capture, and paper legs must exit there
  too.** SMPL printed 15.03 in the auction and traded 13.47 by 09:39 ET,
  −10.4% in nine minutes. #11 DX and #13 RYAAY were closed a day late,
  contaminating labels and bouncing #19 HAL / forcing #20 SCHW to pass.
  The v0.8.1 fix is VERIFIED across three batches: the 7/21 legs (#22-#25),
  the 7/22-7/23 legs (#28-#30) and #33 NEE all closed on time at their
  windows — no slot contamination since.
- **Slots are scarce on crowded calendars; spend them on edge.** #31 NOK was
  a forced pass with 5/5 slots legitimately full of same-day entries (ACI,
  PNFP, KMI, ELS, AAL) — NOT the stale-leg contamination that cost #19/#20.
  On a full slate, prioritize template-(i) catalysts and near-high
  template-(ii) over mid-range asymmetry leans, which are noise (KMI, ELS,
  NEE).
- **Verify the report date.** #12 WBS and #15 FERG were decided against
  mis-dated calendar rows; FERG had no event at all (next report 8/10) —
  a wasted decision slot. State the date source and a second-source check
  in the event component (policy v0.8.2).

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
  +$1.91). The first live WIN. Direction came from a concrete negative
  catalyst (imminent dividend cut at a 10% yield, new CEO, −17.9% YoY EPS,
  distressed tape) and correctly OVERRODE the bullish backtest (up_rate
  0.80). The template for a catalyst-sourced lean: exploration size, forward
  catalyst named, backtest direction ignored.
- **UAL** (amc 7/15) — **traded bearish paper, RIGHT, gap −3.07%** (#8,
  +$2.30). Jet fuel surging above management's ~$3.30-3.40/gal assumption
  was the concrete forward catalyst; it overrode the bullish up_rate 0.67
  and the cheap 10.7x P/E pullback (deliberately NOT used as legs). Second
  confirmation of the CAG template, and DAL's 7/10 down-gap was a valid
  same-sector tell. Same fuel-shock catalyst won AAL #30 eight days later.
- **DX** (bmo 7/20) — **traded bearish paper, RIGHT, −1.20%** (#11, +$0.58).
  High-bar setup: consensus EPS $0.50 above EVERY actual of the last 6
  quarters (missed 5 of 6) plus a premium to stale book after a sector-beta
  run-up. LABEL CAVEAT: closed a day late (7/21 vs the 7/20 window), so the
  labeled move includes a day of extra drift. mREITs gap small — the DX/AGNC
  pair confirmed the complex's event edge is structurally modest.
- **RYAAY** (bmo 7/20) — **traded bearish paper, RIGHT, −5.37%** (#13,
  +$1.93). Concrete catalyst stack: guided −22% YoY
  EPS, FY consensus down ~24% in 90 days, T-1 −5.8% break on the worst tape
  in the airline group, insider sale. Overrode up_rate 0.83. LABEL CAVEAT:
  closed a day late (7/21). Chain quality is poor (35-DTE monthly, $5
  strikes): implied 10.16% ran ~2x realized — treat its implied as an upper
  bound.
- **AGNC** (amc 7/20) — **traded bearish paper, ~flat −0.08%** (#17, +$0.08).
  Monthly BV disclosure keeps gaps tiny (mean abs 0.83%, worst −0.92%
  realized again): the event edge here is structurally small in EITHER
  direction. Floor size or a documented coin-flip pass are both respectable;
  don't spend a position slot on it when the calendar is crowded.
- **KEY** (bmo 7/21) — **traded bearish paper, RIGHT, −1.64%** (#18, +$0.68).
  The clean asymmetry-lean template with NO concrete catalyst: +20% YoY
  consensus bar 1.8% off the high, precedent of good news paying poorly
  (Q1's 33% beat closed +0.6%), ML 0.315 — conviction correctly held at 0.50
  under the weak-basis cap. Validated as a direction source at ≤ 0.55
  (policy v0.8.1); location requirement added v0.8.2 (near the high only).
- **SCHW** (bmo 7/21) — **forced pass (#20, slots full), counterfactual
  −1.10%**: the stated bearish asymmetry lean (telegraphed strong quarter
  fully priced at −1.5% off the 52w high, ML 0.277) would have won ~1%. The
  pass was correct procedure (disqualifier d) but the cost was real — slot
  hygiene (stale paper legs) is what consumed the capacity.
- **T** (bmo 7/22) — **traded bearish paper, WRONG, gap +4.27%** (#22,
  −$3.00, first bearish loss). Labeled template ii but the location was
  wrong: T was a +12% three-week bounce off its 7/2 52-week LOW, not
  extended at a high, and the "overhang" stack (Starlink threat, downgrade,
  CFO exit) was sentiment, not a forward catalyst. Realized +4.27% breached
  the best historical gap +3.43% (4th tail breach); the 2-DTE weekly
  implied 5.19% covered it. Post-open drift is up 6/6 in T — the auction
  exit remains the right capture even when wrong.
- **EQT** (amc 7/21) — **traded bearish paper, WRONG, gap +2.04%** (#24,
  −$1.77). Bearish into a name 0.4% off its 52-week low with a 6-of-6 beat
  record — the thesis itself named the relief-pop risk and it happened.
  The gas-price/EBITDA-model lean was analyst-consensus texture, not a
  CAG-grade catalyst. Confirms: de-rated names at the lows need template
  (i) or a 0.50 cap on any bearish lean (policy v0.8.2). Clean 3-DTE
  weekly implied 4.2% vs 2.04% realized.
- **NLY** (amc 7/21) — **traded bearish paper, RIGHT, −1.21%** (#23,
  +$1.44). Textbook template ii at the right location: 3% off the 52w high
  at 1.14x stale book, $0.75 dividend covered by only $0.76 EAD, ML 0.175
  (its most confident read yet). mREIT gaps stay small but NLY's was 
  large enough to pay above floor size; conviction correctly held at 0.50.
- **ONB** (bmo 7/22) — **traded bearish paper, RIGHT, −1.03%** (#25,
  +$0.28). Template ii: +19% YoY bar with slowing revenue, 4.2% off the
  high after +14.5%, prior beat paid only +0.4%, ML 0.213 — and it
  correctly overrode ONB's up-biased gap history (5/6 up, mean +1.39%).
  Chain junk (30-DTE monthly, zero-OI put): implied 10.8% vs 1.03%
  realized, treat as upper bound only.
- **KMI** (7/23 open exit) — **traded bearish paper, WRONG; auction print
  +1.77%, labeled +0.60%** (#28, −$0.62 labeled, ~−$1.82 at the auction).
  Mid-range template-ii asymmetry lean with NO catalyst: 6.8% off the high
  (26.8% above the low, NOT the T/EQT at-the-low failure), modest +10.7% YoY
  bar after a big Q1 beat that faded, ML 0.289. It opened 33.00 against a
  32.425 entry and faded back to ~32.49 by 09:33 — the mid-range no-edge
  zone, and a first example of the label crediting fade (policy v0.8.4).
  Clean 2-DTE weekly implied 2.84%. Lesson: at 5-7% off the high the
  asymmetry lean is a coin flip — FLOOR size (it took $102.60) or pass.
- **ELS** (amc 7/22, 7/23 exit) — **traded bearish paper, FLAT; auction
  print +0.11%, labeled −0.27%** (#29, +$0.13 labeled, ~−$0.05 at the
  auction). Template-ii asymmetry at 5.2% off the high — just OUTSIDE the
  ~4% band — with 4 straight 23-29% beats that gapped down 5/6, reaffirmed
  guidance, 33.7x PE, ML 0.287. It opened 65.52 against a 65.45 entry: the
  "barely right" label was post-open drift, not capture. Coarse 30-DTE
  monthly implied 6.12% vs ~1.6% realized. Location must be inside ~4%, not
  merely "elevated."
- **AAL** (bmo 7/23) — **traded bearish paper, RIGHT; auction print −4.99%,
  labeled −6.85%** (#30, +$3.96 labeled, ~+$2.88 at the auction; still the
  biggest bearish win). Template-(i) concrete forward catalyst: the June
  Middle East jet-fuel shock (~+70%, IATA cut sector profit forecasts) sits
  above the fuel curve behind AAL's April guidance, and FY consensus ($0.49)
  had been revised UP into the print — the SAME catalyst that won UAL #8, with
  DAL/UAL prints 2-for-2 down. Location was MID-RANGE (21.5% off the high) but
  momentum was BREAKING DOWN (−19% in 3 weeks, −3.5% on the day): template (i)
  is location-independent when the catalyst is concrete and the tape slides
  down. Conviction held at 0.55 (shock 3 weeks old, low bar, relief-pop risk,
  ML 0.452 outside the down-band). Fine 1-DTE weekly implied 6.31% vs 6.85%
  labeled / 4.99% at the auction.
- **NEE** (bmo 7/24) — **traded bearish paper, WRONG at the auction; open
  90.655 = +0.57% vs a 90.145 entry, labeled −1.64%** (#33, +$1.65 labeled,
  ~−$0.64 at the auction). A self-declared no-edge leg: 8.65% off the
  3-month high (mid-range), NO concrete catalyst (the Dominion regulatory
  overhang is sentiment, the T failure mode), conviction 0.45, and the only
  corroboration was ML 0.425 — outside the <0.35 down-band and therefore
  not corroboration at all. It gapped UP and only a four-minute post-open
  fade (to 88.67 by 09:34) rescued the label. Two lessons, both now policy
  (v0.8.4): the auction print is the label, and an off-template lean takes
  FLOOR size — this one sized $100.82 off a 2.89% adverse move, the largest
  leg of its batch. Utility prints are small (gap mean abs 1.47%, worst
  −1.63%, best +2.89%); clean 1-DTE weekly implied 2.73%.
- **INTC** (amc 7/23) — **pass on disqualifiers (c)+(a), RIGHT, +0.58%**
  (#34). A 121% EPS beat (0.42 vs 0.19) paid ~0.6%: neither the "priced for
  perfection" short nor the 18A-narrative long would have earned anything.
  Sizing clamped to $12.62 against a 23.09% adverse move (best gap +23.09%,
  implied 12.36%) — under the $20 floor, so the pass was mechanical, not
  judgment. Location 27% off the high kills template (ii); the news flow was
  constructive, so no template (i). Implied 12.36% vs 0.58% realized on a
  LIQUID chain is ~20x: high realized vol (75.9%) inflates the straddle far
  beyond the event. Wide-tailed lottery — floor size or the (c) pass.
- **SLB** (bmo 7/24) — **passed as a coin flip, MIXED, gapped +6.14%** (#35;
  open 50.07 = +6.03%). RIGHT on what it refused: the marginal statistical
  lean was down (ML 0.463, up_rate 0.33, falling trend) and a bearish leg
  into a name bouncing +5.7% off its low would have been our worst paper
  loss to date — the third time the v0.8.3 off-high/up-momentum rule saved
  money. WRONG on what it missed: the thesis NAMED a live concrete forward
  catalyst (the oil surge, Brent >$100, 5th straight up session) and passed
  because it was double-edged for SLB (crude helps, ME disruption hurts its
  Iraq recovery) and expected to fade. That is now disqualifier (a)'s
  boundary (policy v0.8.4): a named catalyst with an ambiguous sign is not a
  coin flip — take a floor-size leg in the catalyst's primary direction.
  Also the 5th tail breach and the first where BOTH estimates failed: a fine
  1-DTE weekly implied 3.01% and a +2.58% best historical gap against a
  +6.14% move.
- **WBS** (amc 7/21) — **passed twice, RIGHT, +1.0%** (#12, #21). Merger
  math pins the price ($48.75 cash + 2.0548 SAN ADS, ~0.9% arb discount,
  no earnings call): the print cannot move consideration, so the event is
  structurally neutered — a documented true coin-flip pass is correct
  until the deal closes or the spread blows out (which WOULD be a concrete
  catalyst). #12 was decided against a mis-dated calendar row (7/17 vs the
  real 7/21 amc).
- **NOK** (bmo 7/23) — **forced pass (#31, slots full), counterfactual
  −1.17%**. 5/5 slots were legitimately full of same-day entries and the
  T-1 window had elapsed when the run started (~16:04 ET) — a CAPACITY pass
  (disqualifier d), NOT the stale-leg contamination that cost #19/#20. The
  stated lean was a floor-size long: the bar had been cut 39% in six weeks
  into an intact AI/optical demand story (NI guide raised, NVDA optical
  partnership), and a bearish leg would have needed a concrete negative
  catalyst that H2 margin chatter did not provide (ML 0.351, outside the
  down-band). It gapped −1.17%, so a small bearish leg would have edged out a
  small win — but the read was a coin flip on a wide-tailed event (12.43%
  2-DTE implied). Slot allocation, not direction, was the binding call.
  This is also the scale of loss the v0.8.4 ambiguous-catalyst floor accepts.
- **FERG** — **pass on date-integrity, RIGHT** (#15): the 7/21 calendar row
  was false; verified next report 2026-08-10 (calendar still shows phantom
  7/28, 7/31 and 8/4 rows). Do not decide FERG until the date verifies.

Backtest priors (no labeled trade yet):

- **WDFC** (amc): post-open drift fades 5/6 (mean −3.7%) — if held, the
  auction exit is non-negotiable here.
- **PENG** (amc): AI/HPC-adjacent but wide-tailed (worst −17.8%,
  up-rate ~0.5) — minimum size only despite the thematic fit.
- **EPAC / PSMT / AZZ**: coin-flip direction, −10 to −12% tails, modest
  liquidity — exploration size, and a named disqualifier is respectable.
