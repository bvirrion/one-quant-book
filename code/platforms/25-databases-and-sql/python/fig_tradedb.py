"""Chart data for One Quant Book 15, chapter 25 (deterministic: the week's trades, seed 25; 1,000 interleavings)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pl_tradedb import NOW, TUE_18, WED_10, D, lost_updates, report  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/platforms" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

r = report()
conn = r["conn"]
kind = {}
for k, ids in r["fixed"].items():
    for t in ids:
        a, s = conn.execute("SELECT a.name, i.symbol FROM trades t JOIN accounts a ON a.id = t.account_id "
                            "JOIN instruments i ON i.id = t.instrument_id WHERE trade_id = ?", (t,)).fetchone()
        kind[(a, s)] = k
with open(OUT / "report_diff.csv", "w") as f:
    f.write("rank,account,symbol,as_was,corrected,change,kind\n")
    rows = sorted(r["diff"], key=lambda d: d[2] - d[1])
    for i, ((a, s), was, now) in enumerate(rows):
        f.write(f"{i + 1},{a},{s},{was},{now},{now - was},{kind[(a, s)]}\n")
with open(OUT / "summary.csv", "w") as f:
    f.write("trades,versions,qty_fixes,cancels,late,rows_as_was,rows_corrected,rows_differ,in_place_equals_corrected\n")
    f.write(f"{r['n_trades']},{r['versions']},{len(r['fixed']['qty'])},{len(r['fixed']['cancel'])},"
            f"{len(r['fixed']['late'])},{len(r['as_was'])},{len(r['corrected'])},{len(r['diff'])},"
            f"{r['in_place_equals_corrected']}\n")
t = r["fixed"]["qty"][0]
with open(OUT / "versions.csv", "w") as f:
    f.write("trade_id,qty,valid_from,valid_to,sys_from,sys_to,tue_18,wed_10,now\n")
    for row in conn.execute(f"SELECT {D.COLS} FROM trades WHERE trade_id = ? ORDER BY sys_from", (t,)):
        f.write(f"{row[0]},{row[3]},{row[5]},{row[6]},{row[7]},{row[8]},{TUE_18},{WED_10},{NOW}\n")
with open(OUT / "lost.csv", "w") as f:
    f.write("mode,lost_per_1000\n")
    for m in ("autocommit", "transaction", "one statement"):
        f.write(f"{m},{lost_updates(m)}\n")
# the measured query times (bench_tradedb.py) pivoted for the chart: one row per query
meas = list(__import__("csv").DictReader(open(OUT / "measured_queries.csv")))
cols = {"SQLite no index": "sqlite_none", "SQLite index account-instrument": "sqlite_ai",
        "SQLite index valid time": "sqlite_v", "DuckDB": "duckdb"}
with open(OUT / "queries_wide.csv", "w") as f:
    f.write("query," + ",".join(cols.values()) + "\n")
    for q in ("point", "report", "analytic"):
        v = {cols[m["engine"]]: m["ms"] for m in meas if m["query"] == q}
        f.write(q + "," + ",".join(v[c] for c in cols.values()) + "\n")
