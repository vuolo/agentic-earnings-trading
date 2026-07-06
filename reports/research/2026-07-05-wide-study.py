"""Wide study part 2: PEAD (hold days vs exit@open) + BMO premarket exits."""
import sqlite3

# reaction-day close, +1, +2, +3 closes (daily bars)
PEAD = {
 ("TSM","2026-04-16"): [363.35, 370.50, 366.24, 368.08],
 ("VRT","2026-04-22"): [305.14, 321.75, 323.46, 322.43],
 ("AMD","2026-05-05"): [421.39, 408.46, 455.19, 458.79],
 ("SMCI","2026-05-05"): [34.66, 33.62, 35.37, 33.52],
 ("ANET","2026-05-05"): [147.06, 141.75, 141.77, 136.43],
 ("ALAB","2026-05-05"): [213.91, 195.65, 199.79, 207.35],
 ("COHR","2026-05-06"): [319.19, 335.26, 379.69, 374.01],
 ("NVDA","2026-05-20"): [219.51, 215.33, 214.86, 212.60],
 ("MRVL","2026-05-27"): [204.83, 205.00, 219.43, 290.79],   # day+3 contaminated (own 6/2 catalyst)
 ("DELL","2026-05-28"): [420.91, 465.96, 435.31, 421.08],
 ("HPE","2026-06-01"): [56.15, 55.15, 53.69, 49.20],
 ("CRDO","2026-06-01"): [229.00, 214.60, 217.50, 206.89],
 ("AVGO","2026-06-03"): [418.91, 385.73, 396.60, 392.16],
 ("ORCL","2026-06-10"): [184.10, 184.13, 192.64, 188.33],
 ("MU","2026-06-24"): [1213.56, 1132.33, 1145.28, 1154.29],
}
db = sqlite3.connect("datasets/earnings.sqlite3"); db.row_factory = sqlite3.Row
rows = []
for (sym, rd), closes in PEAD.items():
    r = db.execute("SELECT pre_close, post_open FROM backtests WHERE symbol=? AND report_date=?", (sym, rd)).fetchone()
    pre, op = float(r["pre_close"]), float(r["post_open"])
    rets = [(op-pre)/pre*100] + [(c-pre)/pre*100 for c in closes]
    rows.append((sym, rets))

def avg(v): return sum(v)/len(v)
print(f"{'sym':6}{'@open':>8}{'d0 cls':>8}{'d+1':>8}{'d+2':>8}{'d+3':>8}   (long P&L % from T-1 close)")
for sym, r in rows:
    print(f"{sym:6}" + "".join(f"{x:8.2f}" for x in r))
print(f"{'AVG':6}" + "".join(f"{avg([r[1][i] for r in rows]):8.2f}" for i in range(5)))
ups = [r for r in rows if r[1][0] > 0]; dns = [r for r in rows if r[1][0] <= 0]
print(f"{'gapUP':6}" + "".join(f"{avg([r[1][i] for r in ups]):8.2f}" for i in range(5)) + f"  n={len(ups)}")
print(f"{'gapDN':6}" + "".join(f"{avg([r[1][i] for r in dns]):8.2f}" for i in range(5)) + f"  n={len(dns)}")
better1 = sum(1 for r in rows if r[1][2] > r[1][0])
better2 = sum(1 for r in rows if r[1][3] > r[1][0])
print(f"hold d+1 beats open: {better1}/15 | hold d+2 beats open: {better2}/15")
print("worst hold-d+2 give-back vs open: " +
      ", ".join(f"{s} {r[3]-r[0]:+.1f}" for s, r in
                sorted([(s, r) for s, r in rows], key=lambda x: x[1][3]-x[1][0])[:3]))

print("\n=== BMO premarket exits (n=2; % from T-1 close) ===")
# TSM 4/16: pre 375.06 approx from gap -1.66 & open 368.86 -> pre = 368.86/(1-0.0166)
for sym, rd, pts in [
    ("TSM","2026-04-16", [("4:30a",376.61),("5:00a",377.99),("6:30a",368.0),("8:00a",370.44),("9:00a",369.24),]),
    ("VRT","2026-04-22", [("6:00a",299.16),("7:30a",297.46),("8:00a",309.74),("9:00a",307.0),]),
]:
    r = db.execute("SELECT pre_close, post_open FROM backtests WHERE symbol=? AND report_date=?", (sym, rd)).fetchone()
    pre, op = float(r["pre_close"]), float(r["post_open"])
    line = f"{sym:5} open {(op-pre)/pre*100:+.2f}%  | premkt: "
    line += "  ".join(f"{t} {(p-pre)/pre*100:+.2f}%" for t, p in pts)
    print(line)
