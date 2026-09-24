"""Chart data for Book 5, Chapter 15 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from dv_barrier import barrier_curves, calendar_example, delta_curves, monitoring, payoff_curves, reverse_barrier

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/derivatives" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

spots, dc = delta_curves()
with open(OUT / "digital_delta.csv", "w") as f:
    f.write("s,week,day,hour\n")
    for i, x in enumerate(spots):
        f.write(f"{x:.1f},{dc['week'][i]:.5f},{dc['day'][i]:.5f},{dc['hour'][i]:.5f}\n")

s, dig, spread = payoff_curves()
with open(OUT / "overhedge.csv", "w") as f:
    f.write("s,digital,spread\n")
    for a, b, c in zip(s, dig, spread, strict=True):
        f.write(f"{a:.1f},{b:.4f},{c:.4f}\n")

with open(OUT / "barrier_curves.csv", "w") as f:
    f.write("s,call,doc,dic\n")
    for x, c, o, i in barrier_curves():
        f.write(f"{x:.2f},{c:.5f},{o:.5f},{i:.5f}\n")

with open(OUT / "monitoring.csv", "w") as f:
    f.write("n,mc,lo,hi,shifted,cont\n")
    for r in monitoring():
        f.write(f"{r['n']},{r['mc']:.5f},{r['mc'] - 2 * r['se']:.5f},{r['mc'] + 2 * r['se']:.5f},"
                f"{r['shifted']:.5f},{r['cont']:.5f}\n")

cal = calendar_example()
with open(OUT / "calendar_barrier.csv", "w") as f:
    f.write("t,n4,n16\n")
    for i, t in enumerate(cal["times"]):
        f.write(f"{t:.4f},{cal['on_barrier'][4][i]:.5f},{cal['on_barrier'][16][i]:.5f}\n")
with open(OUT / "calendar_prices.csv", "w") as f:
    f.write("n,price,uoc\n")
    for n, p in cal["prices"].items():
        f.write(f"{n},{p:.5f},{cal['uoc']:.5f}\n")

rb = reverse_barrier()
with open(OUT / "reverse.csv", "w") as f:
    f.write("s,value,delta\n")
    for x, v, d in zip(rb["spots"], rb["value"], rb["delta"], strict=True):
        f.write(f"{x:.3f},{v:.5f},{d:.5f}\n")
