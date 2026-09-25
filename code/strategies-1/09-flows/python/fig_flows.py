"""Chart data for Book 8, chapter 9 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s1_flows import YEAR, event_path  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-1" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

top, bot = event_path()
ttop, tbot = event_path(1.5, 3 * YEAR, 2.0)
none_top, none_bot = event_path(0.0)
with open(OUT / "path.csv", "w") as f:
    f.write("year,spread,no_pressure,tilted\n")
    for i in range(0, len(top), 5):
        f.write(f"{i / YEAR:.3f},{100 * (top[i] - bot[i]):.3f},{100 * (none_top[i] - none_bot[i]):.3f},"
                f"{100 * (ttop[i] - tbot[i]):.3f}\n")
