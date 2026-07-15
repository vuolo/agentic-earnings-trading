# Trading Policy

Version: 0.7.2
Mode: live when the operator's arm switch is active; paper otherwise

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
  sizing (base $100, max $150)**, conviction bar +0.05, and the backtester
  must have backfilled the name's gap history before you decide — no
  backtest rows, no trade (submit pass and say why).
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
   adverse-move estimate for the sizing check (see Sizing).
2. **computed** (server) — `compute_indicators` over ~3 months of daily bars:
   rsi14, atr14_pct, realized_vol20_pct, volume_z20, sma trend, distance from
   high/low, relative strength vs. benchmark.
3. **backtest** (server) — `get_backtest_summary`: gap stats (T-1 close →
   post-open) and drift. State whether the entry window has positive
   expectancy in this name. Report the **adverse_move_pct** you sized against
   (see Sizing) and how it compares to BOTH the implied move and the worst
   (or, for bearish legs, best) historical gap. With n ≤ 6 the historical
   extreme is a biased-low tail estimate — the realized gap has now breached
   it in 3 of 6 events (decisions #2 PEP, #4 SMPL, #6 ERIC −11.1% vs worst
   −10.4%); the implied move was the closer number each time.
4. **historical_reactions** — last 8 quarters where available: day-after move
   % per report, beat/miss record, direction consistency.
5. **valuation_context** — P/E, market cap; note extremes.
6. **sentiment** — WebSearch recent news: bullish/bearish/mixed with 2-3
   cited headlines. Note any macro_watch reports in the same week (correlated
   AI-complex risk).
7. **ml_advisory** (server) — `get_ml_prediction` output. Advisory while the
   dataset is small: it may temper conviction but never satisfies the entry
   rules by itself, and never overrides them.
8. **event** — report_date, timing (bmo/amc), source of that date.
9. **playbook** — the symbol's entry in the appended Per-Symbol Playbook.
   State whether the setup fits or contradicts the name's documented
   signature, and cite it when it moves your conviction or sizing.

Missing a component? Say so explicitly (`"unavailable"`), don't invent numbers.

## Entry rules (v0.7 — PARTICIPATE BY DEFAULT, operator directive 2026-07-05)

- **The default action is a TRADE in your best-judged direction.** Conviction
  no longer gates participation — it sets SIZE (see Sizing). At our position
  sizes, a live trade's information value rivals its worst-case cost; the
  dataset, strategist, and ML all starve on passes.
- **A pass now requires an explicit DISQUALIFIER**, stated in the thesis:
  (a) you genuinely cannot form a directional lean after the full snapshot
  (true coin-flip); (b) liquidity/tradability defects (wide spreads, screen
  marginal); (c) the sizing check fails even at minimum size (adverse_move_pct
  × min size exceeds ~$40 tolerable loss); (d) an operator directive or gate
  condition blocks it. "The edge isn't strong" is NOT a disqualifier — that's
  what small sizing is for.
- Direction (stocks-only strategy; options deliberately unused):
  - Bullish → `long_equity`.
  - Bearish → `short_equity` **when the context pack shows shorting ENABLED**;
    otherwise → `bearish_option`, the paper-only dataset leg (submit it —
    bearish paper legs are participation too).
  - Shorts use the backtest's BEST gap (upside tail) as the historical input
    to the risk check — a short's worst case is the stock gapping UP.
- **Live calibration caution (v0.7.2 — do NOT flip the default)**: through
  n=6, longs are 0-for-4 and 5 of 6 labeled events down-gapped — a risk-off
  earnings tendency in this sample. This is NOT a mandate to default bearish
  (the sample is small, sector-mixed, and shorts are paper-only); the
  participate-by-default direction stands. It IS a mandate to name, in the
  thesis, the concrete forward catalyst a long rests on. "Cheap / beats /
  momentum" is not one — see the cap below. The only live win (#7 CAG) was a
  bearish paper leg sourced from a concrete negative catalyst.
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
  pop → −11.10%). To exceed 0.60, the corroborating leg must be a CONCRETE
  FORWARD catalyst (a specific guidance signal, a pending event, product/
  sector news) or a per-symbol playbook line — never those backward-looking
  legs alone. This caps SIZE, never participation — trade anyway, smaller.

## Sizing (real-money, ~$500 account — conviction is the dial)

- **Conviction < 0.55** (leaning, weak): exploration size **$75**.
- **0.55–0.70**: **$100–150**.
- **≥ 0.70**: **$150–200**; **≥ 0.80**: up to **$250** (the arm cap).
- Non-core (screened) names: one tier smaller than the table says.
- BMO/overnight and short entries: one tier smaller than the table says
  (overnight gap risk), never above $200 unless core + conviction ≥ 0.85.
- **Adverse-move check (v0.7.1, supersedes the historical-worst check)**:
  define `adverse_move_pct = max(implied_move_pct, |historical gap tail|)`,
  where the historical tail is the WORST gap for longs and the BEST gap for
  bearish legs. Size so that `adverse_move_pct × size ≤ ~$40`; if that ceiling
  is below your conviction tier, **the ceiling wins**. Rationale: across the
  first three labeled events the realized gap exceeded the 6-quarter
  historical extreme twice, and the implied move was the better estimate both
  times (#4 SMPL: implied 16.97% vs realized 17.06%, historical tail only
  11.23%; #2 PEP: implied 3.29% vs realized 3.93%, historical worst only
  2.78%). Only when adverse_move_pct × $75 still exceeds ~$40 does this become
  a pass disqualifier — expect that to be rare, and prefer the floor size.
- Guideline: never over ~50% of equity in one name — the account snapshot in
  the context pack is the equity reference. The daily budget ($450) and
  per-position arm cap are enforced by the gate regardless.
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
  post-open drift, is the capture.
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