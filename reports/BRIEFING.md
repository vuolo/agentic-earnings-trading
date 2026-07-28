# Operator Briefing - 2026-07-28
_Generated 2026-07-28T13:52:08+00:00 (deterministic; built from the store, not model output)._

## Account & risk
- **LIVE - armed until 2026-08-04** (7d left); live caps $250.00/position, $450.00/day
- ⚠️ **Arm expires in 7 day(s)** - re-arm deliberately: `python -m orchestrator.main arm-live --confirm ...`
- Account (executor-reported 2026-07-28T13:24:57+00:00): equity $489.16, cash $444.44, buying power $444.44
- Designated account: ••••8223 ('Agentic', cash - T+1/GFV-guarded, no PDT; shorting not enabled)
- Live closes today: 2 | same-day round trips this week: 0
- Today's new exposure: $0.00

## Open positions
- none - holding cash

## Trade history & dataset
- Closed trades: 28 (11 live) | wins 18/28 | total P&L $-11.58
- Decisions by action: {'bearish_option': 17, 'long_equity': 15, 'pass': 13} | labeled passes: 12 | rejected: 1 | exec failures: 3
  - #45 KO bearish_option [closed_paper] conv 0.5 policy 0.8.5 → exit 89.18 (+6.19%, P&L $-1.86)
  - #44 NVTS pass [pass] conv 0.5 policy 0.8.5 → exit 9.74 (-14.75%, P&L $0.00)
  - #43 PYPL pass [pass] conv 0.52 policy 0.8.5 → exit 58.22 (+3.73%, P&L $0.00)
  - #42 APLD long_equity [closed_live] conv 0.52 policy 0.8.5 → exit 26.81 (+1.99%, P&L $0.43)
  - #41 GLW bearish_option [closed_paper] conv 0.52 policy 0.8.5 → exit 120.4009 (-15.29%, P&L $4.49)
  - #40 JBLU long_equity [closed_live] conv 0.52 policy 0.8.5 → exit 5.62 (+3.88%, P&L $0.84)
  - #39 AZN long_equity [closed_live] conv 0.45 policy 0.8.4 → exit 169.89 (+0.48%, P&L $0.19)
  - #38 HOPE long_equity [closed_live] conv 0.48 policy 0.8.4 → exit 13.59 (+0.67%, P&L $0.18)
  - #37 EW long_equity [closed_live] conv 0.53 policy 0.8.3 → exit 88.0 (+5.61%, P&L $1.86)
  - #36 NEM long_equity [closed_live] conv 0.52 policy 0.8.3 → exit 93.04 (-1.22%, P&L $-0.55)
  - #35 SLB pass [pass] conv 0.5 policy 0.8.3 → exit 50.12 (+6.00%, P&L $0.00)
  - #34 INTC pass [pass] conv 0.5 policy 0.8.3 → exit 100.81 (+0.82%, P&L $0.00)

## Plan - next 14 days (and why)
- **Next entry session 2026-07-28 ~15:45-15:58 ET** - 126 eligible candidate(s); top 6 by edge rank get the analyst slots:
  - **VRT** (core) reports 2026-07-29 bmo: exit post-report open 2026-07-29 09:31
  - **OMC** (screened) reports 2026-07-28 amc: exit same-day ~16:50 if PDT allows, else next open
  - **SOFI** (screened) reports 2026-07-29 bmo: exit post-report open 2026-07-29 09:31
  - **F** (screened) reports 2026-07-28 amc: exit same-day ~16:50 if PDT allows, else next open
  - **UMC** (screened) reports 2026-07-29 bmo: exit post-report open 2026-07-29 09:31
  - **BSX** (screened) reports 2026-07-29 bmo: exit post-report open 2026-07-29 09:31
  - below the slot line: BE, CTSH, KLAC, MDLZ, AVTR, PG, V, APH, CSGP, VFC, CVE, GEHC, SWKS, JCI, TEVA, IONS, HBM, SW, CZR, ARCC, STX, OI, MIR, FLEX, ULCC, EXE, ENPH, FE, NXPI, TER, PUMP, BANC, HAYW, VRSK, NOV, NEO, ACHC, ETR, FTV, BTU, DB, WM, ADP, EXLS, ACGL, GTX, OPCH, CBRE, MAS, STAG, WEC, UBS, ODFL, VRNS, AON, BIIB, VLTO, HUM, SLGN, CAKE, LMND, PPG, HIW, GD, AKR, BSBR, OGE, WERN, WPC, BXP, SWK, CGAU, UNM, NMRK, FTRE, EXR, LXP, QURE, AXGN, WING, LOGI, SLDE, SMG, SBCF, REYN, ZWS, BG, QRVO, BAND, GRMN, OMF, APAM, MEOH, NMR, VMC, PSN, PB, IART, BUSE, MCHB, AER, FCF, GNRC, CFFN, EDU, OSW, MANH, IEX, CAR, BLKB, CHEF, AXS, PAG, PDM, SITE, RNST, UMBF, ASH, KEX, CR
- Further out (slots edge-ranked on the day):
  - entry 2026-07-29: 257 candidate(s) | 193 screened
  - entry 2026-07-30: 137 candidate(s) | 103 screened
  - entry 2026-07-31: 14 candidate(s) | 4 screened
  - entry 2026-08-03: 33 candidate(s) | 30 screened
  - entry 2026-08-04: 28 candidate(s) | core: ALAB, AMD, ANET | 23 screened
  - entry 2026-08-05: 35 candidate(s) | 32 screened
  - entry 2026-08-06: 26 candidate(s) | 22 screened
  - entry 2026-08-07: 10 candidate(s) | 8 screened
  - entry 2026-08-10: 2 candidate(s) | 1 screened

## System health
- morning tick last ran: 2026-07-27T10:01:54
- afternoon tick last ran: 2026-07-27T15:44:54
- evening tick last ran: 2026-07-27T16:50:54
- ML sidecar: trained (active): 168 rows, CV accuracy 51% vs base rate 50%, as of 2026-07-28T13:52:08+00:00

## Longer-term roadmap status
- Dataset: 28 closed trades + 12 labeled passes | backtests: 1203 historical events
- **ML sidecar (Phase 4)**: pipeline BUILT and self-activating - trains automatically each morning; advisory until ~50 labeled rows
- Phase 2 (deterministic indicators): BUILT - compute_indicators / compute_implied_move run server-side
- Strategy is STOCKS-ONLY (operator decision): live capital goes long equity; bearish theses are paper-only dataset legs (options L2 exists on the account but is deliberately unused)
- Strategist: reviews policy after every 3 new labeled outcomes (auto)

## Steering
- Write standing instructions in **DIRECTIVES.md** - every agent sees them in its context pack on the next run.
- `python -m orchestrator.main report` regenerates this briefing anytime; the morning tick commits it daily.
