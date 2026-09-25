"""Chart data for Book 8, chapter 18 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s1_asia import LIMITS, band, limit_ups  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-1" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "widths.csv", "w") as f:
    f.write("limit_pct,open_pct,filled_pct,week_pct\n")
    for L in LIMITS:
        a = limit_ups(L)["all"]
        f.write(f"{100 * L:.0f},{100 * a['open']:.3f},{100 * a['filled']:.3f},{100 * a['week']:.3f}\n")

with_m, _ = band(0.5)
without, _ = band(0.0)
with open(OUT / "magnet.csv", "w") as f:
    f.write("bin_pct,magnet,none\n")
    for (e, a), (_, b) in zip(with_m, without, strict=True):
        f.write(f"{100 * e + 0.25:.2f},{1e4 * a:.3f},{1e4 * b:.3f}\n")
