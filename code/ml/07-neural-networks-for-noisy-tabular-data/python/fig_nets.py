"""Chart data for Book 12, chapter 7 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from ml_nets import LARGE, SMALL, VAL, _xy, ensemble, fitted, seed_study  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/ml" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

s = seed_study()
with open(OUT / "seeds.csv", "w") as f:
    f.write("arch,ic\n")
    for x in s["small"]:
        f.write(f"1,{x:.5f}\n")
    for x in s["large"]:
        f.write(f"2,{x:.5f}\n")
with open(OUT / "means.csv", "w") as f:
    f.write("arch,mean,ensemble\n")
    f.write(f"1,{s['small'].mean():.5f},{ensemble()['ic']:.5f}\n")
    f.write(f"2,{s['large'].mean():.5f},{ensemble(hidden=LARGE)['ic']:.5f}\n")

_, yv = _xy(VAL)
v = float(np.var(yv / np.std(_xy(np.arange(0, 200))[1])))
with open(OUT / "history.csv", "w") as f:
    f.write("epoch,s1,s2,s3\n")
    hs = [fitted(SMALL, k, 0.0, 0.0, None, 1e-3)[0].history for k in (1, 2, 3)]
    for e in range(max(len(h) for h in hs)):
        vals = [f"{100 * (1 - h[e] / v):.4f}" if e < len(h) else "nan" for h in hs]
        f.write(f"{e + 1}," + ",".join(vals) + "\n")
