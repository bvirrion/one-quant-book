"""Chart data for Book 8, chapter 20 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from s1_carry import paths, summary, wti  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/strategies-1" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

half, full = summary("mixed", 0.5), summary("mixed", 1.0)
with open(OUT / "classes.csv", "w") as f:
    f.write("book,half,full\n")
    for k in ("equity", "bond", "currency", "commodity", "diversified"):
        f.write(f"{k},{half[k]['sr']:.4f},{full[k]['sr']:.4f}\n")

with open(OUT / "paths.csv", "w") as f:
    f.write("year,diversified,currency\n")
    for y, a, b in paths(1.0):
        f.write(f"{y:.3f},{100 * a:.2f},{100 * b:.2f}\n")

w = wti()
with open(OUT / "wti_carry.csv", "w") as f:
    f.write("year,carry_pct\n")
    for i in range(0, len(w["dates"]), 5):
        d = w["dates"][i]
        f.write(f"{d.year + (d.timetuple().tm_yday - 1) / 365.25:.3f},{100 * w['carry'][i]:.2f}\n")
