"""Chart data for Book 9, chapter 8 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s2_convarb import YEAR, cumulative, profile  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-2" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

p = profile()
with open(OUT / "profile.csv", "w") as f:
    f.write("share,value,conversion,floor\n")
    for s, v in zip(p["grid"], p["curve"], strict=True):
        f.write(f"{s:.1f},{v:.2f},{2.5 * s:.2f},{p['floor']:.2f}\n")

c = cumulative()
with open(OUT / "book.csv", "w") as f:
    f.write("year," + ",".join(c) + "\n")
    for i in range(0, len(c["total"]), 5):
        f.write(f"{(i + 1) / YEAR:.3f}," + ",".join(f"{100 * c[k][i]:.2f}" for k in c) + "\n")
