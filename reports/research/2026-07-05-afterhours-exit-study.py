"""After-hours exit study: 13 AMC reactions Apr-Jun 2026.
LONG entered ~15:55 at ~= report-day close (pre_close). Exits: AH checkpoints
(10-min bar closes, ET labels) vs next-morning open (stored post_open)."""
import sqlite3

# symbol, report_date -> 12 AH closes: 16:10,16:20,16:30,16:40,16:50,17:00,17:10,17:20,17:30,17:40,17:50,18:00
AH = {
 ("AMD","2026-05-05"): [355.00,360.17,379.7825,374.1901,369.97,370.8355,372.9828,384.00,382.45,382.81,387.626,393.9328],
 ("SMCI","2026-05-05"): [29.75,31.0873,32.885,33.01,32.64,32.6052,32.7278,33.60,33.4999,33.51,33.03,32.60],
 ("ANET","2026-05-05"): [154.00,168.42,162.82,162.4437,150.60,145.15,147.05,147.25,147.039,147.8062,146.4284,147.59],
 ("ALAB","2026-05-05"): [233.00,219.49,226.5133,216.99,218.00,216.00,219.00,219.00,218.00,218.55,218.60,211.487],
 ("COHR","2026-05-06"): [323.74,321.55,320.50,321.00,317.60,318.13,317.00,315.50,312.58,310.46,309.9071,310.80],
 ("NVDA","2026-05-20"): [224.02,223.90,226.5752,222.174,222.72,222.46,220.94,220.99,223.16,221.8901,221.9303,220.7448],
 ("MRVL","2026-05-27"): [204.93,201.00,207.0001,211.50,215.64,210.00,192.50,201.46,202.98,202.62,204.00,201.57],
 ("DELL","2026-05-28"): [332.10,345.50,370.9064,372.00,370.723,389.25,394.00,401.2769,412.99,411.00,410.31,413.4611],
 ("HPE","2026-06-01"): [57.5561,60.50,61.23,61.11,63.824,63.89,64.29,64.56,64.0209,64.10,62.5463,62.074],
 ("CRDO","2026-06-01"): [193.2802,199.54,201.0652,203.00,201.9562,204.764,201.00,197.9443,201.7498,204.40,202.00,197.11],
 ("AVGO","2026-06-03"): [480.46,450.00,455.32,451.00,446.104,450.60,437.636,427.1738,417.00,416.9175,416.00,419.53],
 ("ORCL","2026-06-10"): [198.48,198.96,191.52,193.8664,190.10,187.50,186.80,186.5002,190.7455,190.55,192.01,189.00],
 ("MU","2026-06-24"): [1158.76,1147.52,1190.14,1194.84,1213.5501,1200.80,1190.36,1173.99,1192.02,1180.23,1184.73,1190.02],
}
LABELS = ["16:10","16:20","16:30","16:40","16:50","17:00","17:10","17:20","17:30","17:40","17:50","18:00"]

db = sqlite3.connect("datasets/earnings.sqlite3"); db.row_factory = sqlite3.Row
events = []
for (sym, rd), closes in AH.items():
    r = db.execute("SELECT pre_close, post_open FROM backtests WHERE symbol=? AND report_date=?", (sym, rd)).fetchone()
    pre, nxt = float(r["pre_close"]), float(r["post_open"])
    path = [(c - pre) / pre * 100 for c in closes]
    open_ret = (nxt - pre) / pre * 100
    events.append((sym, path, open_ret))

def avg(v): return sum(v) / len(v)

print(f"{'sym':6}" + "".join(f"{l:>8}" for l in LABELS) + f"{'nxt open':>10}   (% from 15:55 entry)")
for sym, path, o in events:
    print(f"{sym:6}" + "".join(f"{p:8.2f}" for p in path) + f"{o:10.2f}")

print("\navg   " + "".join(f"{avg([e[1][i] for e in events]):8.2f}" for i in range(12))
      + f"{avg([e[2] for e in events]):10.2f}")

print("\n=== exit rule vs next-open, per event (AH minus open; + means AH better) ===")
for idx, lab in [(1, "16:20"), (2, "16:30"), (5, "17:00"), (11, "18:00")]:
    diffs = [e[1][idx] - e[2] for e in events]
    wins = sum(1 for d in diffs if d > 0)
    print(f"sell@{lab}: avg {avg(diffs):+6.2f}% vs open | better in {wins}/13 | worst {min(diffs):+6.2f} best {max(diffs):+6.2f}")

# The 'reaction not yet out' hazard: how much of the eventual overnight move
# had happened by 16:20? (|16:20 ret| / |next-open ret|, capped cases noted)
print("\n=== % of overnight move realized by 16:20 / 16:30 ===")
for sym, path, o in events:
    if abs(o) < 0.5:
        print(f"{sym:6} open move ~0, skip"); continue
    print(f"{sym:6} 16:20 {path[1]/o*100 if o else 0:7.0f}%   16:30 {path[2]/o*100:7.0f}%   (overnight {o:+.2f}%)")
