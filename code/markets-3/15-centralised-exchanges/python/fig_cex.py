"""Chart data for Book 3, Chapter 15 (deterministic)."""
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from m3_cex import burst

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/markets-3" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)
DATA = HERE.parents[4] / "data/markets-3"

with open(OUT / "burst.csv", "w") as f:
    f.write("second,fifo,age,coalesced\n")
    for (s, _, q, a), (_, _, qc, _) in zip(burst(), burst(coalesce=True), strict=True):
        f.write(f"{s},{q},{a},{qc}\n")

with open(OUT / "flows.csv", "w") as f:
    f.write("day,cust_out,cust_cum,rel_cum\n")
    cc = rc = 0
    for r in csv.DictReader(open(DATA / "ftx_com_daily_flows_nov2022.csv")):
        out = int(r["customer_withdrawals"]) - int(r["customer_deposits"])
        cc += out
        rc += int(r["related_deposits"]) - int(r["related_withdrawals"])
        f.write(f"{int(r['date'][-2:])},{out},{cc},{rc}\n")
