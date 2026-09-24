"""Chapter 9 of Book 4: stochastic control.

Merton's problem for a fund: the optimal constant fraction, the certainty-equivalent cost of other
fractions and of not rebalancing, the discrete-time dynamic programme that confirms the closed
form, and the vanishing-viscosity limit of a value function with a kink."""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/dpsolve"))
from firm_dpsolve import backward_induction, gauss_hermite_normal

MU, R, SIGMA, GAMMA = 0.07, 0.02, 0.18, 3.0          # the fund's assumptions (per year)


def merton_fraction(mu=MU, r=R, sigma=SIGMA, gamma=GAMMA) -> float:
    return (mu - r) / (gamma * sigma**2)


def ce_rate(pi: float, mu=MU, r=R, sigma=SIGMA, gamma=GAMMA) -> float:
    """Certainty-equivalent return per year of a constant fraction pi (continuous rebalancing)."""
    return r + pi * (mu - r) - 0.5 * gamma * pi**2 * sigma**2


def crra(w, gamma=GAMMA):
    w = np.asarray(w, dtype=float)
    return np.log(w) if gamma == 1 else w ** (1 - gamma) / (1 - gamma)


def ce_from_utility(eu: float, horizon: float, gamma=GAMMA) -> float:
    """Annualised certainty-equivalent return of an expected utility of terminal wealth (w0 = 1)."""
    w = math.exp(eu) if gamma == 1 else ((1 - gamma) * eu) ** (1 / (1 - gamma))
    return math.log(w) / horizon


def simulate_strategies(years: int = 10, steps_per_year: int = 252, n: int = 20_000, seed: int = 1,
                        pi0: float = 0.60) -> dict:
    """Terminal wealth of: constant 60% rebalanced daily, Merton rebalanced daily, buy-and-hold
    starting at 60%. Exact lognormal steps for the stock; the rest earns r."""
    rng = np.random.default_rng(seed)
    dt = 1 / steps_per_year
    pm = merton_fraction()
    w60 = np.ones(n)
    wm = np.ones(n)
    stock = np.full(n, pi0)
    cash = np.full(n, 1 - pi0)
    for _ in range(years * steps_per_year):
        g = np.exp((MU - 0.5 * SIGMA**2) * dt + SIGMA * math.sqrt(dt) * rng.standard_normal(n)) - 1
        w60 *= 1 + R * dt + pi0 * (g - R * dt)
        wm *= 1 + R * dt + pm * (g - R * dt)
        stock *= 1 + g
        cash *= 1 + R * dt
    bh = stock + cash
    out = {}
    for name, w in (("const60", w60), ("merton", wm), ("buyhold", bh)):
        out[name] = ce_from_utility(float(np.mean(crra(w))), years)
    out["weight_bh_p10"] = float(np.quantile(stock / bh, 0.1))
    out["weight_bh_p90"] = float(np.quantile(stock / bh, 0.9))
    return out


def dp_merton(years: int = 10, n_nodes: int = 20, gamma=GAMMA) -> dict:
    """Annual rebalancing, CRRA utility of wealth after `years`: backward induction over a log-wealth
    grid with the fraction in the stock chosen on a grid of 0 to 1.5 by steps of 0.005."""
    grid = np.linspace(math.log(0.05), math.log(50.0), 241)
    controls = np.linspace(0.0, 1.5, 301)
    z, wz = gauss_hermite_normal(n_nodes)
    gross = np.exp(MU - 0.5 * SIGMA**2 + SIGMA * z)                  # one year's stock return factor

    def transition(t, x, u):
        port = 1 + R + u[..., None] * (gross - 1 - R)                # (states, controls, nodes)
        return x[..., None] + np.log(np.maximum(port, 1e-12)), wz

    res = backward_induction(grid, controls, years, lambda t, x, u: 0.0 * x, transition,
                             lambda x: crra(np.exp(x), gamma))
    inner = (grid > math.log(0.3)) & (grid < math.log(10.0))
    return {"policy0": res["policy"][0], "grid": grid, "inner": inner,
            "pi_dp": float(np.median(res["policy"][0][inner])),
            "pi_dp_spread": float(np.ptp(res["policy"][0][inner])),
            "pi_dp_last": float(np.median(res["policy"][-1][inner]))}


def discrete_merton(n_nodes: int = 40, gamma=GAMMA) -> float:
    """The one-period optimum with annual lognormal returns, by golden-section search on E[U]."""
    z, wz = gauss_hermite_normal(n_nodes)
    gross = np.exp(MU - 0.5 * SIGMA**2 + SIGMA * z)

    def f(u):
        return float(crra(1 + R + u * (gross - 1 - R), gamma) @ wz)

    a, b = 0.0, 1.5
    g = (math.sqrt(5) - 1) / 2
    for _ in range(80):
        c, d = b - g * (b - a), a + g * (b - a)
        if f(c) > f(d):
            b = d
        else:
            a = c
    return 0.5 * (a + b)


def viscosity_profile(eps: float, x):
    """Solution of -eps u'' + |u'| = 1 on (-1, 1), u(+-1) = 0: tends to 1 - |x| as eps -> 0."""
    x = np.asarray(x, dtype=float)
    return 1 - np.abs(x) + eps * (math.exp(-1 / eps) - np.exp(-np.abs(x) / eps))


def problem() -> dict:
    pm = merton_fraction()
    sim = simulate_strategies()
    dp = dp_merton()
    return {
        "pi_star": pm, "ce_star": ce_rate(pm), "ce_60": ce_rate(0.60),
        "loss_60_bp": 1e4 * (ce_rate(pm) - ce_rate(0.60)),
        "loss_52_bp": 1e4 * (ce_rate(pm) - ce_rate(0.52)), "kelly": merton_fraction(gamma=1.0),
        "pi_gamma2": merton_fraction(gamma=2.0), "pi_gamma5": merton_fraction(gamma=5.0),
        "pi_mu6": merton_fraction(mu=0.06), "pi_mu8": merton_fraction(mu=0.08),
        "ce_const60_sim": sim["const60"], "ce_merton_sim": sim["merton"], "ce_buyhold_sim": sim["buyhold"],
        "bh_cost_bp": 1e4 * (sim["const60"] - sim["buyhold"]),
        "w_bh_p10": sim["weight_bh_p10"], "w_bh_p90": sim["weight_bh_p90"],
        "pi_dp": dp["pi_dp"], "pi_dp_spread": dp["pi_dp_spread"], "pi_discrete": discrete_merton(),
        "buy_after_fall": 0.60 - 0.52,
    }
