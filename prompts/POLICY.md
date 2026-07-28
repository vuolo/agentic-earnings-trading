# Trading Policy

Version: 0.8.6
Mode: live when the operator's arm switch is active; paper otherwise

v0.8.6 (strategist review, 2026-07-28, n=33 labeled events, 6 new since
v0.8.5: #38 HOPE, #39 AZN, #41 GLW, #43 PYPL, #44 NVTS, #45 KO): the
templates keep separating winners from losers, and both new rule changes
are PATCH-scale. (1) #41 GLW is the biggest bearish win in the book ON AN
AUCTION BASIS (-14.28% vs entry at the open, +$4.49 labeled / ~+$4.19
auction): template (i) is now 4-for-4, and GLW extends it - the catalyst
stack was PREVIEW-GRADE (Morgan Stanley sold-out-capacity preview against a
+26.7% EPS bar at 76x, insider sales, plant shutdown), not CAG-grade; what
carried it was VIOLENT momentum breakdown (-43% in 4 weeks, new low on
entry day). Realized -15.01% breached BOTH the clean 3-DTE implied 10.99%
and the -10.07% worst historical gap - the 6th implied breach, the first in
the trade's FAVOR. (2) #45 KO was submitted as a designed experiment and
CONFIRMS the precedent leg of template (ii) is LOAD-BEARING: 2.0% off the
high with an elevated bar but INVERTED precedent (KO's last beat gapped
+5.41%), and it beat and gapped +5.03% at the auction, a near-repeat.
Template (ii) requires all three conjuncts - location, bar, AND own-name
precedent that good news pays poorly; the floor discipline capped the loss
at -$1.86 against the tool's $54.16, and the adverse tail +5.41% covered
the realized move while the implied 3.28% was breached (max() vindicated
again). (3) The refuse-the-off-high-short, take-a-small-long conversion
went 2-for-2 live: #38 HOPE +0.67% +$0.18 (first labeled test of the
v0.8.4 ambiguous-catalyst floor leg) and #39 AZN +0.48% +$0.19 (20% off
the high, no forward down-catalyst, refused the short). Longs are now
4-for-9 lifetime; template-era longs 4-1 net +$2.17, all on real auction
fills. (4) #44 NVTS exposes the cost of disqualifier (c) on paper leans:
pass_below_floor ($17.41) forced a mechanical pass while the stated bearish
lean was template-(i)-shaped (-35% in 3 weeks, ATM dilution, patent suit,
pre-guided trough) and NVTS gapped -10.12% - a paper leg deploys ZERO live
capital, so the $20 executability floor protected nothing. RULE CHANGE:
disqualifier (c) now applies only to legs deploying LIVE capital; a bearish
PAPER lean with pass_below_floor submits the bearish_option at the $20
nominal floor instead (#34 INTC shows the cost is trivial when the lean is
a genuine coin flip). (5) ML updates: the down-band is 8-for-13 (#45 KO
0.301 wrong - the band cannot rescue a lean whose own precedent contradicts
it), the 0.35-0.50 dead band is noise a FOURTH time (#39 AZN 0.433 -> UP,
#38 HOPE 0.445 -> UP, #43 PYPL 0.473 -> UP, #41 GLW 0.359 -> -15%), and the
first labeled read above 0.5 ever (#44 NVTS 0.653, its strongest up-read)
was dead wrong on a max-fear setup - there is NO validated band above 0.35.
(6) #43 PYPL's (c)-pass was acceptable (+1.36% auction) but flags an open
question, observation only: its 18.05% adverse tail predates the standing
Stripe/Advent $60.50 bid, and a standing bid compresses the true downside
tail - deal-anchored names may deserve a fresher tail estimate; max()
stays. (7) Label mechanics: #45 KO's ~09:38 quote was WORSE than the
auction for the losing bearish leg (the stock kept climbing) - the
quote-vs-auction gap is a FADE bias, not a universal pro-short bias; labels
now record both prints, keep citing the auction.

v0.8.5 (strategist review, 2026-07-25, n=27 labeled events, 3 new closed
LIVE trades since v0.8.4): the long side is no longer 0-for-N. #32 VZ
(+1.12%, +$0.49), #36 NEM (-1.22%, -$0.55) and #37 EW (+5.61%, +$1.86) are
the first longs since the 0-for-4 batch and went 2-1 for net +$1.80, against
-$14.80 across the first four. All three were labeled off REAL BROKER
AUCTION FILLS (2026-07-24 09:30:01-09:30:21 ET: 44.31, 93.04, 88.00), so the
v0.8.4 label-of-record standard is VERIFIED on the live path; paper legs
still take a ~09:33 quote, so live and paper P&L are not directly
comparable. All three theses explicitly REFUSED an off-high bearish lean
under the v0.8.2/0.8.3 location rule and took a small long instead - the
bearish leg would have LOST on VZ and EW and won only 1.22% on NEM. Five
PATCH refinements, no rule flips and no cap changes: (1) a LONG template
(iii) is documented at exploration size and conviction <= 0.55 - no concrete
negative forward catalyst in the flow, PLUS a fresh same-sector tell
(#32 VZ took its direction from T's +4.27% gap, i.e. our own #22 loss became
the tell), a ONE-SIGNED event history (#37 EW), or a named company-specific
forward driver; (2) #36 NEM is the counterexample and the caution - a MACRO
or commodity driver (gold at record highs) is NOT company-specific, because
the print reprices production and costs rather than the commodity, and it
was the batch's only loss; (3) #37 EW is the first labeled test of a
UNANIMOUS n=6 gap history (6/6 up, worst gap still +1.2%) and it won
+5.61% - recorded as an OPEN HYPOTHESIS only, the 0.60 weak-basis cap stands
at n=1 and EW's conviction was correctly held at 0.53; (4) the 0.35-0.50 ML
band is noise a third time (#32 VZ 0.413 -> UP, #36 NEM 0.444 -> DOWN,
#37 EW 0.476 -> UP); (5) two sizing biases are now documented in both
directions - whole-share flooring cut #32 VZ from an $81.39 decision to
$43.82 deployed, and a hot distant-monthly implied UNDER-sized the batch's
biggest winner (#37 EW got $33.14 off a 29-DTE 10.11% implied against a
5.61% realized move and a +1.2% worst historical gap). max() stays.

v0.8.4 (strategist review, 2026-07-24, n=24 labeled events, 1 new closed
trade + 2 passes since v0.8.3): the headline finding is a MEASUREMENT bug,
not a strategy one. Our labels are taken from a fresh quote at ~09:33-09:36
ET, but the policy's capture is the 09:30 OPENING AUCTION PRINT. In all
four recent paper legs whose label notes record both prices, the quote is
more favorable to the bearish leg than the auction was: #33 NEE (entry
90.145, auction open 90.655 = +0.57%, i.e. a LOSS) was labeled -1.64%
(+$1.65) off a four-minute post-open fade; #28 KMI opened 33.00 (+1.77%)
but was labeled +0.60%; #29 ELS opened 65.52 (+0.11%) but was labeled
-0.27%; #30 AAL opened 14.00 (-4.99%) but was labeled -6.85%. The bias has
one sign because the documented post-open fade (winners -2.7% by 10:00)
flatters short legs. Across those four, labeled P&L is +$5.12 versus about
+$0.37 on an auction basis, so roughly $4.75 of the bearish template's
credited P&L is drift the strategy never captures, and #33 NEE's sign
flips outright. Four PATCH refinements, no rule flips: (1) the AUCTION
PRINT is the label of record (Exit discipline) and pre-0.8.4 labels should
be discounted where the note shows a fade; (2) OFF-TEMPLATE leans take
FLOOR size, not the sizing tool's number - #33 NEE was submitted as an
explicit no-edge mid-range leg at conviction 0.45 and still sized $100.82
(the tool prices RISK, and a 2.89% adverse move buys a big notional), same
shape as #28 KMI at $102.60, and both were wrong at the auction; (3)
short-DTE weekly implied is the best available estimator but NOT an upper
bound - #35 SLB's 1-DTE 3.01% was breached by a +6.14% realized move that
ALSO breached the +2.58% best historical gap, the 5th tail breach and the
first where max() was not conservative, while #34 INTC's liquid 12.36%
overstated a 0.58% move by ~20x; (4) disqualifier (a) is sharpened - a
NAMED concrete forward catalyst whose sign is ambiguous for the name is
not a true coin flip (#35 SLB passed on exactly that and missed +6.14%,
the largest move in the labeled pass set). Off-template bearish leans are
now 0-for-4 with one flat on an auction basis (#22 T, #24 EQT, #28 KMI,
#33 NEE wrong; #29 ELS flat). Template-era bearish paper is 10-1-3 net
+$9.54 as labeled, but at minimum 9-1-4 and about $4.75 lower on an
auction basis - the templates still work, the scoreboard was generous.
Longs were 0-for-4 at that review with #32 VZ, #36 NEM and #37 EW pending
labels; see v0.8.5 for how those three landed.

v0.8.3 (strategist review, 2026-07-23, n=21 labeled events, 3 new closed
trades + 1 pass since v0.8.2): the location story sharpens into a
MOMENTUM-DIRECTION story. #30 AAL (bearish, -6.85%, +$3.96, biggest bearish
win yet) is the THIRD template-(i) concrete-forward-catalyst win (after #7
CAG, #8 UAL) and the FIRST at mid-range location (21.5% off the high) - it
worked because momentum was BREAKING DOWN into the print (-19% in 3 weeks,
the same June jet-fuel shock that won UAL), the exact opposite of the T/EQT
losers that were bouncing UP off 52-week lows. The discriminator for a
bearish lean is therefore momentum DIRECTION into the print, not
distance-from-high alone: template (i) overrides the near-high requirement
when the catalyst is concrete AND the tape is sliding down. Two mid-range
template-(ii) asymmetry leans with NO catalyst confirm the mirror: #28 KMI
(+0.60%, -$0.62, wrong) at 6.8% off the high and #29 ELS (-0.27%, +$0.13,
barely right) at 5.2% off - both moved sub-1%, i.e. NOISE. Template (ii) is
now 5-for-5 within ~4% of the high, 1-1 at 5-7% off (no edge), 0-for-2 at
the lows. Four PATCH refinements, no rule flips: (1) template (i) is
documented as validated 3-for-3 and LOCATION-INDEPENDENT when momentum
breaks down into the print; (2) template (ii) at >~4% off the high is
reclassified as NO-EDGE - floor size or a coin-flip pass, do not spend a
scarce slot on it; (3) the ML down-band (prob_up < 0.35) is now 8-for-12
(#29 ELS 0.287 right, #28 KMI 0.289 wrong added), corroboration only;
(4) #31 NOK was a forced pass on FULL slots (5/5 legitimate same-day
entries, NOT stale-leg contamination - the v0.8.1 on-time-exit fix is
holding), a capacity reminder that on crowded calendars slot allocation
should favor template-(i) catalysts and near-high template-(ii) over
mid-range noise leans. Template-era bearish paper (post-SMPL) is now 9-1-3,
net +$7.90; longs remain 0-for-4 (#27 PNFP exec_failed, no new long
landed). Do NOT default bearish - direction still comes from a concrete
forward catalyst or a near-high asymmetry setup, never from location alone.

v0.8.2 (strategist review, 2026-07-22, n=18 labeled events, 5 new since
v0.8.1): the bearish streak broke and the break is informative. #23 NLY
(-1.21%, +$1.44) and #25 ONB (-1.03%, +$0.28) won; #22 T (+4.27%, -$3.00)
and #24 EQT (+2.04%, -$1.77) are the first bearish paper losses. The split
is LOCATION: every high-bar asymmetry winner (KEY, DX, NLY, ONB, SCHW
counterfactual) sat within ~4% of its 52-week high after a run; both losers
were bearish into names at or bouncing off 52-week LOWS (EQT 0.4% off the
low with 6/6 beats and a named relief-pop risk; T a +12% three-week bounce
off the 7/2 low). Four PATCH refinements: (1) template (ii) now requires
the name EXTENDED NEAR ITS 52-WEEK HIGH - bearish into a de-rated or
at-the-low name is the mirror of the failed cheapness longs and needs a
concrete negative forward catalyst, else conviction caps at 0.50; (2) the
ML confident-down band (prob_up < 0.35) is now 7-for-10, not 5-for-5 - its
two deepest reads ever split (#23 NLY 0.175 right, #24 EQT 0.199 wrong);
corroboration only, unchanged; (3) short-DTE weekly straddles are
validated as trustworthy implied estimates (#22 T 5.19% on a 2-DTE weekly
vs 4.27% realized, which also breached the +3.43% historical best gap -
the 4th tail breach, max() sizing reaffirmed) while distant monthlies
still run hot (#25 ONB 10.8% vs 1.03%); (4) report-date verification is
now explicit in the event snapshot component - #12 WBS and #15 FERG were
decided against mis-dated calendar rows (FERG had no event at all; next
report 2026-08-10) - a wasted decision slot. The v0.8.1 on-time paper-exit
rule WORKED: all four 7/21 legs closed at the 7/22 auction window, no slot
contamination. 14 of 18 labeled events are down/flat but 3 of the 5 newest
were UP (#22 T, #24 EQT, #21 WBS counterfactual) - the down-tape is fading
and "do NOT default bearish" now has direct P&L teeth.

v0.8.1 (strategist review, 2026-07-21, n=13 labeled outcomes, 7 new since
v0.7.2): bearish paper legs are 6-for-6 non-losing (#7 CAG +$1.91, #8 UAL
+$2.30, #11 DX +$0.58, #13 RYAAY +$1.93, #17 AGNC +$0.08, #18 KEY +$0.68)
and 12 of 13 labeled events moved down or flat at the exit (only #4 SMPL
up). Three PATCH refinements, no rule flips: (1) two direction-sourcing
templates are now documented as validated at exploration size - the
concrete-negative-forward-catalyst lean (CAG, UAL, RYAAY) and the high-bar
asymmetry lean at conviction <= 0.55 (KEY, DX; SCHW counterfactual);
(2) the implied_move snapshot component must report straddle expiry DTE and
strike quality - implied overstated realized in all 6 new events on
distant-monthly/coarse chains (max() sizing unchanged; the bias is
conservative); (3) paper legs now explicitly follow the same exit windows
as live positions - #11 DX and #13 RYAAY (BMO 7/20) were carried to 7/21,
contaminating their labels and holding 2 of 5 position slots, which bounced
#19 HAL at the gate and forced #20 SCHW to pass. The participate-by-default
direction and the 0.60 weak-basis cap stand; do NOT default bearish (the
batch is a two-week, sector-clustered risk-off tape and shorts are
paper-only).

v0.8.0 (OPERATOR-DIRECTED, 2026-07-16): sizing is now SERVER-COMPUTED and
equity-breathing — call `compute_position_size` and trade its number (see
Sizing). The fixed dollar tiers and the flat ~$40 loss rule are retired;
risk scales continuously with current equity and conviction, so wins raise
sizes automatically and drawdowns cut them. Same day: the operator's
announcement-anchored exit hypothesis (sell AMC ~print+5-30m, BMO ~07:20
premarket) was tested against real extended-session bars for all 52
Apr-Jul events (reports/research/2026-07-16-announcement-anchored-exit-
study.md): it LOSES 1.2-2.5%/event to the next-open auction on AMC, is a
wash ex-outlier on BMO, and is unexecutable on a third of the slate — the
auction exit stands. One genuine signal was found and PARKED for the
strategist: AH losers tend to bleed further overnight (selling losers at
16:50 beat the open by +0.75%/event, 7/11) — do NOT act on it; note
AH-adverse observations in your thesis to build the labeled sample.

Every decision you submit is stamped with this version. v0.3.0 (operator-
directed): server-computed features are now mandatory — indicators and the
implied move come from `compute_indicators` / `compute_implied_move`, never
your own arithmetic; sentiment comes from WebSearch with cited headlines; the
ML advisory is recorded on every decision. v0.7.1 (strategist review,
2026-07-09, n=3 labeled outcomes): the risk check now uses the IMPLIED move
as the adverse-move estimate when it exceeds the historical tail, and a
backtest-only directional lean caps conviction at 0.60. v0.7.2 (strategist
review, 2026-07-15, n=6 labeled outcomes): longs are 0-for-4 live (PEP #2,
LEVI #3, DAL #5, ERIC #6 all gapped DOWN) and 5 of 6 labeled events
down-gapped; the only winner (#7 CAG bearish, +$1.91) sourced its direction
from a concrete forward catalyst, not the backtest. Refinement: backward-
looking cheapness/de-rating, EPS beat-records, and pre-print momentum no
longer qualify as the independent leg that lifts conviction past 0.60 — all
four failed longs rested on exactly those. The v0.7.1 implied-move sizing is
validated (ERIC's realized −11.1% breached both estimates, yet max() + the
$75 floor still capped the loss at −$8.33). Participation defaults, windows,
default direction, and exit discipline are unchanged — shorts remain
paper-only.

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
  sizing (the sizing tool applies a x0.75 haircut automatically)**,
  conviction bar +0.05, and the backtester must have backfilled the name's
  gap history before you decide — no backtest rows, no trade (submit pass
  and say why).
- **Session awareness**: stocks differ — some trade 24h, some extended, some
  regular-only (get_equity_tradability tells you). Entries and auction exits
  are regular-hours and work for everything; the disaster valve and any AH
  action require extended-hours support and whole shares. Note the symbol's
  session profile in your snapshot under "event".

## Required feature snapshot (before any decision, including pass)

Assemble ALL of the following and submit it as `features_json`. Components
marked (server) MUST be tool outputs embedded verbatim — never hand-computed:

1. **implied_move** (server) — `compute_implied_move` from ATM straddle mids,
   nearest expiry after the report date. This is also the primary
   adverse-move estimate for the sizing check (see Sizing). Report the
   straddle's expiry vs the report date (DTE) and the strike distance from
   spot (v0.8.1): when the nearest listed expiry is a distant monthly
   (>~10 days past the report) or the strikes are coarse/ITM, the implied
   move overstates the EVENT move - flag it as an upper bound. In the
   7/17-7/21 batch implied exceeded realized in all 6 events (#13 RYAAY:
   implied 10.16% on a 35-DTE straddle vs 5.37% realized; #18 KEY 6.98% vs
   1.64%). A 2-3 DTE weekly with fine strikes is the best available
   estimate (#22 T implied 5.19% vs 4.27% realized, #24 EQT 4.2% vs 2.04%,
   #23 NLY 2.45% vs 1.21%, #30 AAL a fine 1-DTE weekly 6.31% vs 6.85%,
   #32 VZ 1-DTE 3.58% vs 1.12%, #36 NEM 1-DTE 5.08% vs 1.22%), while
   distant monthlies still run hot (#25 ONB 30-DTE 10.8% vs 1.03%;
   #29 ELS 30-DTE 6.12% vs 1.58% mean; #37 EW 29-DTE 10.11% vs 5.61%;
   #39 AZN 25-DTE 6.85% vs 0.48%).
   **But implied is NOT an upper bound (v0.8.4)**: #35 SLB's fine 1-DTE
   weekly said 3.01% and the stock gapped +6.14% on a live oil-shock
   catalyst, breaching implied AND the +2.58% best historical gap - the
   first tail breach where max() was not conservative. The opposite extreme
   is just as real on high-vol names: #34 INTC's liquid chain implied
   12.36% against a 0.58% realized move, ~20x. v0.8.6 adds both poles
   again: #41 GLW's clean 3-DTE 10.99% was breached by a -15.01% auction
   gap (the -10.07% worst historical gap breached too - the 6th implied
   breach, the first in the trade's FAVOR), while #45 KO's clean 3-DTE
   3.28% was breached adversely by a +5.03% gap that the +5.41% best-gap
   tail covered - max() did its job. On a junk chain, report the component
   honestly as unavailable rather than inventing a number (#38 HOPE:
   25-DTE monthly, $2.50 strikes, OI<=2, one-sided quotes - correctly
   "unavailable"). Read implied as a DISPERSION estimate, never as a
   forecast or a worst case; a named catalyst can carry the move past it.
   Sizing still uses max() - it is the better of two imperfect numbers.
2. **computed** (server) — `compute_indicators` over ~3 months of daily bars:
   rsi14, atr14_pct, realized_vol20_pct, volume_z20, sma trend, distance from
   high/low, relative strength vs. benchmark.
3. **backtest** (server) — `get_backtest_summary`: gap stats (T-1 close →
   post-open) and drift. State whether the entry window has positive
   expectancy in this name. Report the **adverse_move_pct** you sized against
   (see Sizing) and how it compares to BOTH the implied move and the worst
   (or, for bearish legs, best) historical gap. With n ≤ 6 the historical
   extreme is a biased-low tail estimate — the realized gap has now breached
   it in 5 labeled events (decisions #2 PEP, #4 SMPL, #6 ERIC −11.1% vs worst
   −10.4%, #22 T +4.27% vs best +3.43%, and #35 SLB +6.14% vs best +2.58%);
   the implied move was the closer number in the first four and was ALSO
   breached in #35 SLB (3.01% on a clean 1-DTE weekly). Both estimates can
   fail together when a live catalyst is in play - size accordingly (and
   they failed together AGAIN in the trade's favor on #41 GLW).
4. **historical_reactions** — last 8 quarters where available: day-after move
   % per report, beat/miss record, direction consistency. Note explicitly
   whether the observed gap sample is ONE-SIGNED (every gap the same
   direction, the worst one still favorable) - #37 EW was 6/6 up with a
   +1.2% worst gap and gapped +5.61%, and that is a different object from a
   4/6 or 5/6 up_rate (v0.8.5, open hypothesis, n=1 - it does NOT lift the
   0.60 weak-basis cap). Note also how the name's own LAST BEAT gapped -
   the precedent leg of template (ii) is load-bearing (v0.8.6, #45 KO).
5. **valuation_context** — P/E, market cap; note extremes.
6. **sentiment** — WebSearch recent news: bullish/bearish/mixed with 2-3
   cited headlines. Note any macro_watch reports in the same week (correlated
   AI-complex risk). Note also whether a direct SECTOR COMP has already
   printed this week and how it gapped - #32 VZ sourced its long direction
   from T's +4.27% gap two days earlier on the identical narrative and won
   (v0.8.5); the bearish mirror won twice (UAL -> AAL on the fuel shock).
7. **ml_advisory** (server) — `get_ml_prediction` output, recorded on every
   decision. The sidecar is above base rate (160 rows, CV 55% vs 49%) and
   its confident down-band (prob_up < 0.35) is 8-for-13 directionally
   through 7/28 (right: #11 DX 0.267, #13 RYAAY 0.244, #17 AGNC 0.264,
   #18 KEY 0.315, #20 SCHW 0.277, #23 NLY 0.175, #25 ONB 0.213, #29 ELS
   0.287; wrong: #22 T 0.229, #24 EQT 0.199, #21 WBS 0.215 counterfactual,
   #28 KMI 0.289, #45 KO 0.301). Its two deepest reads ever (0.175 and
   0.199) split one right one wrong - depth adds no calibration (v0.8.2),
   #28/#29 (both ~0.288, split) confirm the band is corroboration, not a
   catalyst, and #45 KO shows the band cannot rescue a lean whose own
   precedent contradicts it (v0.8.6).
   **Reads between 0.35 and 0.50 are NOT corroboration in either direction
   (v0.8.4, reconfirmed v0.8.5 and a FOURTH time v0.8.6)**: #33 NEE cited
   prob_up 0.425 as an "above base rate" bearish leg and the stock printed
   UP at the auction; the three v0.8.5 longs split with no signal (#32 VZ
   0.413 -> UP, #36 NEM 0.444 -> DOWN, #37 EW 0.476 -> UP); the v0.8.6
   batch did it again (#39 AZN 0.433 -> UP, #38 HOPE 0.445 -> UP, #43 PYPL
   0.473 -> UP, #41 GLW 0.359 -> DOWN 15%); #34 INTC 0.551 and #35 SLB
   0.463 were correctly treated as neutral. **There is NO validated band
   above 0.35 in either direction (v0.8.6)**: the first labeled read above
   0.5 ever (#44 NVTS 0.653, the model's strongest up-read) preceded a
   -10.12% gap. Only the <0.35 band counts, and even then it may
   corroborate a lean and temper conviction - it never satisfies the entry
   rules by itself, never overrides them, and never lifts conviction past
   the 0.60 weak-basis cap - it is trained on the same small, down-heavy
   sample it is predicting.
8. **event** — report_date, timing (bmo/amc), source of that date, and
   (v0.8.2) whether a second source confirms it: #12 WBS and #15 FERG were
   decided against mis-dated calendar rows, and FERG had no event at all
   (verified next report 2026-08-10) - a wasted decision slot. If the date
   cannot be verified, say so in the thesis and treat the event as suspect.
9. **playbook** — the symbol's entry in the appended Per-Symbol Playbook.
   State whether the setup fits or contradicts the name's documented
   signature, and cite it when it moves your conviction or sizing.
10. **sizing** (server) — `compute_position_size` output, computed AFTER the
   components above fix your conviction and adverse_move_pct. Embedded
   verbatim; its `size_usd` is the size you submit, EXCEPT on an
   off-template lean, where the floor applies instead (v0.8.4 - see
   Sizing). State the reason whenever you submit below the tool's number.

Missing a component? Say so explicitly (`"unavailable"`), don't invent numbers.

## Entry rules (v0.7 — PARTICIPATE BY DEFAULT, operator directive 2026-07-05)

- **The default action is a TRADE in your best-judged direction.** Conviction
  no longer gates participation — it sets SIZE (see Sizing). At our position
  sizes, a live trade's information value rivals its worst-case cost; the
  dataset, strategist, and ML all starve on passes.
- **A pass now requires an explicit DISQUALIFIER**, stated in the thesis:
  (a) you genuinely cannot form a directional lean after the full snapshot
  (true coin-flip); (b) liquidity/tradability defects (wide spreads, screen
  marginal); (c) `compute_position_size` returns `pass_below_floor` — the
  clamped size is under the $20 floor — **for a leg that would deploy LIVE
  capital (narrowed v0.8.6)**: on a BEARISH lean while shorts are
  paper-only, pass_below_floor is NOT a disqualifier - submit the
  `bearish_option` at the $20 nominal floor instead (see Sizing; #44 NVTS's
  mechanical (c)-pass missed a -10.12% gap its own template-(i)-shaped lean
  had flagged, and the paper leg would have risked nothing live);
  (d) an operator directive or gate
  condition blocks it. "The edge isn't strong" is NOT a disqualifier — that's
  what small sizing is for.
- **Disqualifier (a) requires the ABSENCE of a concrete forward catalyst
  (v0.8.4).** If your snapshot NAMES a concrete forward catalyst but you
  judge its sign ambiguous for this particular name, that is not a true
  coin flip: take a FLOOR-SIZE leg in the catalyst's primary direction at
  conviction ≤ 0.50 when slots are open, and say in the thesis why the sign
  is ambiguous. #35 SLB passed as a "coin flip" while naming the live oil
  surge (Brent >$100, 5th straight up session) and discounting it as
  double-edged and transient; SLB gapped +6.14%, the largest move in the
  labeled pass set (labeled passes otherwise average 1.50% absolute move
  versus 3.46% for trades, so the pass filter itself stays intact and is
  NOT loosened). Floor size caps the cost of being wrong about an
  ambiguous catalyst: #31 NOK's stated floor-size long lean would have lost
  1.17%, which is exactly the scale of downside this rule accepts. First
  labeled test WON (v0.8.6): #38 HOPE took the floor-size long in the
  primary direction of its sign-ambiguous Manubank-acquisition catalyst
  and earned +0.67% (+$0.18) on a real auction fill. On contended slots, a
  documented coin-flip pass remains correct.
- Direction (stocks-only strategy; options deliberately unused):
  - Bullish → `long_equity`.
  - Bearish → `short_equity` **when the context pack shows shorting ENABLED**;
    otherwise → `bearish_option`, the paper-only dataset leg (submit it —
    bearish paper legs are participation too).
  - Shorts use the backtest's BEST gap (upside tail) as the historical input
    to the risk check — a short's worst case is the stock gapping UP.
- **Live calibration caution (v0.7.2, updated v0.8.6 — do NOT flip the
  default)**: through n=33 labeled events the tape is two-sided (#41 GLW
  -15.01% and #44 NVTS -10.12% down; #45 KO +5.03%, #35 SLB +6.14%,
  #37 EW +5.61%, #43 PYPL +1.36% up) - direction must come from a
  template, never from a tape prior. Longs are now 4-for-9 lifetime:
  0-for-4 on the first batch (-$14.80, all backward-looking legs) and 4-1
  for net +$2.17 on the template-era batch (#32 VZ +1.12% +$0.49, #37 EW
  +5.61% +$1.86, #36 NEM -1.22% -$0.55, #38 HOPE +0.67% +$0.18, #39 AZN
  +0.48% +$0.19), all five labeled off real auction fills.
  Template-era bearish paper is 11-2-3 net +$12.17 AS LABELED, but the
  labels can credit post-open fade the auction exit does not capture
  (v0.8.4): on an auction basis it is at minimum 10-2-4 and roughly $4.70
  lower. Paper legs are labeled off a ~09:33-09:38 quote while live legs
  are labeled off REAL AUCTION FILLS - do not compare paper and live P&L
  directly, and discount the paper scoreboard. Three direction-sourcing
  templates are validated at exploration size:
  (i) **concrete negative forward catalyst** — validated 4-for-4: #7 CAG
  (imminent dividend cut, -2.54%), #8 UAL (jet fuel surged above
  management's cost assumption, -3.07%), #30 AAL (same June fuel shock
  above the guidance curve into a low bar, -6.85% labeled / -4.99% at the
  auction print), #41 GLW (-14.28% at the auction vs entry, +$4.49, the
  biggest bearish win in the book); #13 RYAAY (guided −22% YoY EPS, 90-day
  estimate collapse, T-1 −5.8% break, -5.37%) is a fifth. This template is
  LOCATION-INDEPENDENT (v0.8.3): AAL won at mid-range (21.5% off the high)
  because momentum was BREAKING DOWN into the print (-19% in 3 weeks) - the
  discriminator vs the T/EQT losers is momentum DIRECTION, not
  distance-from-high. #41 GLW extends it (v0.8.6): a PREVIEW-GRADE
  negative stack (analyst preview naming capacity limits against a
  +26.7% EPS bar at 76x, insider sales, plant shutdown) qualifies when
  momentum is VIOLENTLY breaking down (-43% in 4 weeks, new low on entry
  day) - conviction stays ~0.52-0.55 and exploration size on the softer
  catalyst grade. A concrete forward catalyst plus a tape sliding DOWN
  into the print overrides the near-high requirement of template (ii); a
  catalyst-less bearish lean into UP momentum off a low is the failure mode
  (T, EQT).
  (ii) **high-bar asymmetry lean, conviction ≤ 0.55, ONLY on a name
  EXTENDED NEAR ITS 52-WEEK HIGH (~4%, v0.8.2), AND ONLY when the name's
  OWN precedent shows good news paying poorly (v0.8.6)** — an elevated
  consensus bar into an extended tape where the name's own precedent shows
  good news pays poorly, corroborated by an above-base-rate ML read. ALL
  THREE conjuncts are load-bearing. Near the high with the precedent leg
  intact it is 5-for-5 (#18 KEY 1.8% off, #11 DX post-run premium to stale
  book, #23 NLY 3% off at 1.14x book, #25 ONB 4.2% off after +14.5%,
  #20 SCHW 1.5% off counterfactual). The PRECEDENT conjunct got its
  designed test in #45 KO (v0.8.6): 2.0% off the high with an elevated bar
  but an INVERTED precedent - KO's last beat had gapped +5.41% - and it
  beat and gapped +5.03% at the auction, a near-repeat (-$1.86 at the $30
  floor; the ML down-band read 0.301 could not rescue it). Near-high
  location alone is NOT template (ii): with inverted precedent the name is
  OFF-TEMPLATE (floor size either direction), and an inverted precedent
  may itself be a long tell (n=1, open hypothesis, does not lift any cap).
  Away from the high the lean has NO edge, and v0.8.4 hardened the finding
  on an auction basis: OFF-TEMPLATE bearish leans are 0-for-4 with one
  flat (#22 T +4.27% and #24 EQT +2.04% at the lows; #28 KMI +1.77% at the
  auction, 6.8% off the high; #33 NEE +0.57% at the auction, 8.65% off the
  high; #29 ELS +0.11% at the auction, 5.2% off, a flat that its label
  scored as a win), and 0-for-5 counting #45 KO's inverted-precedent leg.
  A bearish lean off template (ii) at >~4% off the high is the MIRROR of
  the failed cheapness longs: "already fallen" (and "modestly de-rated")
  is not a down-catalyst. Off-high, a bearish leg requires template (i);
  otherwise cap conviction at 0.50, take FLOOR SIZE (mandatory since
  v0.8.4 - see Sizing; #33 NEE correctly called itself no-edge and still
  deployed $100.82), and on a crowded calendar do NOT spend a scarce slot
  on a mid-range asymmetry lean (#31 NOK was a forced pass on 5/5 full
  slots). The asymmetry lean is NOT a catalyst — it never lifts conviction
  past 0.55.
  (iii) **LONG mirror, conviction ≤ 0.55, exploration size (v0.8.5)** —
  when a name is OFF its high with NO concrete negative forward catalyst in
  the flow, the correct expression is a SMALL LONG, not a bearish lean.
  Requires BOTH: (1) no concrete negative forward catalyst (bullish or
  neutral news flow, no guidance cut, no negative estimate revision), and
  (2) at least one of - a FRESH SAME-SECTOR TELL from a comparable that
  just printed (#32 VZ took direction from T's +4.27% gap two days earlier
  on the identical Starlink/broadband narrative: +1.12%, +$0.49), a
  ONE-SIGNED event history (#37 EW 6/6 up gaps with the worst still +1.2%,
  entering oversold at -11.4% off its high with an unchanged bar and fresh
  target raises: +5.61%, +$1.86), or a NAMED COMPANY-SPECIFIC forward
  driver. **A MACRO or COMMODITY driver does not qualify as (2)**: #36 NEM
  sourced its long from gold at record highs and lost 1.22% - the print
  reprices company items (production -10.9% YoY, costs), not the commodity,
  so a macro driver is at best a tiebreaker. The broader
  refuse-the-off-high-short conversion is 4-1 through v0.8.6 (#32 VZ,
  #37 EW, #39 AZN off-template floor long +0.48%, #38 HOPE
  ambiguous-catalyst floor long +0.67%; #36 NEM the loss). This template
  does NOT lift any cap: a long still requires a named CONCRETE FORWARD
  catalyst to exceed 0.60, and "cheap / beats / momentum" is never one
  (the 0-for-4 batch). Its whole value is that it converts the documented
  off-template bearish failure mode into a small, correctly-signed
  participation.
- **Conviction cap on weak-basis leans (v0.7.1, tightened v0.7.2)**: cap
  conviction at **0.60** whenever your directional lean rests primarily on
  either (a) the backtest's gap direction (`up_rate` or the sign of
  `mean_pct`) with n ≤ 6 — a 6-sample up-rate has a standard error near 0.20,
  it cannot separate a coin flip from a real edge, and it was wrong in 6 of 6
  labeled events (#2 PEP 0.67 → down; #3 LEVI +3.32% → down; #4 SMPL 0.33 →
  up; #5 DAL 0.83 → down; #6 ERIC +2.94% → down; #7 CAG 0.80 → down); or
  (b) backward-looking cheapness/de-rating, an EPS beat-record, or pre-print
  momentum — the four failed longs each leaned on these and went 0-for-4
  (#2 PEP cheap+target-cuts → −3.93%; #3 LEVI 6 beats near 52w high → −4.17%;
  #5 DAL 6-for-6 beats + rising trend → −0.61%; #6 ERIC de-rated + pre-print
  pop → −11.10%). The same backward-looking legs are equally invalid as
  DOWN-catalysts (v0.8.2: #22 T, #24 EQT). To exceed 0.60, the
  corroborating leg must be a CONCRETE FORWARD catalyst (a specific
  guidance signal, a pending event, product/sector news) or a per-symbol
  playbook line — never those backward-looking legs alone. The cap holds
  for a ONE-SIGNED n=6 history too (v0.8.5): #37 EW's 6/6-up sample won
  +5.61% at conviction 0.53, which is one event, not a licence - record the
  observation and stay capped. This caps SIZE, never participation — trade
  anyway, smaller.

## Sizing (v0.8.0 — SERVER-COMPUTED, equity-breathing)

- **Call `compute_position_size(symbol, conviction, adverse_move_pct,
  overnight)` and trade its `size_usd`.** Embed its output verbatim in
  features_json under `"sizing"`. Never hand-compute a size; never submit a
  size above the tool's number (below is allowed only with a stated reason,
  e.g. odd-lot rounding).
- **OFF-TEMPLATE LEANS TAKE FLOOR SIZE, $20-40 (v0.8.4).** The sizing tool
  prices RISK, not EDGE: on a name with a small adverse move it returns a
  large notional even at low conviction, which is how #33 NEE - a leg whose
  own thesis called it "mid-range NO-EDGE zone" at conviction 0.45 - became
  a $100.82 position (adverse 2.89%), the largest of its batch, and how
  #28 KMI became $102.60. Both were wrong at the auction print. When your
  lean satisfies NONE of template (i) (concrete negative forward catalyst
  with the tape sliding down), template (ii) (high-bar asymmetry within
  ~4% of the 52-week high with intact precedent) or template (iii) (the
  long mirror), submit the
  $20-40 floor with the stated reason "off-template, no documented edge" -
  the dataset gets its row, the T+1 buying power stays free for template
  setups, and the position is sized to the information, not to the risk
  budget. The same floor applies to the ambiguous-catalyst leg under
  disqualifier (a) above. VALIDATED both ways in the 7/27 batch (v0.8.6):
  #45 KO's $30 floor (vs the tool's $54.16) capped a designed-experiment
  loss at -$1.86 through a +5.03% adverse gap, and #38 HOPE's $27 floor
  overrode a $244.44 tool number priced off a 0.84% adverse input - the
  small-adverse/big-notional trap in its purest form yet - and still won
  its label.
- `adverse_move_pct = max(implied_move_pct, |historical gap tail|)` — the
  v0.7.1 rule, unchanged: the tail is the WORST gap for longs, the BEST gap
  for bearish legs; with n ≤ 6 the historical extreme is biased low and the
  implied move was the closer estimate in 4 of the 5 labeled tail breaches
  (#22 T realized +4.27% vs best-gap +3.43%, covered by the 2-DTE implied
  5.19%). In the 5th (#35 SLB) BOTH were breached - a 1-DTE implied 3.01%
  and a +2.58% best gap against a +6.14% realized move - so max() is the
  better of two imperfect numbers, not a worst case. **The bias runs both
  ways and BOTH are now documented (v0.8.5)**: a hot distant-monthly
  implied UNDER-sizes exactly the setups with the cleanest history -
  #37 EW, the biggest percentage winner in the book's long column, drew the
  batch's smallest size ($33.14) because a 29-DTE straddle implied 10.11%
  against a 5.61% realized move while its own worst historical gap was
  +1.2%. v0.8.6 adds a clean max() vindication: #45 KO's +5.41% best-gap
  tail covered a +5.03% adverse gap that breached the clean 3-DTE implied
  3.28%. max() STAYS (six implied breaches earn the conservatism); note
  the distortion in the thesis rather than working around it. OPEN
  QUESTION, observation only (v0.8.6, #43 PYPL): on a DEAL-ANCHORED name,
  a historical tail that predates a standing bid (PYPL's 18.05% pre-bid
  worst gap under a $60.50 Stripe/Advent bid) overstates the true downside
  and can mechanically force a (c)-pass - flag it in the thesis; no rule
  change yet.
- What the server does (so you can sanity-check, not recompute): risk 1% of
  CURRENT equity at conviction 0.5, rising ~0.5%/0.1 conviction to a 3%
  ceiling; size = risk / adverse_move; haircuts non-core x0.75 and
  overnight-through-print x0.8; clamped to the per-position arm cap, half of
  equity, buying power minus $5, and the remaining daily budget — the
  binding constraint is named in the output. The account BREATHES: equity
  growth raises every size automatically, drawdowns cut them.
- If the tool returns `pass_below_floor` (clamped size under $20) on a leg
  that would deploy LIVE capital, that is disqualifier (c): submit a pass
  citing the sizing output. **On a bearish PAPER lean it is NOT a
  disqualifier (v0.8.6)**: submit the `bearish_option` at the $20 nominal
  floor with the sizing output embedded and the reason stated - the leg
  deploys no live capital, so the executability floor protects nothing.
  #44 NVTS's mechanical (c)-pass missed a -10.12% gap its stated
  template-(i)-shaped bearish lean had flagged, while #34 INTC (the same
  mechanic on a genuine coin flip) cost nothing - the asymmetry favors
  submitting the paper row. The floor is low
  on purpose — fractional orders execute fine at $20-40, and a small live
  fill on a wild name is exactly the evidence the dataset wants.
- The daily budget and per-position arm cap are enforced by the gate
  regardless — the tool mirrors them so an honest submission never bounces.
- **Whole-share flooring can halve your deployed size (v0.8.5).** The
  executor prefers whole shares when the price fits, because only whole
  shares can exit after-hours: #32 VZ's $81.39 decision became ONE share at
  $43.8199, i.e. 46% of the intended notional, and the label/P&L were
  reconciled to the real fill. On a name priced above roughly half your
  size, expect the deployed amount to round down hard - that is correct
  behaviour, not an error, but say so in the thesis so the P&L is read
  against the size actually at risk.
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
- **Exits fill IN the opening auction**: the evening tick queues a gfd market
  close after the reaction-day close (crash-proof; gfd not gtc — Robinhood
  rejects gtc on market/fractional orders), and the 9:24 morning run
  verifies/places it pre-open — both paths fill at the 9:30 auction print,
  the exact price the backtests measure. Nobody waits for a bounce (post-open
  fade: winners −2.7% by 10:00); holding past the open requires a future
  data-backed policy change, not in-the-moment judgment. Reconfirmed
  2026-07-09 (decision #4): SMPL printed 15.03 in the auction and traded
  13.47 by 09:39 ET, −10.4% in nine minutes — the auction print, not the
  post-open drift, is the capture. Re-tested 2026-07-16 with announcement-
  ANCHORED exits (print+5/15/30m, premarket 07:20/08:00) across all 52
  Apr–Jul events: anchored exits lose 1.2–2.5%/event on AMC, wash on BMO
  ex-outlier, unexecutable on a third of the slate — the auction stands.
- **The AUCTION PRINT is the label of record (v0.8.4), and the LIVE path now
  meets that standard (v0.8.5).** #32 VZ, #36 NEM and #37 EW were labeled
  off real broker auction fills (2026-07-24 09:30:01-09:30:21 ET at 44.31,
  93.04 and 88.00), which is the price the strategy actually got; #38 HOPE
  and #39 AZN followed (2026-07-27 09:30 fills). PAPER
  legs are still labeled from a fresh quote at ~09:33-09:38, and that bias
  is systematic where the post-open fade flatters short legs:
  #33 NEE opened 90.655 against a 90.145 entry (+0.57%, a LOSS) yet
  was labeled -1.64% (+$1.65) off the 09:34 quote; #28 KMI opened 33.00
  (+1.77%) and was labeled +0.60%; #29 ELS opened 65.52 (+0.11%) and was
  labeled -0.27%; #30 AAL opened 14.00 (-4.99%) and was labeled -6.85%.
  Labeled P&L across those four is +$5.12 versus about +$0.37 on an auction
  basis. The bias is a FADE bias, not a universal pro-short bias (v0.8.6):
  when the stock keeps RUNNING after the open the quote is WORSE for the
  short leg than the auction was (#45 KO auction +5.03% but quote +6.19%).
  Label notes now record BOTH prints. When you cite a labeled outcome in a
  thesis or a review, prefer the
  auction figure where the note records it, treat pre-0.8.4 bearish P&L as
  generous, and do NOT compare paper P&L directly against live P&L. If both
  prints are available, state both.
- **Paper legs follow the SAME exit windows as live positions (v0.8.1).**
  A `bearish_option` or any other paper leg is closed by the morning tick at
  the post-report open, exactly like a live fill — its label must measure
  the same capture the strategy trades. #11 DX and #13 RYAAY (BMO 7/20)
  were carried to 7/21: their labels absorbed a day of extra drift AND the
  stale legs held 2 of 5 position slots, bouncing #19 HAL at the gate and
  forcing #20 SCHW to pass on a lean the counterfactual says was right.
  VERIFIED WORKING 2026-07-22 (v0.8.2): all four 7/21 paper legs (#22 T,
  #23 NLY, #24 EQT, #25 ONB) closed on time at the 7/22 morning tick, no
  slot contamination; #28 KMI, #29 ELS, #30 AAL, #33 NEE, #41 GLW and
  #45 KO likewise closed
  on time at their windows. A paper leg found open past its window is
  closed at the first available tick and the late close is stated in the
  label notes.
- **Hold-to-close variants remain UNAUTHORIZED.** A favorable n ≤ 6 backtest
  drift stat is not sufficient evidence to extend the holding period (that
  prior class went 0-for-3 on direction in the first labeled cycle). Extending
  any exit requires labeled outcomes spanning several events, decided by a
  strategist review — never in-the-moment judgment. Note the observation in
  your thesis and move on.
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