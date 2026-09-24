"""Chart data for Book 2, Chapter 27 (deterministic, seeded)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from access_demo import day_of_orders, plan

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/markets-2" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)
with open(OUT / "nop_path.csv", "w") as f:
    f.write("order,A,B,C\n")
    for t, a, b, c in day_of_orders()["path"]:
        f.write(f"{t},{a:.3f},{b:.3f},{c:.3f}\n")
with open(OUT / "plans.csv", "w") as f:
    f.write("k,plan,fees,nop\n")
    for k, (name, fees, nop) in enumerate(plan()["bars"]):
        f.write(f"{k},{name},{fees / 1000:.3f},{nop / 1000:.3f}\n")
