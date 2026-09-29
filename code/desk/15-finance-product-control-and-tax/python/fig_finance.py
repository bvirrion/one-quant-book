"""Chart data for Book 16, chapter 15 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import fm_finance as m  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/desk" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

w = m.the_walk()
steps = ["flash", "market moves after the flash", "late trades", "fees", "valuation adjustments", "final"]
with open(OUT / "walk.csv", "w") as f:
    f.write("pos,step,base,height\n")
    level = 0.0
    for i, k in enumerate(steps):
        v = w[k] / 1000
        if k in ("flash", "final"):
            base, h = 0.0, v
            level = v
        else:
            base, h = min(level, level + v), abs(v)
            level += v
        f.write(f"{i},{k},{base:.3f},{h:.3f}\n")

with open(OUT / "turnover.csv", "w") as f:
    f.write("turnover,t10,t20,t50\n")
    for t in range(0, 51):
        f.write(f"{t}," + ",".join(f"{100 * m.so.tax_drag(0.08, t, tt):.3f}" for tt in (0.001, 0.002, 0.005)) + "\n")

with open(OUT / "strategies.csv", "w") as f:
    f.write("pos,strategy,r0,r1,r2\n")
    for i, (s, v) in enumerate(m.tax_table().items()):
        f.write(f"{i},{s}," + ",".join(f"{100 * x:.3f}" for x in v.values()) + "\n")
