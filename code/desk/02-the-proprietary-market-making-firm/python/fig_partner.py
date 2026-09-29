"""Chart data for Book 16, chapter 2 (deterministic)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import fm_partner as m  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/desk" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

(req, _), fo, vol = m.regulatory()
with open(OUT / "capital.csv", "w") as f:
    f.write("k,label,amount\n")
    rows = [("permanent minimum", 0.75), ("fixed overheads (a quarter)", 0.25 * fo),
            ("K-DTF cash trades", 0.001 * vol), ("K-DTF derivatives", 0.0001 * vol),
            ("prime brokers' requirement", m.BASE.capital0)]
    for k, (lab, x) in enumerate(rows):
        f.write(f"{k},{lab},{x:.2f}\n")

v = m.retention_curve()
with open(OUT / "retention.csv", "w") as f:
    f.write("retention,value\n")
    for r, x in zip(m.GRID, v, strict=True):
        f.write(f"{100 * r:.0f},{x:.1f}\n")

t = m.treadmill()
with open(OUT / "treadmill.csv", "w") as f:
    f.write("year,rel_steady,rel_lean,profit_steady,profit_lean\n")
    for i in range(len(t["steady"]["rel"])):
        f.write(f"{i + 1},{t['steady']['rel'][i]:.3f},{t['lean']['rel'][i]:.3f},{t['steady']['profit'][i]:.1f},"
                f"{t['lean']['profit'][i]:.1f}\n")
