"""One Quant Book 10, chapter 15: execution schedules that look at the market.

    signal_study(halves, strengths)    the chapter 14 block sold over a day in 78 five-minute steps, with an alpha
                                       signal (an Ornstein-Uhlenbeck drift of given half-life and standard
                                       deviation): the basis points the Riccati schedule saves over Almgren-Chriss
                                       on common random numbers (cached)
    transient_study(rho)               under an exponential transient kernel, the cost of the time-weighted schedule,
                                       the Almgren-Chriss one and the Obizhaeva-Wang optimum with its blocks
    aim_study(a)                       an aggressive-in-the-money rule against the static schedule: mean and standard
                                       deviation of the cost
    liquidity_study()                  two liquidity regimes: the dynamic-programming policy against a schedule that
                                       ignores them
All deterministic (fixed seeds).
"""
from __future__ import annotations

import functools
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for c in ("execcontrol", "acexec", "propagator", "dpsolve"):
    sys.path.insert(0, str(ROOT / "code" / "firm" / c))
from firm_acexec import discrete  # noqa: E402
from firm_execcontrol import OWScheduler, aim, liquidity_dp, lqr_signal, simulate  # noqa: E402
from firm_propagator import impact_matrix, optimal_liquidation  # noqa: E402

PRICE, X, SIGMA = 50.0, 1_000_000, 1.0
ETA = 0.8 * 0.02 * math.sqrt(0.1) * 50.0 / 1e6              # chapter 14: dollars per share per share a day
LAM = 1e-6
N, TAU = 78, 1.0 / 78
HALVES = (0.05, 0.2, 1.0)                                   # days
STRENGTHS = (0.5, 1.0, 2.0)                                 # dollars a day (standard deviation of the drift)


def _bp(cost_per_share) -> float:
    return float(cost_per_share / PRICE * 1e4)


@functools.cache
def signal_study(halves=HALVES, strengths=STRENGTHS, paths: int = 1500) -> dict:
    ac = lqr_signal(N, TAU, ETA, SIGMA, LAM, 0.0)
    out = {}
    for h in halves:
        phi = math.exp(-math.log(2) * TAU / h)
        g = lqr_signal(N, TAU, ETA, SIGMA, LAM, phi)
        for s in strengths:
            c_ac = simulate(lambda k, x, a, dp: ac[k][0] * x, X, N, TAU, ETA, SIGMA, phi, s, seed=7, paths=paths)
            c_sig = simulate(lambda k, x, a, dp, g=g: g[k][0] * x + g[k][1] * a, X, N, TAU, ETA, SIGMA, phi, s,
                             seed=7, paths=paths)
            d = c_ac - c_sig
            out[(h, s)] = {"ac": _bp(c_ac.mean()), "signal": _bp(c_sig.mean()), "saved": _bp(d.mean()),
                           "saved_se": _bp(d.std(ddof=1) / math.sqrt(paths)), "sd_ac": _bp(c_ac.std()),
                           "sd_signal": _bp(c_sig.std())}
    return out


def transient_study(rho: float = 10.0, n: int = 100) -> dict:
    t = np.linspace(0.0, 1.0, n + 1)
    gam = impact_matrix(t, lambda x: np.exp(-rho * x))

    def cost(q):
        return float(0.5 * q @ gam @ q)
    twap = np.full(n + 1, 1.0 / (n + 1))
    ow = optimal_liquidation(gam, 1.0)
    block = OWScheduler(1.0, rho, 1.0).block
    return {"twap": cost(twap), "ow": cost(ow), "first": float(ow[0]), "last": float(ow[-1]),
            "middle": float(ow[n // 2]), "block_formula": block, "all_at_once": cost(np.eye(n + 1)[0])}


def aim_study(a: float = 0.5, paths: int = 3000, kt: float = 2.0) -> dict:
    static = aim(kt, 0.0, SIGMA, 1.0, N)
    adaptive = aim(kt, a, SIGMA, 1.0, N)
    c0 = simulate(static, X, N, TAU, ETA, SIGMA, 0.0, 0.0, seed=11, paths=paths)
    c1 = simulate(adaptive, X, N, TAU, ETA, SIGMA, 0.0, 0.0, seed=11, paths=paths)
    return {"static": (_bp(c0.mean()), _bp(c0.std())), "adaptive": (_bp(c1.mean()), _bp(c1.std())),
            "ce_static": _bp(c0.mean()) + LAM * (c0.std() * X) ** 2 / X / PRICE * 1e4,
            "ce_adaptive": _bp(c1.mean()) + LAM * (c1.std() * X) ** 2 / X / PRICE * 1e4}


def liquidity_study(n: int = 26, paths: int = 3000, dry: float = 4.0) -> dict:
    tau = 1.0 / n
    eta = (ETA, dry * ETA)
    stay = (0.9, 0.7)
    r = liquidity_dp(X, n, tau, eta, SIGMA, LAM, stay, grid=101)
    grid = r["grid"]
    static = discrete(X, 1.0, n, ETA, SIGMA, LAM)
    rng = np.random.default_rng(3)
    cost_dp, cost_st = np.empty(paths), np.empty(paths)
    for j in range(paths):
        reg = 0
        xd = xs = X
        cd = cs = 0.0
        dp = 0.0
        for k in range(n):
            e = eta[reg]
            pol = (r["policy_normal"], r["policy_dry"])[reg][k]
            ud = xd if k == n - 1 else min(xd, float(np.interp(xd, grid, pol)))
            us = xs - static[k + 1]
            cd += ud * (dp - e * ud / tau)
            cs += us * (dp - e * us / tau)
            xd -= ud
            xs -= us
            dp += SIGMA * math.sqrt(tau) * rng.standard_normal()
            reg = reg if rng.random() < stay[reg] else 1 - reg
        cost_dp[j], cost_st[j] = -cd / X, -cs / X
    d = cost_st - cost_dp
    return {"dp": _bp(cost_dp.mean()), "static": _bp(cost_st.mean()), "saved": _bp(d.mean()),
            "saved_se": _bp(d.std(ddof=1) / math.sqrt(paths)), "sd_dp": _bp(cost_dp.std()),
            "sd_static": _bp(cost_st.std()),
            "policy_mid": (float(np.interp(X / 2, grid, r["policy_normal"][n // 2])),
                           float(np.interp(X / 2, grid, r["policy_dry"][n // 2])))}


AIMS = (0.25, 0.5, 1.0, 2.0)


@functools.cache
def aim_grid(aims=AIMS) -> dict:
    return {a: aim_study(a) for a in aims}
