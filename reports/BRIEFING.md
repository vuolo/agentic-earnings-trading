# Operator Briefing — 2026-07-05
_Generated 2026-07-06T02:11:14+00:00 (deterministic; built from the store, not model output)._

## Account & risk
- **LIVE — armed until 2026-08-04** (30d left); live caps $250.00/position, $450.00/day
- Account (executor-reported 2026-07-06T02:11:11+00:00): equity $500.00, cash $500.00, buying power $500.00
- Designated account: ••••8223 ('Agentic', cash — T+1/GFV-guarded, no PDT; shorting not enabled)
- Live closes today: 0 | same-day round trips this week: 0
- Today's new exposure: $0.00

## Open positions
- none — holding cash

## Trade history & dataset
- Closed trades: none yet
- Decisions by action: {'pass': 1} | labeled passes: 0 | rejected: 0 | exec failures: 0
  - #1 TSM pass [pass] conv 0.3 policy 0.1.0

## Plan — next 14 days (and why)
- **TSM** reports 2026-07-16 bmo: analyst+entry 2026-07-15 ~15:40-15:58 ET, exit post-report open 2026-07-16 09:31 (already decided) — window per backtest gap stats (see `get_backtest_summary`)

## System health
- morning tick last ran: 2026-07-05T22:10:05
- afternoon tick last ran: never
- evening tick last ran: never
- ML sidecar: accumulating dataset (0/25 usable labeled rows)

## Longer-term roadmap status
- Dataset: 0 closed trades + 0 labeled passes | backtests: 90 historical events
- **ML sidecar (Phase 4)**: pipeline BUILT and self-activating — trains automatically each morning; advisory until ~50 labeled rows
- Phase 2 (deterministic indicators): BUILT — compute_indicators / compute_implied_move run server-side
- Strategy is STOCKS-ONLY (operator decision): live capital goes long equity; bearish theses are paper-only dataset legs (options L2 exists on the account but is deliberately unused)
- Strategist: reviews policy after every 3 new labeled outcomes (auto)

## Steering
- Write standing instructions in **DIRECTIVES.md** — every agent sees them in its context pack on the next run.
- `python -m orchestrator.main report` regenerates this briefing anytime; the morning tick commits it daily.
