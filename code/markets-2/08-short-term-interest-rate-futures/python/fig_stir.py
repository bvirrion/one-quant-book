"""Chart data for Book 2, Chapter 8 (deterministic)."""
import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from stir_demo import DEC, JAN, OCT, START_RATE, convexity_table, path, turn_sensitivity

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-2/08-short-term-interest-rate-futures"
OUT.mkdir(parents=True, exist_ok=True)
T0 = dt.date(2026, 9, 1)

p = dict(path())
steps = [(dt.date(2026, 9, 17), START_RATE), (OCT.meeting + dt.timedelta(days=1), p["2026-11"]),
         (DEC.meeting + dt.timedelta(days=1), p["2026-12"]), (JAN.meeting + dt.timedelta(days=1), p["2027-01"]),
         (dt.date(2027, 1, 31), p["2027-01"])]
with open(OUT / "path.csv", "w") as f:
    f.write("t,rate\n")
    for d, r in steps:
        f.write(f"{(d - T0).days},{r:.4f}\n")

with open(OUT / "convexity.csv", "w") as f:
    f.write("t1,s08,s10,s12\n")
    for row in convexity_table():
        f.write(",".join(f"{v:.4f}" for v in row) + "\n")

with open(OUT / "turn.csv", "w") as f:
    f.write("turn,prob\n")
    for t, pr in turn_sensitivity():
        f.write(f"{t},{pr:.3f}\n")
