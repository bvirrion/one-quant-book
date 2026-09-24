"""Chart data for Book 4, Chapter 15 (deterministic; ECB reference rates in data/methods)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from qm_robust import _norm_ppf, hill_curve, load, sensitivity, student_t_fit, tail_quantiles

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/methods" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "sensitivity.csv", "w") as f:
    f.write("error,sd,mad,qn\n")
    for e, sd, md, qn in sensitivity():
        f.write(f"{100 * e:.1f},{sd:.4f},{md:.4f},{qn:.4f}\n")

with open(OUT / "hill.csv", "w") as f:
    f.write("k,alpha,lo,hi\n")
    for k, a, se in hill_curve():
        f.write(f"{k},{a:.4f},{a - 2 * se:.4f},{a + 2 * se:.4f}\n")

d = load(False)
loss = np.sort(-d["r_usd"])[::-1]
n = loss.size
tq = tail_quantiles(False)
t = student_t_fit(-d["r_usd"])
sim = np.sort(np.random.default_rng(11).standard_t(t["df"], 400_000))
with open(OUT / "tail.csv", "w") as f:
    f.write("loss,empirical,normal,student,gpd\n")
    for x in np.linspace(0.5, 4.5, 41):
        emp = np.sum(loss >= x) / n
        mu, sd = float(-d["r_usd"].mean()), tq["sd"]
        pn = 0.5 * math.erfc((x - mu) / sd / math.sqrt(2))
        pt = 1 - np.searchsorted(sim, (x - t["mu"]) / t["scale"]) / sim.size
        pg = float("nan")
        if x > tq["u"]:
            pg = (tq["n_exc"] / n) * (1 + tq["xi"] * (x - tq["u"]) / tq["beta"]) ** (-1 / tq["xi"])
        f.write(f"{x:.2f},{max(emp, 1e-6):.6g},{max(pn, 1e-6):.6g},{max(pt, 1e-6):.6g},"
                + (f"{pg:.6g}" if pg == pg else "nan") + "\n")

a, b = d["r_usd"], d["r_gbp"]
ra = (np.argsort(np.argsort(a)) + 1) / (a.size + 1)
rb = (np.argsort(np.argsort(b)) + 1) / (b.size + 1)
idx = np.arange(0, a.size, 4)
with open(OUT / "copula.csv", "w") as f:
    f.write("u,v\n")
    for i in idx:
        f.write(f"{ra[i]:.4f},{rb[i]:.4f}\n")

qq = np.sort((d["r_usd"] - d["r_usd"].mean()) / d["r_usd"].std())
with open(OUT / "qq.csv", "w") as f:
    f.write("normal,sample\n")
    for i in list(range(0, 40)) + list(range(40, n - 40, 50)) + list(range(n - 40, n)):
        f.write(f"{_norm_ppf((i + 0.5) / n):.4f},{qq[i]:.4f}\n")
