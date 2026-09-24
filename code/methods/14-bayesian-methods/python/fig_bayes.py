"""Chart data for Book 4, Chapter 14 (deterministic, seeded)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from qm_bayes import SE, SEED, average_mse, eb_normal_means, mcmc, platform

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/methods" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)

p = platform(SEED)
eb = eb_normal_means(p["x1"], SE)
with open(OUT / "managers.csv", "w") as f:
    f.write("x1,x2,theta,eb\n")
    for a, b, c, d in zip(p["x1"], p["x2"], p["theta"], eb["post_mean"], strict=True):
        f.write(f"{a:.4f},{b:.4f},{c:.4f},{d:.4f}\n")
with open(OUT / "lines.csv", "w") as f:
    f.write("x,diag,eb\n")
    for x in np.linspace(-1.0, 3.0, 9):
        f.write(f"{x:.2f},{x:.4f},{eb['m'] + (1 - eb['shrink'][0]) * (x - eb['m']):.4f}\n")

a = average_mse()
with open(OUT / "mse.csv", "w") as f:
    f.write("k,estimator,truth,next\n")
    for k, name in enumerate(("raw", "js", "eb", "oracle")):
        f.write(f"{k},{name},{a['truth'][name]:.4f},{a['next'][name]:.4f}\n")

rows = []
for s in range(2000):
    q = platform(10_000 + s)
    i = int(np.argmax(q["x1"]))
    rows.append((q["x1"][i] - q["theta"][i], eb_normal_means(q["x1"], SE)["post_mean"][i] - q["theta"][i]))
err = np.array(rows)
edges = np.linspace(-1.5, 3.0, 46)
h_raw = np.histogram(err[:, 0], bins=edges)[0] / (err.shape[0] * np.diff(edges))
h_eb = np.histogram(err[:, 1], bins=edges)[0] / (err.shape[0] * np.diff(edges))
with open(OUT / "curse.csv", "w") as f:
    f.write("x,raw,eb\n")
    for i in range(h_raw.size):
        f.write(f"{0.5 * (edges[i] + edges[i + 1]):.3f},{h_raw[i]:.4f},{h_eb[i]:.4f}\n")

m = mcmc()
edges = np.linspace(0.0, 1.0, 41)
hg = np.histogram(m["tau_draws_gibbs"], bins=edges)[0] / (m["tau_draws_gibbs"].size * np.diff(edges))
hm = np.histogram(m["tau_draws_mh"], bins=edges)[0] / (m["tau_draws_mh"].size * np.diff(edges))
with open(OUT / "tau.csv", "w") as f:
    f.write("tau,gibbs,metropolis\n")
    for i in range(hg.size):
        f.write(f"{0.5 * (edges[i] + edges[i + 1]):.4f},{hg[i]:.4f},{hm[i]:.4f}\n")
