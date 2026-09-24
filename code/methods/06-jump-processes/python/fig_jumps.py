"""Chart data for Book 4, Chapter 6 (deterministic, seeded)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from qm_jumps import LAM, SD_DAY, SIG_J, YEAR, Phi, calibrate, charfn_check, day_tail, kurtosis_term

HERE = pathlib.Path(__file__).resolve()
OUT = HERE.parents[4] / "figdata/methods" / HERE.parents[1].name
OUT.mkdir(parents=True, exist_ok=True)
c = calibrate()

# left panel: a Poisson process with rate 5 a year over two years and its compensated version
rng = np.random.default_rng(3)
times = np.cumsum(rng.exponential(1 / 5.0, 30))
times = times[times < 2.0]
with open(OUT / "poisson.csv", "w") as f:
    f.write("t,n,comp\n")
    grid = np.linspace(0, 2, 401)
    for t in grid:
        n = int(np.sum(times <= t))
        f.write(f"{t:.4f},{n},{n - 5.0 * t:.4f}\n")

# right panel: ten years of the calibrated jump-diffusion's log price, daily
rng = np.random.default_rng(8)
n = 10 * YEAR
k = rng.poisson(LAM / YEAR, n)
jumps = c["mu_j"] * k + SIG_J * np.sqrt(k) * rng.standard_normal(n)
drift = -LAM * c["mu_j"] / YEAR                      # makes the mean daily return zero
x = np.concatenate([[0.0], np.cumsum(drift + c["sig_c"] / math.sqrt(YEAR) * rng.standard_normal(n) + jumps)])
with open(OUT / "jd_path.csv", "w") as f:
    f.write("t,x\n")
    for i in range(0, n + 1):
        f.write(f"{i / YEAR:.4f},{x[i]:.5f}\n")
with open(OUT / "jd_jumps.csv", "w") as f:
    f.write("t,x\n")
    for i in np.flatnonzero(k):
        f.write(f"{(i + 1) / YEAR:.4f},{x[i + 1]:.5f}\n")

with open(OUT / "tail.csv", "w") as f:
    f.write("drop,normal,jd\n")
    for d in np.arange(1, 26):
        p_n = Phi(-d / 100 / SD_DAY)
        f.write(f"{d},{math.log10(max(p_n, 1e-300)):.4f},{math.log10(day_tail(d / 100, c['mu_j'], c['sig_c'])):.4f}\n")

with open(OUT / "kurtosis.csv", "w") as f:
    f.write("h,theory,sim\n")
    for h, th, sim in kurtosis_term(c["mu_j"], c["sig_c"]):
        f.write(f"{h},{th:.4f},{sim:.4f}\n")

with open(OUT / "charfn.csv", "w") as f:
    f.write("u,re_emp,re_th,im_emp,im_th\n")
    for row in charfn_check(c["mu_j"], c["sig_c"]):
        f.write(",".join(f"{v:.5f}" for v in row) + "\n")

from qm_jumps import densities  # noqa: E402

with open(OUT / "densities.csv", "w") as f:
    f.write("x,gauss,jd,vg,nig\n")
    for row in densities():
        f.write(",".join(f"{v:.6g}" if v > 0 else "nan" for v in row[1:]).join([f"{row[0]:.2f},", "\n"]))
