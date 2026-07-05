# Operator Briefing — 2026-07-05
_Generated 2026-07-05T23:32:27+00:00 (deterministic; built from the store, not model output)._

## Account & risk
- **LIVE — armed until 2026-08-04** (30d left); live caps $120.00/position, $140.00/day
- Account: no snapshot yet (first executor run reports it)
- PDT: 0/3 same-day live round trips used (trailing week)
- Today's new exposure: $0.00

## Open positions
- none — holding cash

## Trade history & dataset
- Closed trades: none yet
- Decisions by action: {'pass': 1} | labeled passes: 0 | rejected: 0 | exec failures: 0
  - #1 TSM pass [pass] conv 0.3 policy 0.1.0

## Plan — next 14 days (and why)
- **TSM** reports 2026-07-16 bmo: analyst+entry 2026-07-15 ~15:40-15:58 ET, exit post-report open 2026-07-16 09:31 — window per backtest gap stats (see `get_backtest_summary`)

## Longer-term roadmap status
- Dataset: 0 closed trades + 0 labeled passes | backtests: 90 historical events
- **ML sidecar (Phase 4)**: trains when ~50 labeled trade outcomes exist — until then every decision/pass/outcome is training data
- Phase 2 (deterministic feature/indicator engine): NEXT BUILD — moves implied-move/indicator math from agent arithmetic into tested code
- Phase 5b (live options for bearish leg): after Phase 2
- Strategist: reviews policy after every 3 new labeled outcomes (auto)

## Steering
- Write standing instructions in **DIRECTIVES.md** — every agent sees them in its context pack on the next run.
- `python -m orchestrator.main report` regenerates this briefing anytime; the morning tick commits it daily.
