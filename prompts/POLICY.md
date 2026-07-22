# Trading Policy

Version: 0.8.2
Mode: live when the operator's arm switch is active; paper otherwise

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
report 2026-08-10). The v0.8.1 on-time paper-exit rule WORKED: all four
7/21 legs closed at the 7/22 auction window, no slot contamination. 14 of
18 labeled events are down/flat but 3 of the 5 newest were UP (#22 T,
#24 EQT, #21 WBS counterfactual) - the down-tape is fading and "do NOT
default bearish" now has direct P&L teeth.

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
   1.64%). Conversely (v0.8.2), a 2-3 DTE weekly with fine strikes is a
   trustworthy estimate: #22 T implied 5.19% vs 4.27% realized, #24 EQT
   4.2% vs 2.04%, #23 NLY 2.45% vs 1.21% - while #25 ONB's 30-DTE monthly
   said 10.8% vs 1.03% realized. Sizing still uses max() - the bias is
   conservative.
2. **computed** (server) — `compute_indicators` over ~3 months of daily bars:
   rsi14, atr14_pct, realized_vol20_pct, volume_z20, sma trend, distance from
   high/low, relative strength vs. benchmark.
3. **backtest** (server) — `get_backtest_summary`: gap stats (T-1 close →
   post-open) and drift. State whether the entry window has positive
   expectancy in this name. Report the **adverse_move_pct** you sized against
   (see Sizing) and how it compares to BOTH the implied move and the worst
   (or, for bearish legs, best) historical gap. With n ≤ 6 the historical
   extreme is a biased-low tail estimate — the realized gap has now breached
   it in 4 labeled events (decisions #2 PEP, #4 SMPL, #6 ERIC −11.1% vs worst
   −10.4%, and #22 T +4.27% vs best +3.43%); the implied move was the closer
   number each time.
4. **historical_reactions** — last 8 quarters where available: day-after move
   % per report, beat/miss record, direction consistency.
5. **valuation_context** — P/E, market cap; note extremes.
6. **sentiment** — WebSearch recent news: bullish/bearish/mixed with 2-3
   cited headlines. Note any macro_watch reports in the same week (correlated
   AI-complex risk).
7. **ml_advisory** (server) — `get_ml_prediction` output, recorded on every
   decision. The sidecar is above base rate (141 rows, CV 53% vs 48%) and
   its confident down-band (prob_up < 0.35) is 7-for-10 directionally
   through 7/22 (right: #11 DX 0.267, #13 RYAAY 0.244, #17 AGNC 0.264,
   #18 KEY 0.315, #20 SCHW 0.277, #23 NLY 0.175, #25 ONB 0.213; wrong:
   #22 T 0.229, #24 EQT 0.199, #21 WBS 0.215 counterfactual). Its two
   deepest reads ever (0.175 and 0.199) split one right one wrong - depth
   adds no calibration (v0.8.2). It may corroborate a lean and temper
   conviction, but it never satisfies the entry rules by itself, never
   overrides them, and never lifts conviction past the 0.60 weak-basis cap -
   it is trained on the same small, down-heavy sample it is predicting.
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
   verbatim; its `size_usd` is the size you submit.

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
  clamped size is under the $20 floor; (d) an operator directive or gate
  condition blocks it. "The edge isn't strong" is NOT a disqualifier — that's
  what small sizing is for.
- Direction (stocks-only strategy; options deliberately unused):
  - Bullish → `long_equity`.
  - Bearish → `short_equity` **when the context pack shows shorting ENABLED**;
    otherwise → `bearish_option`, the paper-only dataset leg (submit it —
    bearish paper legs are participation too).
  - Shorts use the backtest's BEST gap (upside tail) as the historical input
    to the risk check — a short's worst case is the stock gapping UP.
- **Live calibration caution (v0.7.2, updated v0.8.2 — do NOT flip the
  default)**: through n=18 labeled events, 14 moved down or flat at the
  exit, but 3 of the 5 NEWEST moved UP (#22 T +4.27%, #24 EQT +2.04%,
  #21 WBS +1.0% counterfactual) - the down-tape is fading, and the first
  two bearish paper losses (net -$3.05 on the 7/21-7/22 batch) are the
  direct cost of leaning bearish off-template. Longs remain 0-for-4 (no
  new longs landed - #16 MMM exec_failed, #19 HAL gate-rejected); bearish
  paper legs are 7-1-2 (seven wins, one flat, two losses, net +$4.45).
  Two direction-sourcing templates are validated at exploration size:
  (i) **concrete negative forward catalyst** — #7 CAG (imminent dividend
  cut), #8 UAL (fuel surged above management's cost assumption), #13 RYAAY
  (guided −22% YoY EPS, 90-day estimate collapse, T-1 −5.8% break); and
  (ii) **high-bar asymmetry lean, conviction ≤ 0.55, ONLY on a name
  EXTENDED NEAR ITS 52-WEEK HIGH (v0.8.2)** — an elevated consensus bar
  into an extended tape where the name's own precedent shows good news
  pays poorly, corroborated by an above-base-rate ML read. All five
  winners sat within ~4.2% of the 52-week high after a run (#18 KEY 1.8%
  off, #11 DX post-run premium to stale book, #23 NLY 3% off at 1.14x
  book, #25 ONB 4.2% off after +14.5%, #20 SCHW 1.5% off counterfactual).
  Applied to names at or bouncing off 52-week LOWS it is 0-for-2: #24 EQT
  (0.4% off the low, 6/6 beats, relief-popped +2.04%) and #22 T (+12%
  bounce off the 7/2 low, gapped +4.27% - its "overhang" list of
  downgrades and threats was sentiment, not a forward catalyst). A bearish
  lean on a beaten-down/de-rated name is the MIRROR of the failed
  cheapness longs: "already fallen" is not a down-catalyst. On such names
  a bearish leg requires template (i); otherwise cap conviction at 0.50
  and prefer floor size or a documented coin-flip pass. The asymmetry
  lean is NOT a catalyst — it never lifts conviction past 0.55. A long
  still requires a named CONCRETE FORWARD catalyst in the thesis;
  "cheap / beats / momentum" is not one — see the cap below.
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
  playbook line — never those backward-looking legs alone. This caps SIZE,
  never participation — trade anyway, smaller.

## Sizing (v0.8.0 — SERVER-COMPUTED, equity-breathing)

- **Call `compute_position_size(symbol, conviction, adverse_move_pct,
  overnight)` and trade its `size_usd`.** Embed its output verbatim in
  features_json under `"sizing"`. Never hand-compute a size; never submit a
  size above the tool's number (below is allowed only with a stated reason,
  e.g. odd-lot rounding).
- `adverse_move_pct = max(implied_move_pct, |historical gap tail|)` — the
  v0.7.1 rule, unchanged: the tail is the WORST gap for longs, the BEST gap
  for bearish legs; with n ≤ 6 the historical extreme is biased low and the
  implied move was the closer estimate in the 4 labeled tail breaches
  (latest: #22 T realized +4.27% vs best-gap +3.43%, covered by the 2-DTE
  implied 5.19%). (On sparse screened-name chains implied can also
  OVERSTATE the event move — see snapshot component 1 — but max() stays:
  that bias only shrinks size.)
- What the server does (so you can sanity-check, not recompute): risk 1% of
  CURRENT equity at conviction 0.5, rising ~0.5%/0.1 conviction to a 3%
  ceiling; size = risk / adverse_move; haircuts non-core x0.75 and
  overnight-through-print x0.8; clamped to the per-position arm cap, half of
  equity, buying power minus $5, and the remaining daily budget — the
  binding constraint is named in the output. The account BREATHES: equity
  growth raises every size automatically, drawdowns cut them.
- If the tool returns `pass_below_floor` (clamped size under $20), that is
  disqualifier (c): submit a pass citing the sizing output. The floor is low
  on purpose — fractional orders execute fine at $20-40, and a small live
  fill on a wild name is exactly the evidence the dataset wants.
- The daily budget and per-position arm cap are enforced by the gate
  regardless — the tool mirrors them so an honest submission never bounces.
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
- **Exits fill IN the opening auction**: the evening tick queues a gtc market
  close after the reaction-day close (crash-proof), and the 9:24 morning run
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
- **Paper legs follow the SAME exit windows as live positions (v0.8.1).**
  A `bearish_option` or any other paper leg is closed by the morning tick at
  the post-report open, exactly like a live fill — its label must measure
  the same capture the strategy trades. #11 DX and #13 RYAAY (BMO 7/20)
  were carried to 7/21: their labels absorbed a day of extra drift AND the
  stale legs held 2 of 5 position slots, bouncing #19 HAL at the gate and
  forcing #20 SCHW to pass on a lean the counterfactual says was right.
  VERIFIED WORKING 2026-07-22 (v0.8.2): all four 7/21 paper legs (#22 T,
  #23 NLY, #24 EQT, #25 ONB) closed on time at the 7/22 morning tick, no
  slot contamination. A paper leg found open past its window is closed at
  the first available tick and the late close is stated in the label notes.
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