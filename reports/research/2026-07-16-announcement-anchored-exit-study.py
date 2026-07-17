"""Announcement-anchored exit study (operator question, 2026-07-16).

Hypothesis under test (operator): selling shortly AFTER the earnings print
lands (AMC ~16:20 for a 16:15 report; BMO ~07:20 premarket for a 07:15
report) beats the current next-open auction exit, and prior studies did not
properly examine after-hours / premarket bars.

Method: real extended-hours bars (Robinhood historicals, bounds=extended)
on report evenings (5-min, 16:05-17:35 ET bar closes) and report premarkets
(10-min, 06:10-09:30 ET bar closes) for every backtests-table event
2026-04-15..2026-07-16 with recorded pre_close/post_open. The print bar is
DETECTED from the price path (first bar-over-bar move > 0.8%), so exits are
anchored to the actual announcement, not the clock - exactly the operator's
proposed rule. Entry basis = pre_close (the ~15:55 entry). LONG framing
throughout (higher exit = better), matching the earlier studies.

Events whose extended-session tape was too thin to execute against (mostly
interpolated bars / a few hundred shares per print) are EXCLUDED from exit
stats and counted separately - an exit you cannot fill is not an exit.

Data collected 2026-07-16 evening via mcp robinhood get_equity_historicals;
arrays are bar CLOSES in ET order. Reproduce by re-fetching the same windows.
"""
import sqlite3

# ---- AMC report evenings: 19 five-minute bar closes, 16:05 -> 17:35 ET ----
AMC = {
 ("NFLX","2026-04-16"): [102.83,98.12,97.97,98.13,98.1044,99.30,98.96,98.94,99.13,98.4803,98.6298,99.01,98.68,98.2394,98.25,98.40,98.29,98.40,98.0813],
 ("AA","2026-04-16"):   [70.60,71.00,66.07,66.30,66.30,67.3399,70.41,67.38,67.79,67.75,67.30,68.10,68.13,67.591,67.7825,68.00,67.76,67.99,67.90],
 ("UAL","2026-04-21"):  [97.3648,96.669,95.40,96.20,96.50,96.30,96.35,98.50,97.50,97.26,98.10,98.01,98.03,98.00,98.10,97.91,98.00,98.02,98.0025],
 ("AMD","2026-05-05"):  [356.43,355.00,355.51,360.17,371.00,379.7825,374.3042,374.1901,373.26,369.97,371.53,370.8355,372.9828,377.12,378.1216,384.00,382.70,382.45,382.33],
 ("SMCI","2026-05-05"): [28.05,29.75,31.8705,31.0873,32.01,32.885,32.40,33.01,32.5948,32.64,32.63,32.6052,32.72,32.7278,32.63,33.60,33.3174,33.4999,33.70],
 ("ANET","2026-05-05"): [170.261,154.00,160.9633,168.42,162.4447,162.82,163.00,162.4437,158.00,150.60,147.5863,145.15,147.05,147.85,146.61,147.25,147.04,147.039,147.00],
 ("ALAB","2026-05-05"): [214.00,233.00,224.99,219.49,221.00,226.5133,221.00,216.99,217.00,218.00,219.75,216.00,219.00,221.52,220.00,219.00,220.00,218.00,218.50],
 ("COHR","2026-05-06"): [344.76,323.74,321.55,318.88,320.20,320.50,325.50,321.00,320.85,317.60,317.50,318.13,318.01,317.00,316.7295,315.50,313.21,312.58,313.14],
 ("NVDA","2026-05-20"): [223.86,224.02,223.90,224.24,223.00,226.5752,222.72,222.174,223.053,222.72,221.73,222.46,222.2525,220.94,220.85,220.99,222.68,223.16,222.72],
 ("MRVL","2026-05-27"): [198.90,204.93,201.00,211.3801,207.183,207.0001,208.30,211.50,216.00,215.64,209.1603,210.00,203.6417,192.50,194.41,201.46,201.39,202.98,202.27],
 ("DELL","2026-05-28"): [319.87,332.10,345.50,364.8155,362.2361,370.9064,365.21,372.00,371.8208,370.723,377.832,389.25,388.00,394.00,397.52,401.2769,407.61,412.99,410.08],
 ("HPE","2026-06-01"):  [47.7777,57.5561,64.0117,60.50,61.30,61.23,60.8487,61.11,62.38,63.824,63.7986,63.89,64.52,64.29,64.1888,64.56,63.9603,64.0209,64.95],
 ("CRDO","2026-06-01"): [229.94,193.2802,192.00,199.54,199.90,201.0652,202.4625,203.00,201.45,201.9562,203.4258,204.764,202.00,201.00,198.5001,197.9443,201.2089,201.7498,204.82],
 ("AVGO","2026-06-03"): [480.46,478.13,476.30,450.00,462.50,455.32,453.08,451.00,442.598,446.104,448.87,450.60,448.44,437.636,417.45,427.1738,424.37,417.00,412.81],
 ("ORCL","2026-06-10"): [201.7571,198.48,196.39,198.96,195.30,191.52,193.44,193.8664,191.85,190.10,189.8999,187.50,185.95,186.80,187.10,186.5002,185.731,190.7455,189.01],
 ("MU","2026-06-24"):   [1101.99,1158.76,1149.00,1147.52,1178.71,1190.14,1168.54,1194.84,1207.7546,1213.5501,1205.41,1200.80,1194.91,1190.36,1180.8791,1173.99,1168.82,1192.02,1181.00],
 ("PENG","2026-07-07"): [63.3791,69.43,67.75,68.04,68.40,67.00,66.93,67.60,67.40,67.36,67.4523,67.35,67.50,67.69,68.00,67.16,64.5001,66.45,65.70],
 ("LEVI","2026-07-08"): [24.45,24.50,23.4246,23.1428,23.28,23.09,23.00,23.11,23.00,23.02,22.9938,23.08,23.20,23.1065,23.1499,23.07,23.0901,23.03,23.00],
 ("WDFC","2026-07-09"): [238.00,268.00,269.94,270.9832,273.0515,273.305,272.1395,272.1395,273.0655,275.75,274.00,272.00,272.00,272.00,272.00,272.00,272.00,274.815,273.32],
 ("UAL","2026-07-15"):  [117.8605,116.40,116.6034,115.80,116.38,117.24,117.50,117.45,117.50,119.0014,118.3525,118.07,118.25,118.45,118.10,118.67,118.54,118.1701,117.8859],
}
# AH tape too thin to execute a $75-250 exit reliably (mostly interpolated
# bars / isolated odd-lot prints): the announcement-anchored AH exit is
# structurally UNAVAILABLE for these - counted, not averaged.
AMC_THIN = [("AZZ","2026-04-22"), ("SAR","2026-05-05"), ("EPAC","2026-07-07"),
            ("KRUS","2026-07-07"), ("SAR","2026-07-07"), ("AZZ","2026-07-08"),
            ("PSMT","2026-07-08"), ("SLP","2026-07-09")]

# ---- BMO report premarkets: 21 ten-minute bar closes, 06:10 -> 09:30 ET ----
BMO = {
 ("BAC","2026-04-15"):  [53.60,53.23,53.53,53.78,53.87,53.97,53.8008,53.9999,53.90,53.98,53.84,53.78,53.8153,53.90,53.88,54.1482,54.25,54.19,54.45,54.54,54.50],
 ("MS","2026-04-15"):   [183.00,183.40,183.40,183.40,182.8766,183.81,183.3915,183.3901,185.1642,187.00,188.09,188.40,188.30,189.00,188.1522,188.75,188.65,188.36,189.00,188.40,189.14],
 ("TSM","2026-04-16"):  [373.62,370.89,367.80,365.00,363.50,368.00,366.90,366.99,366.94,368.06,368.50,371.20,370.3828,368.1529,370.44,367.77,367.43,367.9453,370.1801,370.84,369.24],
 ("PEP","2026-04-16"):  [154.24,153.75,154.06,155.50,155.78,156.40,156.19,157.37,156.54,156.4799,156.47,156.53,156.00,156.30,156.12,155.00,155.2675,155.00,156.25,155.80,155.80],
 ("ABT","2026-04-16"):  [102.50,102.96,102.96,101.80,102.96,102.96,101.92,102.20,102.00,98.50,97.1472,97.60,97.99,97.00,97.4003,97.2658,96.48,96.97,97.0785,97.70,96.75],
 ("ERIC","2026-04-17"): [12.14,12.12,12.13,12.0515,12.0515,12.10,12.12,11.98,11.94,11.93,11.96,11.91,12.00,12.07,12.0013,12.00,12.03,12.05,12.24,12.2214,12.13],
 ("UNH","2026-04-21"):  [341.45,342.9006,342.00,343.42,345.20,344.00,346.80,346.3164,346.8699,346.10,346.44,346.28,348.8384,347.70,347.1771,347.6344,347.2403,348.122,349.30,349.40,353.50],
 ("VRT","2026-04-22"):  [294.00,300.82,299.16,301.21,301.04,299.40,298.00,298.216,297.51,298.3231,297.50,297.46,298.20,306.00,309.7426,310.12,306.21,302.00,305.99,304.73,307.00],
 ("BYRN","2026-07-09"): [6.18,6.18,6.23,6.23,6.23,6.23,6.23,6.23,6.23,6.23,6.2296,6.2296,4.36,4.55,4.5709,4.60,4.50,4.46,4.44,4.61,4.70],
 ("PEP","2026-07-09"):  [144.30,144.00,142.45,140.12,140.75,141.22,141.574,141.00,141.50,140.3984,140.25,139.82,139.90,139.7999,139.354,139.02,138.3917,138.90,137.94,137.87,136.97],
 ("SMPL","2026-07-09"): [13.07,13.07,13.07,13.07,13.07,13.07,14.73,14.84,14.5201,14.6102,14.9871,14.51,14.53,14.76,14.71,14.51,14.81,15.10,15.35,15.51,15.01],
 ("DAL","2026-07-10"):  [89.25,88.47,89.00,90.71,90.70,89.90,89.4203,87.12,86.50,85.99,88.25,87.94,87.00,87.97,88.40,88.00,88.55,88.90,88.88,88.60,86.9291],
 ("CAG","2026-07-15"):  [14.14,14.14,14.14,14.14,14.14,14.14,14.12,14.0709,14.1207,13.7993,13.7204,13.6509,13.50,13.52,13.34,13.3093,13.39,13.38,13.32,13.324,13.69],
 ("TSM","2026-07-16"):  [403.22,403.04,403.02,402.00,400.71,402.25,399.32,397.79,399.69,399.99,398.44,399.50,398.60,401.00,403.00,401.80,400.61,402.80,403.25,403.84,405.88],
}
# Premarket tape too thin to execute against before ~09:20 (regional banks
# and small caps: isolated odd-lot prints on a session Robinhood only opens
# to us at 07:00, whole shares only).
BMO_THIN = [("FHN","2026-04-15"), ("PGR","2026-04-15"), ("BNY","2026-04-16"),
            ("CFG","2026-04-16"), ("USB","2026-04-16"), ("FITB","2026-04-17"),
            ("RF","2026-04-17"), ("TFC","2026-04-17"), ("HELE","2026-04-23"),
            ("HELE","2026-07-08")]

AMC_LBL = [f"{16 + (5*(i+1))//60}:{(5+5*i) % 60:02d}" for i in range(19)]   # 16:05..17:35
BMO_LBL = [f"{6 + (10*(i+1))//60}:{(10+10*i) % 60:02d}" for i in range(21)]  # 06:10..09:30

db = sqlite3.connect("datasets/earnings.sqlite3"); db.row_factory = sqlite3.Row

def ref(sym, rd):
    r = db.execute("SELECT pre_close, post_open FROM backtests WHERE symbol=? AND report_date=?",
                   (sym, rd)).fetchone()
    return float(r["pre_close"]), float(r["post_open"])

def detect_print(closes, pre_close, thresh=0.8):
    """First bar whose close moved > thresh% vs the prior close (prior =
    pre_close for the first bar). Returns index or None."""
    prev = pre_close
    for i, c in enumerate(closes):
        if abs(c / prev - 1) * 100 > thresh:
            return i
        prev = c
    return None

def pct(a, b): return (a / b - 1) * 100

def study(events, labels, fixed_idx, anchor_offsets, first_tradeable_idx, title):
    rows, no_print = [], []
    for (sym, rd), closes in sorted(events.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        pre, nxt = ref(sym, rd)
        p = detect_print(closes, pre)
        open_ret = pct(nxt, pre)
        r = {"sym": sym, "rd": rd, "open": open_ret, "print": p}
        for name, off in anchor_offsets.items():
            if p is None:
                r[name] = None
            else:
                j = min(max(p + off, first_tradeable_idx), len(closes) - 1)
                r[name] = pct(closes[j], pre)
        for name, j in fixed_idx.items():
            r[name] = pct(closes[j], pre)
        (rows if p is not None else no_print).append(r)
    cols = list(anchor_offsets) + list(fixed_idx)
    print(f"\n=== {title} (n={len(rows)} with detectable print; "
          f"{len(no_print)} without) ===")
    print(f"{'sym':6}{'date':12}{'print@':8}" + "".join(f"{c:>10}" for c in cols) + f"{'next-open':>11}")
    for r in rows:
        lab = labels[r["print"]]
        print(f"{r['sym']:6}{r['rd']:12}{lab:8}" +
              "".join(f"{r[c]:10.2f}" for c in cols) + f"{r['open']:11.2f}")
    print("-" * (26 + 10 * len(cols) + 11))
    avg = lambda k: sum(r[k] for r in rows) / len(rows)
    print(f"{'AVG':26}" + "".join(f"{avg(c):10.2f}" for c in cols) + f"{avg('open'):11.2f}")
    for c in cols:
        diffs = [r[c] - r["open"] for r in rows]
        wins = sum(d > 0 for d in diffs)
        print(f"  exit {c:<12} vs next-open: avg {sum(diffs)/len(diffs):+6.2f}% | better in {wins}/{len(rows)}")
    losers = [r for r in rows if r["open"] < 0]
    if losers:
        print(f"  LOSERS only (next-open < 0, n={len(losers)}):")
        for c in cols:
            diffs = [r[c] - r["open"] for r in losers]
            wins = sum(d > 0 for d in diffs)
            print(f"    exit {c:<12} vs next-open: avg {sum(diffs)/len(diffs):+6.2f}% | better in {wins}/{len(losers)}")
    if no_print:
        print("  no detectable print in window: " + ", ".join(f"{r['sym']} {r['rd']}" for r in no_print))
    return rows

print(f"Universe: {len(AMC)+len(AMC_THIN)} AMC evenings, {len(BMO)+len(BMO_THIN)} BMO premarkets")
print(f"Structurally UNEXITABLE extended-session tapes: "
      f"{len(AMC_THIN)}/{len(AMC)+len(AMC_THIN)} AMC, {len(BMO_THIN)}/{len(BMO)+len(BMO_THIN)} BMO")
print("  AMC thin: " + ", ".join(f"{s} {d}" for s, d in AMC_THIN))
print("  BMO thin: " + ", ".join(f"{s} {d}" for s, d in BMO_THIN))

# AMC: anchored exits print+5/15/30m; fixed 16:20 / 16:50 / 17:35.
study(AMC, AMC_LBL,
      fixed_idx={"@16:20": 3, "@16:50": 9, "@17:35": 18},
      anchor_offsets={"print+5m": 1, "print+15m": 3, "print+30m": 6},
      first_tradeable_idx=0,
      title="AMC: long %-return from pre-close entry at each exit")

# BMO: anchored print+10/30m clamped to 07:00 ET (Robinhood premarket opens
# 07:00; index 5 closes 07:00, so first executable close is index 6 = 07:10);
# fixed 07:20 / 08:00 / 09:00 / 09:30(last premarket print).
study(BMO, BMO_LBL,
      fixed_idx={"@07:20": 7, "@08:00": 11, "@09:00": 17, "@09:30pm": 20},
      anchor_offsets={"print+10m": 1, "print+30m": 3},
      first_tradeable_idx=6,
      title="BMO: long %-return from T-1-close entry at each exit")

# How much of the overnight move had printed by print+15m (AMC)?
print("\n=== AMC: fraction of the overnight move already priced at print+15m ===")
for (sym, rd), closes in sorted(AMC.items(), key=lambda kv: (kv[0][1], kv[0][0])):
    pre, nxt = ref(sym, rd)
    p = detect_print(closes, pre)
    if p is None or abs(pct(nxt, pre)) < 0.5:
        continue
    j = min(p + 3, len(closes) - 1)
    print(f"{sym:6}{rd:12}{pct(closes[j], pre)/pct(nxt, pre)*100:6.0f}%  (overnight {pct(nxt, pre):+.2f}%)")
