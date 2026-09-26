"""Chart data for Book 12, chapter 11 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from ml_uncert import ALPHAS, conformal, ensemble, scores  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/ml" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

c = conformal()
b = c["band"]
(_, _, _), (em, ea, ee) = ensemble()
from scipy.stats import norm  # noqa: E402

z = norm.ppf(0.95)
A = 20
with open(OUT / "band.csv", "w") as f:
    f.write("day,y,lo,hi,alo,ahi\n")
    for i in range(0, len(b["y"]), A):                                   # asset 0
        d = b["day"][i]
        if 2000 <= d < 2250:
            s = np.sqrt(ea[i] + ee[i])
            w = b["adaptive_threshold"][i] * b["sigma"][i]
            f.write(f"{d},{100 * b['y'][i]:.4f},{100 * (em[i] - z * s):.4f},{100 * (em[i] + z * s):.4f},"
                    f"{100 * (b['mean'][i] - w):.4f},{100 * (b['mean'][i] + w):.4f}\n")

s = scores()
with open(OUT / "coverage.csv", "w") as f:
    f.write("i,name,before,after\n")
    rows = [("boosted quantiles", s["boosted quantiles"]), ("ensemble of 5", s["ensemble of 5"]),
            ("mixture density", s["mixture density"])]
    for i, (name, r) in enumerate(rows):
        f.write(f"{i},{name},{100 * r['before']['cov90']:.2f},{100 * r['after']['cov90']:.2f}\n")
    for j, key in enumerate(("raw", "normalised", "adaptive")):
        f.write(f"{3 + j},conformal {key},{100 * c['before'][key]:.2f},{100 * c['after'][key]:.2f}\n")
del ALPHAS
