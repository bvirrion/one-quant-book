"""Chart data for Book 3, Chapter 29 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from m3_map import SIZES, desks, staffed_minutes  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/markets-3" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "sizes.csv", "w") as f:
    f.write("idx,usd_bn\n")
    for i, (_, v) in enumerate(SIZES, 1):
        f.write(f"{i},{v:.2f}\n")

with open(OUT / "staffing.csv", "w") as f:
    f.write("hour,weekday,weekend\n")
    wd, we = staffed_minutes(desks(), 2), staffed_minutes(desks(), 6)
    for h in range(24):
        f.write(f"{h},{wd[h * 60]},{we[h * 60]}\n")
