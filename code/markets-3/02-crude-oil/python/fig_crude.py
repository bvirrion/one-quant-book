"""Chart data for Book 3, Chapter 2 (deterministic, from data/markets-3)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from m3_crude import load_wti, spring_2020

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/markets-3" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "spring2020.csv", "w") as f:
    f.write("day,c1,c2\n")
    d0 = spring_2020()[0][0]
    for d, c1, c2 in spring_2020():
        f.write(f"{(d - d0).days},{c1:.2f},{c2:.2f}\n")
with open(OUT / "spread.csv", "w") as f:
    f.write("t,spread\n")
    for d, c1, c2, _, _ in load_wti():
        if d.weekday() == 2 or c2 - c1 > 10:          # Wednesdays, plus every day off the scale
            f.write(f"{d.year + (d.timetuple().tm_yday - 0.5) / 366:.4f},{min(c2 - c1, 10.0):.2f}\n")
