# Operator Briefing - 2026-07-27
_Generated 2026-07-27T14:31:43+00:00 (deterministic; built from the store, not model output)._

## Account & risk
- **LIVE - armed until 2026-08-04** (8d left); live caps $250.00/position, $450.00/day
- Account (executor-reported 2026-07-27T13:25:21+00:00): equity $488.32, cash $420.43, buying power $420.43
- Designated account: ••••8223 ('Agentic', cash - T+1/GFV-guarded, no PDT; shorting not enabled)
- Live closes today: 2 | same-day round trips this week: 0
- Today's new exposure: $0.00

## Open positions
- none - holding cash

## Trade history & dataset
- Closed trades: 24 (9 live) | wins 15/24 | total P&L $-15.48
- Decisions by action: {'bearish_option': 15, 'long_equity': 13, 'pass': 11} | labeled passes: 10 | rejected: 1 | exec failures: 3
  - #39 AZN long_equity [closed_live] conv 0.45 policy 0.8.4 → exit 169.89 (+0.48%, P&L $0.19)
  - #38 HOPE long_equity [closed_live] conv 0.48 policy 0.8.4 → exit 13.59 (+0.67%, P&L $0.18)
  - #37 EW long_equity [closed_live] conv 0.53 policy 0.8.3 → exit 88.0 (+5.61%, P&L $1.86)
  - #36 NEM long_equity [closed_live] conv 0.52 policy 0.8.3 → exit 93.04 (-1.22%, P&L $-0.55)
  - #35 SLB pass [pass] conv 0.5 policy 0.8.3 → exit 50.12 (+6.00%, P&L $0.00)
  - #34 INTC pass [pass] conv 0.5 policy 0.8.3 → exit 100.81 (+0.82%, P&L $0.00)
  - #33 NEE bearish_option [closed_paper] conv 0.45 policy 0.8.3 → exit 88.67 (-1.64%, P&L $1.65)
  - #32 VZ long_equity [closed_live] conv 0.5 policy 0.8.3 → exit 44.31 (+1.12%, P&L $0.49)
  - #31 NOK pass [pass] conv 0.5 policy 0.8.2 → exit 10.18 (-1.17%, P&L $0.00)
  - #30 AAL bearish_option [closed_paper] conv 0.55 policy 0.8.2 → exit 13.725 (-6.85%, P&L $3.96)
  - #29 ELS bearish_option [closed_paper] conv 0.5 policy 0.8.2 → exit 65.275 (-0.27%, P&L $0.13)
  - #28 KMI bearish_option [closed_paper] conv 0.5 policy 0.8.2 → exit 32.62 (+0.60%, P&L $-0.62)

## Plan - next 14 days (and why)
- **Next entry session 2026-07-27 ~15:45-15:58 ET** - 65 eligible candidate(s); top 6 by edge rank get the analyst slots:
  - **JBLU** (screened) reports 2026-07-28 bmo: exit post-report open 2026-07-28 09:31
  - **PYPL** (screened) reports 2026-07-28 bmo: exit post-report open 2026-07-28 09:31
  - **GLW** (screened) reports 2026-07-28 bmo: exit post-report open 2026-07-28 09:31
  - **APLD** (screened) reports 2026-07-27 amc: exit same-day ~16:50 if PDT allows, else next open
  - **NVTS** (screened) reports 2026-07-27 amc: exit same-day ~16:50 if PDT allows, else next open
  - **KO** (screened) reports 2026-07-28 bmo: exit post-report open 2026-07-28 09:31
  - below the slot line: ESI, CNP, BCS, RITM, CARR, CNC, IVZ, AMKR, BA, PNR, UPS, UL, GSK, AMT, UDR, WELL, CMS, PCAR, BRO, DINO, RMBS, HLT, SHW, RCL, SPGI, BRX, HAPN, NE, XYL, TRU, AXTA, PFG, ALKS, CDNS, IQV, CLS, NUE, INCY, ECL, ITW, SUI, RGEN, NWBI, TXT, KRC, CDP, DTE, VIV, CINF, UHS, PHG, OSK, SANM, PII, FFIV, HTO, HUBB, CVLT, TIMB
- Further out (slots edge-ranked on the day):
  - entry 2026-07-28: 81 candidate(s) | core: VRT | 74 screened
  - entry 2026-07-29: 85 candidate(s) | 74 screened
  - entry 2026-07-30: 47 candidate(s) | 41 screened
  - entry 2026-07-31: 14 candidate(s) | 4 screened
  - entry 2026-08-03: 33 candidate(s) | 30 screened
  - entry 2026-08-04: 28 candidate(s) | core: ALAB, AMD, ANET | 23 screened
  - entry 2026-08-05: 35 candidate(s) | 31 screened
  - entry 2026-08-06: 26 candidate(s) | 22 screened
  - entry 2026-08-07: 10 candidate(s) | 9 screened
  - entry 2026-08-10: 2 candidate(s) | 2 screened

## System health
- morning tick last ran: 2026-07-27T10:01:54
- afternoon tick last ran: 2026-07-26T15:30:05
- evening tick last ran: 2026-07-26T16:51:35
- ML sidecar: trained (active): 160 rows, CV accuracy 55% vs base rate 49%, as of 2026-07-27T14:01:54+00:00

## Longer-term roadmap status
- Dataset: 24 closed trades + 10 labeled passes | backtests: 1163 historical events
- **ML sidecar (Phase 4)**: pipeline BUILT and self-activating - trains automatically each morning; advisory until ~50 labeled rows
- Phase 2 (deterministic indicators): BUILT - compute_indicators / compute_implied_move run server-side
- Strategy is STOCKS-ONLY (operator decision): live capital goes long equity; bearish theses are paper-only dataset legs (options L2 exists on the account but is deliberately unused)
- Strategist: reviews policy after every 3 new labeled outcomes (auto)

## Steering
- Write standing instructions in **DIRECTIVES.md** - every agent sees them in its context pack on the next run.
- `python -m orchestrator.main report` regenerates this briefing anytime; the morning tick commits it daily.
