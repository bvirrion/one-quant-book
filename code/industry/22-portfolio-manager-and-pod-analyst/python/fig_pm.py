"""Chart data for Book 17, chapter 22."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import in_pm as a  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/industry" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)
rows = a.curve()
with open(OUT / "deal.csv", "w") as f:
    f.write("sr,mean,p10,p50,p90,ce,stopped\n")
    for r in rows:
        f.write(f"{r['sr']:.2f}," + ",".join(f"{r[k] / 1e6:.3f}" for k in ("mean", "p10", "p50", "p90", "ce"))
                + f",{100 * r['stopped']:.2f}\n")
x, _ = a.crossing(rows)
xc, _ = a.crossing(rows, "ce")
with open(OUT / "cross.csv", "w") as f:
    f.write("sr,pay\n")
    f.write(f"{x:.3f},{3 * a.ALTERNATIVE / 1e6:.2f}\n{xc:.3f},{3 * a.ALTERNATIVE / 1e6:.2f}\n")
edges = np.arange(0, 42, 2.0)
with open(OUT / "hist.csv", "w") as f:
    f.write("left,sr0,sr1\n")
    h0 = np.histogram(np.clip(a.run(0.0)["pay"] / 1e6, 0, 39.99), edges)[0] / a.N * 100
    h1 = np.histogram(np.clip(a.run(1.0)["pay"] / 1e6, 0, 39.99), edges)[0] / a.N * 100
    for e, u, v in zip(edges[:-1], h0, h1, strict=True):
        f.write(f"{e:.0f},{u:.2f},{v:.2f}\n")
    f.write(f"{edges[-1]:.0f},0.00,0.00\n")  # right edge of the last bin (ybar interval)
s = a.survey()
rows2 = (("analysts; funds and pools", ("525900", "13-2051")), ("analysts; securities", ("523000", "13-2051")),
         ("financial managers; funds and pools", ("525900", "11-3031")),
         ("financial managers; securities", ("523000", "11-3031")))
with open(OUT / "survey.csv", "w") as f:
    f.write("pos,label,p10,p25,p50,p75,p90\n")
    for i, (lab, k) in enumerate(rows2):
        vals = ",".join(f"{float(s[k][q]) / 1000:.1f}" for q in ("p10", "p25", "p50", "p75", "p90"))
        f.write(f"{i + 1},{lab},{vals}\n")
