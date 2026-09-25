"""Chart data for Book 7, chapter 6 (deterministic)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from rs_anatomy import BURN, exposures, lag_profile, neutralisation, panel  # noqa: I001  (sets the paths)
from firm_predictor import ic_series, neutralise  # noqa: E402
from firm_synthmkt import MarketConfig, simulate  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/research" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

lp = lag_profile(range(1, 11))
with open(OUT / "lags.csv", "w") as f:
    f.write("k,ic\n")
    for k, v in lp.items():
        f.write(f"{k},{v:.5f}\n")

p = panel()
ret = np.where(p.listed, p.ret, np.nan)
ic = ic_series(neutralise(-ret, exposures(p))[BURN:-1], ret[BURN + 1:], "rank")
cum = np.cumsum(np.nan_to_num(ic))
with open(OUT / "cumic.csv", "w") as f:
    f.write("year,cum\n")
    for i in range(0, len(cum), 5):
        f.write(f"{(BURN + i + 1) / 252:.4f},{cum[i]:.4f}\n")

nz = neutralisation(simulate(MarketConfig(ind_vol=0.30)))
with open(OUT / "neutral.csv", "w") as f:
    f.write("k,label,ic,t\n")
    for k, name in enumerate(("raw", "residual", "neutral")):
        f.write(f"{k},{name},{nz[name]['mean']:.5f},$t = {nz[name]['t_hac']:.1f}$\n")
print("share", round(nz["share"], 3), {k: round(nz[k]["mean"], 4) for k in ("raw", "residual", "neutral")})
