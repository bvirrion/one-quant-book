"""Chart data for Book 10, chapter 6 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mx_ticks import did_panel, priority_compare, tick_experiment  # noqa: E402, I001
from firm_queuevalue import fill_probability  # noqa: E402, I001  (on the path once mx_ticks is imported)

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/microstructure" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

r = tick_experiment()
with open(OUT / "queue.csv", "w") as f:
    f.write("k,n,fill1,bd1,fill5,bd5,value1,value5,value10\n")
    rows = zip(r[1]["by_orders"], r[5]["by_orders"], r[10]["by_orders"], strict=True)
    for k, (a, b, c) in enumerate(rows):
        bd1 = fill_probability(a["lo"], r[1]["mu"], r[1]["theta"], r[1]["theta"])
        bd5 = fill_probability(b["lo"], r[5]["mu"], r[5]["theta"], r[5]["theta"])
        f.write(f"{k},{a['lo']},{a['fill']:.4f},{bd1:.4f},{b['fill']:.4f},{bd5:.4f},{a['value']:.4f},{b['value']:.4f},"
                f"{c['value']:.4f}\n")

p = priority_compare()
with open(OUT / "priority.csv", "w") as f:
    f.write("k,n,fill_fifo,fill_pr,value_fifo,value_pr\n")
    for k, (a, b) in enumerate(zip(p["fifo"], p["pro_rata"], strict=True)):
        f.write(f"{k},{a['lo']},{a['fill']:.4f},{b['fill']:.4f},{a['value']:.4f},{b['value']:.4f}\n")

d = did_panel()["depth"]["cells"]
with open(OUT / "did.csv", "w") as f:
    f.write("period,treated,control\n")
    for post in (0, 1):
        f.write(f"{post},{d[f't1p{post}']:.1f},{d[f't0p{post}']:.1f}\n")
