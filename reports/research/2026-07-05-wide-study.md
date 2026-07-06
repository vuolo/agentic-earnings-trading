# Wide Study — per-event structure, BMO premarket, multi-day drift (2026-07-05)

Operator asked for a wider, more thorough, non-generalized analysis, including
BMO pre-market handling. Four extensions over the two earlier studies (which
covered post-open intraday and AMC after-hours). Companion scripts committed.

## 1. Every event, no averaging (90 events, 6 quarters, daily resolution)

Full per-symbol gap|drift tables are in prompts/PLAYBOOK.md (now injected into
every analyst and strategist run). Highlights that averages were hiding:

- **TSM** drifts negative after the open **6/6** quarters. **NVDA** 6/6 —
  and NVDA barely gaps anymore (|gap| < 3% in 5/6): its gap edge is weak.
- **ORCL** is the lone consistent extender: day-0 drift positive **5/6**
  regardless of gap direction. An ORCL hold-to-close variant is a candidate
  once the strategist has live outcomes to weigh.
- **HPE**'s drift never once followed its gap (0/6); gap-ups faded 4/4.
  **CRDO** gap-ups faded 3/3. **MRVL** drift followed the gap 6/6 (momentum).
- Bucket structure: up-gaps of +2–10% fade day-0 (−2.2 to −2.6% avg over 22
  events); down-gaps of 5–10% bounce mildly (+0.7%, 15 events); >10% gaps
  (36 events) have no pooled signal — behavior is name-specific.

## 2. BMO pre-market exits ("before hours") — n=2, informative not decisive

30-min 24_5-session bars on the two BMO reaction mornings:

- **TSM 4/16** (reports ~2am ET): premarket 4:30–5am was the ONLY window
  above water (+0.4/+0.8% vs −1.66% at the open) — the fade began hours
  before the bell. 6:30am −1.89%, 8am −1.24%, 9am −1.56%.
- **VRT 4/22** (reports ~5:30–6am): early premarket was WORSE (−4.3 to −4.8%
  at 6–7:30am); 8am briefly best (−0.86%); open −2.28%.

Read: premarket exit quality depends on when the name reports and premarket
liquidity (VRT premarket volumes were tiny; spreads unobservable in bars —
real fills worse). Mechanically possible (24_5 limit orders, whole shares
only). **Default stays 9:31**; a premarket exit window (~8:00–9:15, marketable
limit, whole shares) is parked as an operator-optional experiment once more
BMO events accumulate. TSM 7/16 will add n=3.

## 3. Multi-day drift (PEAD) — hold days instead of exiting at the open?

All 15 recent events, long P&L from T-1 close (avg):
open +4.71% | day0 close +4.35% | d+1 +3.17% | d+2 +5.63% | d+3 +6.11%

Looks like holding wins — until you refuse to generalize:
- Hold-to-d+2 beat exit-at-open in only **7/15** events (coin flip).
- The tails are violent both ways: AMD +12.9pts by d+2, COHR +14.8pts,
  DELL +15.1pts at the d+1 peak — vs **HPE −19.9pts, ALAB −13.9, MU −8.4**.
- d+3 averages are contaminated (MRVL's +46% includes its own 6/2 catalyst).

Verdict: multi-day holding is a **different strategy needing selection
criteria** (which prints "have legs" — likely guidance-driven beats à la
AMD/DELL/SMCI vs sell-the-news pops à la HPE), not a blanket exit change. At
$150–250/position the give-back tail is unacceptable. Exit-at-open stays;
the strategist gets this as a standing research question with the playbook's
runner candidates (AMD, DELL, SMCI, COHR-reversals).

## 4. Actions taken

- **prompts/PLAYBOOK.md** — per-name evidence injected into every analyst and
  strategist mission (policy v0.4.4 requires consulting it).
- No default exit changes: open exit survived a much wider interrogation.
- Standing agenda for the strategist: ORCL hold-to-close variant; runner
  criteria for multi-day holds; BMO premarket window as n grows.

## Caveats

Single regime (AI-cycle bull, Apr–Jun 2026 for intraday; 6 quarters daily).
Megacap (macro_watch) reactions not yet studied — non-tradeable, lower
priority. All of this refreshes automatically as the labeler feeds realized
events into the backtests table; re-run the wide study after the August
cluster.
