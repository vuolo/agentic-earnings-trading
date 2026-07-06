"""Intraday exit-timing study: 15 universe earnings reactions, Apr-Jun 2026.
Data: 5-min bars 9:30-10:05 ET + hourly closes 11:00-16:00 ET (Robinhood MCP),
joined to stored pre-report closes. Perspective: LONG entered at T-1 close."""
import sqlite3

# (symbol, backtest report_date) -> open price + closes at checkpoints
# checkpoints: minutes after open: 5,10,15,20,25,30,35, then 90,150,210,270,330,389(close)
DATA = {
 ("TSM","2026-04-16"): (368.86, [368.605,368.475,366.845,366.605,363.87,365.48,367.0224, 365.8685,365.625,365.52,362.4051,362.9342,363.2497]),
 ("VRT","2026-04-22"): (305.32, [307.535,304.19,312.065,305.53,306.40,305.2452,300.56, 304.05,305.565,302.915,301.6399,305.37,305.77]),
 ("AMD","2026-05-05"): (409.26, [426.80,423.27,428.19,421.11,417.695,411.4501,410.2001, 409.64,413.9983,412.78,414.3401,419.66,421.3001]),
 ("SMCI","2026-05-05"): (31.50, [31.5899,32.83,33.145,32.69,33.09,32.4352,32.53, 31.885,31.93,32.0701,32.71,33.945,34.65]),
 ("ANET","2026-05-05"): (152.75, [152.91,150.34,150.76,148.0597,148.21,146.89,147.9287, 148.57,144.375,142.255,141.82,141.90,147.07]),
 ("ALAB","2026-05-05"): (229.65, [215.91,214.76,214.841,210.33,211.3104,206.08,205.98, 204.40,206.37,204.77,207.04,208.60,214.01]),
 ("COHR","2026-05-06"): (329.01, [331.87,321.665,322.075,327.42,324.805,322.635,324.28, 327.67,323.19,321.35,316.415,308.5101,309.70]),
 ("NVDA","2026-05-20"): (222.33, [227.0999,223.175,223.87,221.9001,222.6772,222.26,224.10, 223.53,219.55,220.1401,220.915,219.06,219.50]),
 ("MRVL","2026-05-27"): (198.75, [202.04,201.2099,205.03,201.49,202.9801,202.275,199.4299, 202.46,199.375,204.85,205.29,206.575,202.14]),
 ("DELL","2026-05-28"): (417.48, [416.07,417.70,422.155,424.6944,425.705,421.505,421.595, 405.50,417.81,407.64,407.805,416.445,421.10]),
 ("HPE","2026-06-01"): (63.12, [62.33,59.8044,58.5896,59.26,58.4201,58.75,58.625, 59.16,59.02,54.605,54.345,54.9264,56.15]),
 ("CRDO","2026-06-01"): (219.055, [239.65,224.035,217.54,219.61,217.80,216.51,212.255, 218.4399,223.70,221.6325,221.48,228.24,229.005]),
 ("AVGO","2026-06-03"): (408.75, [410.385,408.2594,403.715,404.3243,405.94,404.045,405.89, 408.17,408.185,414.04,423.63,416.25,419.03]),
 ("ORCL","2026-06-10"): (179.5975, [176.32,176.795,176.5351,178.085,179.7793,180.19,180.7701, 177.88,177.365,175.955,178.49,182.04,183.83]),
 ("MU","2026-06-24"): (1234.49, [1250.44,1248.17,1216.695,1195.1701,1147.44,1138.24,1146.215, 1164.56,1178.4951,1217.16,1236.91,1228.445,1199.98]),
}
LABELS = ["9:35","9:40","9:45","9:50","9:55","10:00","10:05","11:00","12:00","13:00","14:00","15:00","close"]

db = sqlite3.connect("datasets/earnings.sqlite3"); db.row_factory = sqlite3.Row
events = []
for (sym, rd), (op, closes) in DATA.items():
    row = db.execute("SELECT pre_close FROM backtests WHERE symbol=? AND report_date=?", (sym, rd)).fetchone()
    pre = float(row["pre_close"])
    gap = (op - pre) / pre * 100
    path = [(c - op) / op * 100 for c in closes]          # % from the 9:30 open
    total = [(c - pre) / pre * 100 for c in closes]        # % from T-1 close (long P&L)
    events.append((sym, gap, path, total))

def avg(v): return sum(v) / len(v)

print(f"{'sym':6}{'gap%':>8}" + "".join(f"{l:>8}" for l in LABELS) + "   (from-open %)")
for sym, gap, path, _ in sorted(events, key=lambda e: -abs(e[1])):
    print(f"{sym:6}{gap:8.2f}" + "".join(f"{p:8.2f}" for p in path))

ups   = [e for e in events if e[1] > 0]
downs = [e for e in events if e[1] <= 0]
print(f"\n=== from-open drift, avg (n={len(events)}) ===")
print("all    : " + "".join(f"{avg([e[2][i] for e in events]):8.2f}" for i in range(13)))
print(f"gap-UP (n={len(ups)}): " + "".join(f"{avg([e[2][i] for e in ups]):8.2f}" for i in range(13)))
print(f"gap-DN (n={len(downs)}): " + "".join(f"{avg([e[2][i] for e in downs]):8.2f}" for i in range(13)))

print("\n=== LONG total P&L (from T-1 close), avg ===")
print("labels :  open  " + "".join(f"{l:>8}" for l in LABELS))
print(f"all    : {avg([e[1] for e in events]):6.2f}" + "".join(f"{avg([e[3][i] for e in events]):8.2f}" for i in range(13)))
print(f"gap-UP : {avg([e[1] for e in ups]):6.2f}" + "".join(f"{avg([e[3][i] for e in ups]):8.2f}" for i in range(13)))
print(f"gap-DN : {avg([e[1] for e in downs]):6.2f}" + "".join(f"{avg([e[3][i] for e in downs]):8.2f}" for i in range(13)))

# Exit-rule comparison for the LONG carrier (per event, then averaged):
# open (9:31 market), each checkpoint, plus "first 30min worst/best" awareness
print("\n=== exit rule comparison (long, avg captured % of [T-1 close -> exit]) ===")
rules = {"exit@open(9:31)": None, "exit@9:45": 2, "exit@10:00": 5, "exit@11:00": 7,
         "exit@12:00": 8, "exit@14:00": 10, "exit@close": 12}
for name, idx in rules.items():
    if idx is None:
        vals = [e[1] for e in events]; u = [e[1] for e in ups]; d = [e[1] for e in downs]
    else:
        vals = [e[3][idx] for e in events]; u = [e[3][idx] for e in ups]; d = [e[3][idx] for e in downs]
    print(f"{name:16} all {avg(vals):6.2f}%   gapUP {avg(u):6.2f}%   gapDN {avg(d):6.2f}%")

# Volatility cost of waiting: mean abs deviation from open at each checkpoint
print("\n=== |move from open|, avg (risk of waiting) ===")
print("".join(f"{avg([abs(e[2][i]) for e in events]):8.2f}" for i in range(13)))
