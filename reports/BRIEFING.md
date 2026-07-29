# Operator Briefing - 2026-07-29
_Generated 2026-07-29T13:55:20+00:00 (deterministic; built from the store, not model output)._

## Account & risk
- **LIVE - armed until 2026-08-04** (6d left); live caps $250.00/position, $450.00/day
- ⚠️ **Arm expires in 6 day(s)** - re-arm deliberately: `python -m orchestrator.main arm-live --confirm ...`
- Account (executor-reported 2026-07-29T13:25:07+00:00): equity $485.26, cash $427.63, buying power $427.63
- Designated account: ••••8223 ('Agentic', cash - T+1/GFV-guarded, no PDT; shorting not enabled)
- Live closes today: 2 | same-day round trips this week: 0
- Today's new exposure: $0.00

## Open positions
- none - holding cash

## Trade history & dataset
- Closed trades: 33 (13 live) | wins 20/33 | total P&L $-10.91
- Decisions by action: {'bearish_option': 21, 'long_equity': 17, 'pass': 13} | labeled passes: 13 | rejected: 2 | exec failures: 3
  - #51 UMC bearish_option [rejected] conv 0.5 policy 0.8.6
  - #50 BSX long_equity [closed_live] conv 0.5 policy 0.8.6 → exit 42.67 (-7.84%, P&L $-2.06)
  - #49 OMC long_equity [closed_live] conv 0.45 policy 0.8.6 → exit 83.63 (-2.65%, P&L $-0.93)
  - #48 VRT bearish_option [closed_paper] conv 0.52 policy 0.8.6 → exit 238.335 (-11.17%, P&L $2.53)
  - #47 SOFI bearish_option [closed_paper] conv 0.5 policy 0.8.6 → exit 15.0581 (-9.40%, P&L $2.78)
  - #46 F bearish_option [closed_paper] conv 0.5 policy 0.8.6 → exit 15.715 (+5.47%, P&L $-1.64)
  - #45 KO bearish_option [closed_paper] conv 0.5 policy 0.8.5 → exit 89.18 (+6.19%, P&L $-1.86)
  - #44 NVTS pass [pass] conv 0.5 policy 0.8.5 → exit 9.74 (-14.75%, P&L $0.00)
  - #43 PYPL pass [pass] conv 0.52 policy 0.8.5 → exit 58.22 (+3.73%, P&L $0.00)
  - #42 APLD long_equity [closed_live] conv 0.52 policy 0.8.5 → exit 26.81 (+1.99%, P&L $0.43)
  - #41 GLW bearish_option [closed_paper] conv 0.52 policy 0.8.5 → exit 120.4009 (-15.29%, P&L $4.49)
  - #40 JBLU long_equity [closed_live] conv 0.52 policy 0.8.5 → exit 5.62 (+3.88%, P&L $0.84)

## Plan - next 14 days (and why)
- **Next entry session 2026-07-29 ~15:45-15:58 ET** - 214 eligible candidate(s); top 6 by edge rank get the analyst slots:
  - **HOOD** (screened) reports 2026-07-29 amc: exit same-day ~16:50 if PDT allows, else next open
  - **AUR** (screened) reports 2026-07-29 amc: exit same-day ~16:50 if PDT allows, else next open
  - **STLA** (screened) reports 2026-07-30 bmo: exit post-report open 2026-07-30 09:31
  - **CMG** (screened) reports 2026-07-29 amc: exit same-day ~16:50 if PDT allows, else next open
  - **LYG** (screened) reports 2026-07-30 bmo: exit post-report open 2026-07-30 09:31
  - **OWL** (screened) reports 2026-07-30 bmo: exit post-report open 2026-07-30 09:31
  - below the slot line: BMY, QCOM, LRCX, CLBK, ASX, NCLH, CCC, ORLY, AG, EXC, CVNA, PTEN, MO, BFLY, VICI, KGC, ADT, ARM, SBUX, SHEL, EXK, SO, FTNT, IP, AEP, COUR, BAX, ICE, XEL, KKR, BTI, TAK, CRH, TDOC, AR, INVH, AGI, SOLS, TENB, MFG, VLO, FMC, TAL, PBF, MGM, SIRI, EPD, MA, YUM, FTI, PCOR, VTR, ADPT, TRP, LKQ, KRG, RSI, APG, CNK, CWH, AEM, CRK, CP, NEXT, LTH, MAIR, TTEK, WAY, HSY, EA, ING, SONO, PEB, BGC, GFL, PGY, BUD, BLDR, SFM, WVE, ALGM, VKTX, MTG, AM, OHI, AWK, UNIT, FLS, CI, MOD, DAR, AMRX, CHRW, CNX, LNC, AOS, MT, VET, FORM, YUMC, PPC, APD, BXMT, PMT, LHX, PRCH, NEOG, PWR, ABTC, ST, PBI, PTC, ESRT, FTAI, RAL, GIL, BNL, ALNY, ARIS, TT, KBR, PSA, REG, VIRT, RES, TW, CHKP, MAX, CORT, TEX, SCI, LAUR, HXL, SXC, BBNX, MAA, OBE, ALKT, AGIO, FBRT, PFS, HGV, PHAT, REGN, UPBD, STGW, DRS, EFOR, FJTSY, MTH, CNMD, XPO, RTO, CVI, GVA, QTWO, LH, CROX, HLI, SHOO, WHD, ADAM, ALGN, CLB, NSP, BBT, DTM, MC, AVY, LXU, AGCO, CHDN, H, ARXS, LSPD, SIMO, OMCL, WWD, FCPT, BC, CBZ, GOOS, WCC, NPKI, SPNT, NFG, EQIX, TYL, TRN, CFR, BOOT, ICLR, PATK, EPR, TK, OIS, PIPR, CRS, AMCX, BDC, HNI, CMCO, EME, EEFT, TIMB, XHR, SPHR, BHE
- Further out (slots edge-ranked on the day):
  - entry 2026-07-30: 165 candidate(s) | 110 screened
  - entry 2026-07-31: 34 candidate(s) | 16 screened
  - entry 2026-08-03: 208 candidate(s) | 129 screened
  - entry 2026-08-04: 173 candidate(s) | core: ALAB, AMD, ANET | 110 screened
  - entry 2026-08-05: 37 candidate(s) | 33 screened
  - entry 2026-08-06: 26 candidate(s) | 19 screened
  - entry 2026-08-07: 10 candidate(s) | 3 screened
  - entry 2026-08-10: 9 candidate(s) | 4 screened
  - entry 2026-08-11: 7 candidate(s) | core: SMCI | 5 screened

## System health
- morning tick last ran: 2026-07-28T09:52:08
- afternoon tick last ran: 2026-07-28T15:44:17
- evening tick last ran: 2026-07-28T16:50:46
- ML sidecar: trained (active): 174 rows, CV accuracy 54% vs base rate 49%, as of 2026-07-29T13:55:20+00:00

## Longer-term roadmap status
- Dataset: 33 closed trades + 13 labeled passes | backtests: 1231 historical events
- **ML sidecar (Phase 4)**: pipeline BUILT and self-activating - trains automatically each morning; advisory until ~50 labeled rows
- Phase 2 (deterministic indicators): BUILT - compute_indicators / compute_implied_move run server-side
- Strategy is STOCKS-ONLY (operator decision): live capital goes long equity; bearish theses are paper-only dataset legs (options L2 exists on the account but is deliberately unused)
- Strategist: reviews policy after every 3 new labeled outcomes (auto)

## Steering
- Write standing instructions in **DIRECTIVES.md** - every agent sees them in its context pack on the next run.
- `python -m orchestrator.main report` regenerates this briefing anytime; the morning tick commits it daily.
