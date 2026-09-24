"""Chapter 4 of Book 4: stochastic differential equations.

The overnight NaN: plain Euler steps of a square-root variance process that violates the Feller
condition; exact and full-truncation schemes; Ornstein-Uhlenbeck paths and half-lives; stationary
laws against the Kolmogorov forward equation; Feynman-Kac for a discount factor under a mean-
reverting short rate."""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/mcengine"))
from firm_mcengine import feller_ratio, ou_exact, sqrt_euler, sqrt_exact

DESK = {"v0": 0.04, "kappa": 2.0, "vbar": 0.04, "eta": 0.6}     # the desk's calibrated variance process


def negative_fraction(eta: float, steps_per_year: int = 252, n_paths: int = 20_000, seed: int = 1,
                      kappa: float = 2.0, vbar: float = 0.04, v0: float = 0.04, years: float = 1.0) -> float:
    """Share of plain-Euler paths that produce a negative variance (hence a NaN) within `years`."""
    v = sqrt_euler(v0, kappa, vbar, eta, years, int(steps_per_year * years), n_paths, seed)
    return float(np.isnan(v).any(axis=1).mean())


def feller_table(etas=(0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.6, 0.7, 0.8, 1.0)) -> list[tuple]:
    rows = []
    for i, eta in enumerate(etas):
        rows.append((feller_ratio(2.0, 0.04, eta), negative_fraction(eta, seed=10 + i),
                     negative_fraction(eta, steps_per_year=252 * 4, n_paths=10_000, seed=30 + i)))
    return rows


def stationary_gamma(v, kappa: float, vbar: float, eta: float):
    """Density of the square-root process' stationary law: Gamma(shape 2 kappa vbar / eta^2,
    scale eta^2 / (2 kappa)), the solution of L* p = 0."""
    k, th = 2 * kappa * vbar / eta**2, eta**2 / (2 * kappa)
    v = np.asarray(v, dtype=float)
    return v ** (k - 1) * np.exp(-v / th) / (math.gamma(k) * th**k)


def gamma_cdf(x: float, shape: float, scale: float) -> float:
    """Regularised lower incomplete gamma P(shape, x / scale) by its power series (x / scale < 50)."""
    y = x / scale
    if y <= 0:
        return 0.0
    term = 1.0 / shape
    total = term
    n = 0
    while term > 1e-17 * total:
        n += 1
        term *= y / (shape + n)
        total += term
    return total * math.exp(-y + shape * math.log(y) - math.lgamma(shape))


def stationary_histograms(n_paths: int = 50_000, seed: int = 4) -> dict:
    """Long exact simulations of the desk's process and of one with Feller ratio 2."""
    out = {}
    for name, eta in (("desk", 0.6), ("feller2", 0.2)):
        v = sqrt_exact(0.04, 2.0, 0.04, eta, 5.0, 10, n_paths, seed)[:, -1]
        edges = np.linspace(0, 0.16, 33)
        h = np.histogram(v, bins=edges)[0] / (v.size * np.diff(edges))      # share of all paths, not of those in range
        mids = 0.5 * (edges[1:] + edges[:-1])
        k, th = 2 * 2.0 * 0.04 / eta**2, eta**2 / (2 * 2.0)
        cdf = np.array([gamma_cdf(e, k, th) for e in edges])
        out[name] = (mids, h, np.diff(cdf) / np.diff(edges), float((v < 0.004).mean()), gamma_cdf(0.004, k, th))
    return out


def ou_half_life(kappa: float) -> float:
    return math.log(2) / kappa


def bond_price_mc(r0=0.03, kappa=0.5, rbar=0.04, sigma=0.01, T=5.0, n_steps=500, n_paths=20_000, seed=6):
    """E[exp(-int_0^T r dt)] under an Ornstein-Uhlenbeck short rate, by simulation (trapezoid rule)."""
    r = ou_exact(r0, kappa, rbar, sigma, T, n_steps, n_paths, seed)
    integral = (r[:, :-1] + r[:, 1:]).sum(axis=1) * 0.5 * T / n_steps
    d = np.exp(-integral)
    return float(d.mean()), float(d.std() / math.sqrt(n_paths))


def bond_price_pde(r0=0.03, kappa=0.5, rbar=0.04, sigma=0.01, T=5.0) -> float:
    """Feynman-Kac: u = exp(A(tau) - B(tau) r) solves u_t + kappa (rbar - r) u_r + sigma^2/2 u_rr - r u = 0,
    with B = (1 - e^{-kappa tau}) / kappa and A = (rbar - sigma^2 / (2 kappa^2)) (B - tau) - sigma^2 B^2 / (4 kappa)."""
    B = (1 - math.exp(-kappa * T)) / kappa
    A = (rbar - sigma**2 / (2 * kappa**2)) * (B - T) - sigma**2 * B**2 / (4 * kappa)
    return math.exp(A - B * r0)


def problem() -> dict:
    d = DESK
    fr = feller_ratio(d["kappa"], d["vbar"], d["eta"])
    out = {"feller": fr, "stat_mean": d["vbar"], "stat_sd": math.sqrt(d["vbar"] * d["eta"] ** 2 / (2 * d["kappa"])),
           "half_life": ou_half_life(d["kappa"]),
           "neg_daily": negative_fraction(d["eta"], 252, 40_000, seed=101),
           "neg_4x": negative_fraction(d["eta"], 1008, 20_000, seed=102),
           "neg_16x": negative_fraction(d["eta"], 4032, 5_000, seed=103),
           "neg_weekly": negative_fraction(d["eta"], 52, 40_000, seed=104)}
    ft = sqrt_euler(d["v0"], d["kappa"], d["vbar"], d["eta"], 1.0, 252, 20_000, seed=105, scheme="full_truncation")
    ex = sqrt_exact(d["v0"], d["kappa"], d["vbar"], d["eta"], 1.0, 252, 20_000, seed=106)
    out.update({"ft_mean": float(ft[:, -1].mean()), "ex_mean": float(ex[:, -1].mean()),
                "ft_zero_share": float((ft[:, 1:] == 0).mean()), "ex_min": float(ex.min()),
                "eta_for_feller": math.sqrt(2 * d["kappa"] * d["vbar"])})
    # a day's step from v near zero: P(v_{k+1} < 0 | v_k = v) = Phi(-(v + kappa (vbar - v) dt) / (eta sqrt(v dt)))
    v, dt = 0.004, 1 / 252
    z = (v + d["kappa"] * (d["vbar"] - v) * dt) / (d["eta"] * math.sqrt(v * dt))
    out["p_neg_step_from_0004"] = 0.5 * math.erfc(z / math.sqrt(2))
    return out
