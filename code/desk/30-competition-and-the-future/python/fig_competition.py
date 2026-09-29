"""Chart data for Book 16, chapter 30 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import fm_competition as m  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/desk" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "entry.csv", "w") as f:
    f.write("F,n,planner,hhi\n")
    for fixed in range(10, 205, 5):
        e = m.entry(float(fixed))
        f.write(f"{fixed},{e['n']},{e['planner']},{e['hhi']:.1f}\n")

lo_hi = m.public_bounds()
x = m.WHOLESALERS - 2
lo = [m.TOP2 / 2] * 2 + [(1 - m.TOP2) / x] * x
b = (1 - m.TOP2) / x
hi = [m.TOP2 - b, b] + [b] * x
with open(OUT / "bounds.csv", "w") as f:
    f.write("rank,low,high\n")
    for i, (u, v) in enumerate(zip(lo, hi, strict=True), start=1):
        f.write(f"{i},{100 * u:.2f},{100 * v:.2f}\n")
assert abs(m.fm.hhi(lo) - lo_hi[0]) < 1e-6 and abs(m.fm.hhi(hi) - lo_hi[1]) < 1e-6

with open(OUT / "merger.csv", "w") as f:
    f.write("synergy,price,hhi\n")
    for i in range(0, 13):
        d = 0.1 * i
        r = m.merger(d)
        f.write(f"{d:.1f},{r['post']['price']:.4f},{r['post']['hhi']:.1f}\n")
