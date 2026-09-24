"""Book 4, chapter 26: Monte Carlo (teaching module).

The representative trade of the overnight batch, an arithmetic-average (Asian) call on geometric Brownian motion
with 64 fixings, valued by plain Monte Carlo, antithetic variates, the geometric-average control variate and
scrambled Sobol points with and without a Brownian-bridge construction; Euler and Milstein orders; multilevel
Monte Carlo; importance sampling for a deep out-of-the-money digital.
"""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / "code" / "firm" / "mcengine"))
from firm_mcengine import (  # noqa: E402
    asian_payoffs,
    bridge_from_normals,
    control_variate,
    geometric_asian_price,
    increment_from_normals,
    mlmc,
    norm_ppf,
    owen_scramble,
    philox_uniforms,
    sobol_points,
)

S0, K, R, SIGMA, T, FIX = 100.0, 100.0, 0.03, 0.25, 1.0, 64
BOOK_SE, TARGET_SE, BOOK_PATHS = 80_000.0, 20_000.0, 100_000


def _payoffs(U: np.ndarray, bridge: bool) -> tuple:
    Z = norm_ppf(U)
    W = bridge_from_normals(Z, T) if bridge else increment_from_normals(Z, T)
    return asian_payoffs(W, S0, K, R, SIGMA, T)


def plain(n: int, seed: int = 26, stream: int = 0) -> dict:
    a, g = _payoffs(philox_uniforms(n, FIX, seed, stream), bridge=False)
    return {"est": float(a.mean()), "var": float(a.var(ddof=1)), "a": a, "g": g}


def antithetic(n_pairs: int, seed: int = 26) -> dict:
    U = philox_uniforms(n_pairs, FIX, seed, stream=1)
    a1, _ = _payoffs(U, False)
    a2, _ = _payoffs(1.0 - U, False)
    y = 0.5 * (a1 + a2)
    return {"est": float(y.mean()), "var_pair": float(y.var(ddof=1)), "rho": float(np.corrcoef(a1, a2)[0, 1])}


def rqmc_replicates(m: int = 14, reps: int = 32, bridge: bool = True, seed: int = 2600) -> np.ndarray:
    """Per replicate (independent Owen scramble) and per prefix size 2^k, k <= m: the plain and control-variate
    averages. Returns array (reps, m + 1, 2)."""
    X = sobol_points(2**m, FIX)
    geo = geometric_asian_price(S0, K, R, SIGMA, T, FIX)
    out = np.empty((reps, m + 1, 2))
    for rep in range(reps):
        a, g = _payoffs(owen_scramble(X, seed + rep), bridge)
        ca, cg = np.cumsum(a), np.cumsum(g)
        for k in range(m + 1):
            n = 2**k
            out[rep, k, 0] = ca[n - 1] / n
            out[rep, k, 1] = (ca[n - 1] - cg[n - 1]) / n + geo      # control variate with beta = 1
    return out


def table(m: int = 14, reps: int = 32) -> dict:
    """Variance of each estimator at n = 2^m paths (equal payoff evaluations), and the factor over plain MC."""
    n = 2**m
    geo = geometric_asian_price(S0, K, R, SIGMA, T, FIX)
    p = plain(n)
    cv = control_variate(p["a"], p["g"], geo)
    an = antithetic(n // 2)
    rb = rqmc_replicates(m, reps, bridge=True)
    ri = rqmc_replicates(m, reps, bridge=False)
    v_plain = p["var"] / n
    rows = {"plain": v_plain, "antithetic": an["var_pair"] / (n // 2), "control variate": cv["se"] ** 2,
            "rqmc increments": float(ri[:, m, 0].var(ddof=1)),
            "rqmc bridge": float(rb[:, m, 0].var(ddof=1)), "rqmc bridge + cv": float(rb[:, m, 1].var(ddof=1))}
    return {"n": n, "var": rows, "factor": {k: v_plain / v for k, v in rows.items()},
            "price": float(rb[:, m, 1].mean()),
            "price_se": float(rb[:, m, 1].std(ddof=1) / math.sqrt(reps)), "rho_cv": cv["rho"], "beta": cv["beta"],
            "rho_anti": an["rho"], "geo": geo, "plain_est": p["est"], "plain_se": math.sqrt(v_plain)}


def error_vs_cost(m: int = 15, reps: int = 16) -> list[tuple]:
    """Standard error against the number of paths for plain MC, the control variate, RQMC (bridge) and RQMC
    (bridge) + control variate. Plain and CV standard errors are s / sqrt(n) from 2^m Philox paths."""
    geo = geometric_asian_price(S0, K, R, SIGMA, T, FIX)
    p = plain(2**m, stream=2)
    cv = control_variate(p["a"], p["g"], geo)
    rb = rqmc_replicates(m, reps, bridge=True)
    ri = rqmc_replicates(m, reps, bridge=False)
    rows = []
    for k in range(6, m + 1):
        n = 2**k
        rows.append((n, math.sqrt(p["var"] / n), float(cv["z"].std(ddof=1)) / math.sqrt(n),
                     float(ri[:, k, 0].std(ddof=1)), float(rb[:, k, 0].std(ddof=1)), float(rb[:, k, 1].std(ddof=1))))
    return rows


def points_2d(n: int = 256, seed: int = 7) -> dict:
    return {"prng": philox_uniforms(n, 2, seed), "sobol": owen_scramble(sobol_points(n, 2), seed)}


# --- discretisation --------------------------------------------------------------------------------------

def orders(steps=(2, 4, 8, 16, 32, 64, 128, 256), n_paths: int = 20_000, seed: int = 4, mu: float = 0.05,
           sigma: float = 0.5) -> list[tuple]:
    """Strong error E|X_T^h - X_T| of Euler and Milstein for GBM driven by the same increments, and the weak
    error of the mean |E X_T^h - E X_T| = X_0 |(1 + mu h)^n - e^{mu T}| (exact for both schemes)."""
    rng = np.random.default_rng(seed)
    nmax = max(steps)
    dW = rng.standard_normal((n_paths, nmax)) * math.sqrt(T / nmax)
    exact = S0 * np.exp((mu - 0.5 * sigma**2) * T + sigma * dW.sum(axis=1))
    rows = []
    for n in steps:
        h = T / n
        inc = dW.reshape(n_paths, n, nmax // n).sum(axis=2)
        xe = np.full(n_paths, S0)
        xm = np.full(n_paths, S0)
        for k in range(n):
            d = inc[:, k]
            xe = xe * (1 + mu * h + sigma * d)
            xm = xm * (1 + mu * h + sigma * d + 0.5 * sigma**2 * (d * d - h))
        rows.append((n, float(np.abs(xe - exact).mean()), float(np.abs(xm - exact).mean()),
                     abs(S0 * ((1 + mu * h) ** n - math.exp(mu * T)))))
    return rows


def slope(x, y) -> float:
    return float(np.polyfit(np.log(x), np.log(y), 1)[0])


# --- multilevel -----------------------------------------------------------------------------------------

def bs_call(S: float, Kk: float, r: float, sigma: float, tau: float) -> float:
    d1 = (math.log(S / Kk) + (r + 0.5 * sigma**2) * tau) / (sigma * math.sqrt(tau))
    n = lambda x: 0.5 * math.erfc(-x / math.sqrt(2))  # noqa: E731
    return S * n(d1) - Kk * math.exp(-r * tau) * n(d1 - sigma * math.sqrt(tau))


def make_sampler(seed: int = 11, sigma: float = 0.25):
    """Level l: Milstein on 2^l steps (fine) coupled with 2^(l-1) steps (coarse) on the same Brownian path;
    the discounted call payoff. Cost of one sample: 2^l fine steps."""
    rng = np.random.default_rng(seed)

    def step(x, d, h):
        return x * (1 + R * h + sigma * d + 0.5 * sigma**2 * (d * d - h))

    def sampler(lev: int, n: int):
        out = np.empty(n)
        for i0 in range(0, n, 50_000):
            b = min(50_000, n - i0)
            nf = 2**lev
            hf = T / nf
            dW = rng.standard_normal((b, nf)) * math.sqrt(hf)
            xf = np.full(b, S0)
            for k in range(nf):
                xf = step(xf, dW[:, k], hf)
            pf = math.exp(-R * T) * np.maximum(xf - K, 0.0)
            if lev == 0:
                out[i0:i0 + b] = pf
                continue
            dc = dW[:, 0::2] + dW[:, 1::2]
            xc = np.full(b, S0)
            for k in range(nf // 2):
                xc = step(xc, dc[:, k], 2 * hf)
            out[i0:i0 + b] = pf - math.exp(-R * T) * np.maximum(xc - K, 0.0)
        return out, float(2**lev)

    return sampler


def mlmc_study(eps_list=(0.04, 0.02, 0.01, 0.005)) -> list[dict]:
    """MLMC cost against the cost of standard Monte Carlo at the same finest level and the same RMSE."""
    rows = []
    for i, eps in enumerate(eps_list):
        res = mlmc(make_sampler(11 + i), eps, L0=2, N0=10_000, alpha=1.0)
        L = res["L"]
        y, _ = make_sampler(99)(0, 200_000)
        # variance of the fine payoff at level L is close to the level-0 payoff variance
        std_cost = 2 * float(y.var()) / eps**2 * 2**L
        rows.append({"eps": eps, "L": L, "N": res["N"], "V": res["V"], "est": res["est"], "cost": res["cost"],
                     "std_cost": std_cost, "ratio": std_cost / res["cost"]})
    return rows


# --- importance sampling --------------------------------------------------------------------------------

THETAS = tuple(0.2 * k for k in range(26))


def digital_is(thetas=THETAS, n: int = 100_000, strike: float = 250.0, seed: int = 8) -> dict:
    """P(S_T > strike) by sampling Z ~ N(theta, 1) with likelihood ratio exp(-theta Z + theta^2 / 2)."""
    zstar = (math.log(strike / S0) - (R - 0.5 * SIGMA**2) * T) / (SIGMA * math.sqrt(T))
    exact = 0.5 * math.erfc(zstar / math.sqrt(2))
    rng = np.random.default_rng(seed)
    base = rng.standard_normal(n)
    rows = []
    for th in thetas:
        z = base + th
        y = (z > zstar) * np.exp(-th * z + 0.5 * th * th)
        rows.append((float(th), float(y.mean()), float(y.std(ddof=1) / math.sqrt(n) / exact)))
    return {"zstar": zstar, "exact": exact, "rows": rows}
