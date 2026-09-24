"""Chart data for Book 2, Chapter 5 (deterministic)."""
import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from repo_demo import sept_2019, specialness_curve, sponsored

OUT = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-2/05-repo-and-specials"
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "sept2019.csv", "w") as f:
    f.write("t,sofr,effr,upper,lower\n")
    for r in sept_2019():
        t = (dt.date.fromisoformat(str(r["date"])) - dt.date(2019, 9, 1)).days
        f.write(f"{t},{r['sofr']:.2f},{r['effr']:.2f},{r['range_upper']:.2f},{r['range_lower']:.2f}\n")

with open(OUT / "sponsored.csv", "w") as f:
    f.write("t,repo,reverse,total\n")
    for d, a, b in sponsored():
        day = dt.date.fromisoformat(d)
        t = day.year + (day.month - 0.5) / 12
        f.write(f"{t:.4f},{a / 1000:.3f},{b / 1000:.3f},{(a + b) / 1000:.3f}\n")

with open(OUT / "special.csv", "w") as f:
    f.write("day,bp\n")
    for d, s in specialness_curve():
        f.write(f"{d},{s:.1f}\n")
