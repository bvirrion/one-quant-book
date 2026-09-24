"""Book 4, chapter 14: Bayesian methods (teaching module).

Fifty portfolio managers, each with a true Sharpe ratio drawn from the platform's distribution and a
three-year record that measures it with an error of 1/sqrt(3). The best record is shrunk toward what
managers usually achieve, and a second three-year period shows the shrinkage was right.
"""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "bayes"))
from firm_bayes import (  # noqa: E402
    beta_binomial,
    eb_normal_means,
    ess,
    gibbs_hierarchical,
    james_stein,
    metropolis,
    rhat,
)

K = 50                     # managers
M_TRUE = 0.5               # mean true Sharpe ratio on the platform
TAU_TRUE = 0.4             # dispersion of true Sharpe ratios
YEARS = 3
SE = 1 / math.sqrt(YEARS)  # standard error of a three-year Sharpe ratio (chapter 11, small daily ratios)
SEED = 203                 # a platform whose best three-year record is 2.4, as in the hook


def platform(seed: int, k: int = K, m: float = M_TRUE, tau: float = TAU_TRUE, se: float = SE) -> dict:
    """True Sharpe ratios and two independent three-year records."""
    rng = np.random.default_rng(seed)
    theta = m + tau * rng.standard_normal(k)
    return {"theta": theta, "x1": theta + se * rng.standard_normal(k), "x2": theta + se * rng.standard_normal(k)}


def oracle(x, m: float = M_TRUE, tau: float = TAU_TRUE, se: float = SE) -> np.ndarray:
    """Posterior mean with the true platform parameters (the best any shrinkage can do)."""
    b = se**2 / (se**2 + tau**2)
    return m + (1 - b) * (np.asarray(x) - m)


def mse_table(p: dict) -> dict:
    x1, th, x2 = p["x1"], p["theta"], p["x2"]
    eb = eb_normal_means(x1, SE)["post_mean"]
    js = james_stein(x1, SE)
    ests = {"raw": x1, "js": js, "eb": eb, "oracle": oracle(x1)}
    return {"truth": {k: float(np.mean((v - th) ** 2)) for k, v in ests.items()},
            "next": {k: float(np.mean((v - x2) ** 2)) for k, v in ests.items()}}


def average_mse(n_plat: int = 2000, seed0: int = 10_000) -> dict:
    acc = {"truth": {}, "next": {}}
    for s in range(n_plat):
        t = mse_table(platform(seed0 + s))
        for a in acc:
            for k, v in t[a].items():
                acc[a][k] = acc[a].get(k, 0.0) + v / n_plat
    return acc


def best_manager_average(n_plat: int = 2000, seed0: int = 10_000) -> dict:
    """Across platforms: the best record, its true ratio, its EB estimate and its next-period record."""
    rows = []
    for s in range(n_plat):
        p = platform(seed0 + s)
        i = int(np.argmax(p["x1"]))
        rows.append((p["x1"][i], p["theta"][i], eb_normal_means(p["x1"], SE)["post_mean"][i], p["x2"][i]))
    a = np.array(rows)
    return {"best": float(a[:, 0].mean()), "theta": float(a[:, 1].mean()), "eb": float(a[:, 2].mean()),
            "next": float(a[:, 3].mean())}


def marginal_logpost(x, se: float = SE):
    """log p(m, log tau | x) with flat priors on m and tau: x_i ~ N(m, se^2 + tau^2), Jacobian tau."""
    x = np.asarray(x, dtype=float)

    def f(z):
        m, lt = z
        v = se**2 + math.exp(2 * lt)
        return float(-0.5 * np.sum((x - m) ** 2) / v - 0.5 * x.size * math.log(v) + lt)
    return f


def mcmc(seed: int = SEED, n_iter: int = 20_000, burn: int = 2_000, n_chains: int = 4) -> dict:
    p = platform(seed)
    x = p["x1"]
    i = int(np.argmax(x))
    g = gibbs_hierarchical(x, SE, n_iter, np.random.default_rng(1))
    theta_best = g["theta"][burn:, i]
    tau = g["tau"][burn:]
    chains = []
    accs = []
    for c in range(n_chains):
        ch, acc = metropolis(marginal_logpost(x), [x.mean() + c - 1.5, math.log(0.2 + 0.2 * c)], n_iter,
                             [0.12, 0.35], np.random.default_rng(100 + c))
        chains.append(ch[burn:])
        accs.append(acc)
    tau_mh = np.concatenate([np.exp(ch[:, 1]) for ch in chains])
    return {"best_post_mean": float(theta_best.mean()), "best_ci": tuple(np.quantile(theta_best, [0.025, 0.975])),
            "tau_mean": float(tau.mean()), "tau_ci": tuple(np.quantile(tau, [0.025, 0.975])),
            "p_tau_small": float(np.mean(tau < 0.2)),
            "tau_draws_gibbs": tau, "tau_draws_mh": tau_mh, "tau_mean_mh": float(tau_mh.mean()),
            "ess_gibbs_tau": ess(tau), "ess_mh_tau": ess(np.exp(chains[0][:, 1])),
            "rhat_mh_tau": rhat([np.exp(ch[:, 1]) for ch in chains]), "acc_mh": float(np.mean(accs)),
            "n_kept": n_iter - burn}


def problem(seed: int = SEED) -> dict:
    p = platform(seed)
    x = p["x1"]
    i = int(np.argmax(x))
    eb = eb_normal_means(x, SE)
    js = james_stein(x, SE)
    t = mse_table(p)
    order = np.argsort(-x)
    return {"best": float(x[i]), "best_theta": float(p["theta"][i]), "best_next": float(p["x2"][i]),
            "m": eb["m"], "tau": math.sqrt(eb["tau2"]), "shrink": float(eb["shrink"][0]),
            "best_eb": float(eb["post_mean"][i]), "best_eb_sd": float(eb["post_sd"][i]),
            "best_js": float(js[i]), "js_factor": float((js[i] - x.mean()) / (x[i] - x.mean())),
            "mse": t, "top3_raw": [float(v) for v in x[order[:3]]],
            "top3_eb": [float(v) for v in eb["post_mean"][order[:3]]],
            "top3_next": [float(v) for v in p["x2"][order[:3]]],
            "top3_theta": [float(v) for v in p["theta"][order[:3]]],
            "rank_by_eb_equals_raw": bool(np.all(np.argsort(-eb["post_mean"]) == order)),
            "sd_x": float(x.std(ddof=1)), "n_neg": int(np.sum(x < 0))}


def hit_rate_example() -> dict:
    """A signal right on 110 of 200 trades, prior Beta(50, 50): posterior and P(hit rate > 50%) by simulation."""
    a, b = beta_binomial(50, 50, 110, 200)
    draws = np.random.default_rng(5).beta(a, b, 400_000)
    return {"a": a, "b": b, "mean": a / (a + b), "p_above": float(np.mean(draws > 0.5)),
            "ci": tuple(np.quantile(draws, [0.025, 0.975]))}
