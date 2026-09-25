"""Chart data for Book 7, chapter 27 (deterministic)."""
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from rs_tcost import AUMS, HALF_LIVES, HALF_SPREAD, estimate, fills, run  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/research" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

cost, sigma, part = fills()
f = estimate()
edges = np.quantile(part, np.linspace(0, 1, 21))
idx = np.clip(np.searchsorted(edges, part, side="right") - 1, 0, 19)
with open(OUT / "fills.csv", "w") as fh:
    fh.write("participation,cost_bp,se_bp,fit_bp\n")
    for k in range(20):
        m = idx == k
        p = part[m].mean()
        y = 1e4 * (cost[m] - HALF_SPREAD) / sigma[m] * 0.02                 # scaled to a 2% daily volatility
        fit = 1e4 * f["eta"] * p ** f["exponent"] * 0.02
        fh.write(f"{p:.6f},{y.mean():.3f},{y.std(ddof=1) / np.sqrt(m.sum()):.3f},{fit:.3f}\n")

with open(OUT / "smoothing.csv", "w") as fh:
    fh.write("half_life,naive,aware\n")
    for h in HALF_LIVES:
        naive, aware = max(run("naive", 1e9, h)["sr_net"], -4.0), run("cost-aware", 1e9, h)["sr_net"]
        fh.write(f"{max(h, 0.3):g},{naive:.4f},{aware:.4f}\n")

with open(OUT / "aum.csv", "w") as fh:
    fh.write("aum,naive,aware,aware_smooth,naive_smooth\n")
    for a in AUMS:
        fh.write(f"{a:g},{max(run('naive', a)['sr_net'], -4.0):.4f},{run('cost-aware', a)['sr_net']:.4f},"
                 f"{run('cost-aware', a, 1.0)['sr_net']:.4f},{max(run('naive', a, 50.0)['sr_net'], -4.0):.4f}\n")
