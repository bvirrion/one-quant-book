"""Chapter 7 of Book 4: point processes and Hawkes processes.

A trading day of 23,400 seconds of self-exciting trade arrivals; the dispersion of counts; maximum
likelihood; time-rescaled residuals; and the spurious branching ratio fitted to a day with no
excitation at all but a U-shaped intraday baseline."""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/hawkes"))
from firm_hawkes import fit, residuals, simulate_branching, simulate_thinning

DAY = 23_400.0                          # seconds from 09:30 to 16:00
MU, ALPHA, BETA = 0.1, 0.7, 1.0         # per second: baseline, jump of the intensity, decay rate
N_BR = ALPHA / BETA
LAM_BAR = MU / (1 - N_BR)


def dispersion_theory(tau: float, n: float = N_BR, beta: float = BETA) -> float:
    """Var N(tau) / E N(tau) for a stationary exponential Hawkes process: the covariance density
    c(u) = lam_bar n (2 - n) beta / (2 (1 - n)) exp(-beta (1 - n) |u|) integrated twice."""
    gam = beta * (1 - n)
    a_rel = n * (2 - n) * beta / (2 * (1 - n))
    return 1 + 2 * a_rel / tau * (tau / gam - (1 - math.exp(-gam * tau)) / gam**2)


def dispersion_sim(times: np.ndarray, tau: float, T: float = DAY) -> float:
    counts = np.histogram(times, bins=np.arange(0, T + 1e-9, tau))[0]
    return float(counts.var() / counts.mean())


def seasonal_rate(t, level: float):
    """U-shaped intraday baseline: three times higher at the open and close than at midday."""
    s = np.asarray(t, dtype=float) / DAY
    return level * (1 + 8 * (s - 0.5) ** 2)


def simulate_seasonal_poisson(mean_rate: float, seed: int) -> np.ndarray:
    """Inhomogeneous Poisson process with the U-shaped rate, by thinning at the maximum rate."""
    level = mean_rate / (1 + 8 / 12)            # mean of 1 + 8 (s - 1/2)^2 over [0, 1] is 5/3
    rng = np.random.default_rng(seed)
    top = 3 * level
    n = rng.poisson(top * DAY)
    cand = np.sort(rng.uniform(0, DAY, n))
    keep = rng.random(n) * top <= seasonal_rate(cand, level)
    return cand[keep]


def problem() -> dict:
    t = simulate_thinning(MU, ALPHA, BETA, DAY, seed=1)
    f = fit(t, DAY)
    r = residuals(t, f["mu"], f["alpha"], f["beta"])
    poisson_r = np.diff(np.concatenate([[0.0], t])) * (t.size / DAY)
    days = [fit(simulate_thinning(MU, ALPHA, BETA, DAY, seed=100 + k), DAY)["branching"] for k in range(40)]
    s = simulate_seasonal_poisson(LAM_BAR, seed=2)
    fs = fit(s, DAY)
    spurious = [fit(simulate_seasonal_poisson(LAM_BAR, seed=200 + k), DAY)["branching"] for k in range(20)]
    flat = []
    for k in range(20):
        n_k = np.random.default_rng(400 + k).poisson(LAM_BAR * DAY)
        flat.append(fit(np.sort(np.random.default_rng(300 + k).uniform(0, DAY, n_k)), DAY)["branching"])
    tb, gen = simulate_branching(MU, ALPHA, BETA, DAY, seed=3)
    return {
        "lam_bar": LAM_BAR, "expected_events": LAM_BAR * DAY, "events": int(t.size),
        "mu_hat": f["mu"], "alpha_hat": f["alpha"], "beta_hat": f["beta"], "n_hat": f["branching"],
        "n_mean": float(np.mean(days)), "n_sd": float(np.std(days)),
        "res_mean": float(r.mean()), "res_var": float(r.var()),
        "poisson_res_var": float(poisson_r.var()),
        "disp_1s": dispersion_theory(1.0), "disp_60s": dispersion_theory(60.0), "disp_inf": 1 / (1 - N_BR) ** 2,
        "disp_60s_sim": dispersion_sim(t, 60.0),
        "seasonal_events": int(s.size), "n_spurious": fs["branching"], "beta_spurious": fs["beta"],
        "n_spurious_mean": float(np.mean(spurious)), "n_flat_mean": float(np.mean(flat)),
        "branch_share": float((gen > 0).mean()), "branch_events": int(tb.size),
        "cluster_size": 1 / (1 - N_BR), "half_life_kernel": math.log(2) / BETA,
    }
