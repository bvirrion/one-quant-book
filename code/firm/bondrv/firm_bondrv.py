"""firm.bondrv -- government-bond relative value on a fitted curve (build of One Quant Book 9, chapter 10).

A synthetic government bond market: the curve is Nelson-Siegel in three factors (level, slope, curvature) that
follow mean-reverting daily processes; forty bonds with maturities spread from one to thirty years at the start age
a day at a time and are replaced by a new thirty-year issue when they mature; each bond's yield is the curve's at
its maturity plus a pricing error in two parts, one reverting in weeks (the rich-cheap the book trades) and one over
about a year; the analyst fits yields seen with noise (stale quotes) but trades at the true ones. Each day a
Nelson-Siegel curve (the same decay) is fitted to all yields by least squares; the residuals are the book's signal.
Positions are in DV01 (P&L in basis points of yield times DV01): long the cheapest bonds (yield above the curve),
short the richest, equal in DV01 or made neutral in the three curve factors, rebalanced weekly with a cost per unit
of DV01 traded. NumPy only.

API (stable):
    BondConfig(...)                            parameters (seed 107)
    loadings(tau, decay)                       (n, 3) Nelson-Siegel loadings for maturities tau (years)
    simulate_market(cfg)                       dict of traded and seen yields (T, n), maturities, factors, errors
    fit_residuals(yields, tau, decay)          (T, n) residuals of a daily least-squares Nelson-Siegel fit
    neutralise(w, X)                           weights with their exposures to the columns of X removed
    book(sim, cfg, hedge)                      dict of daily P&L (bp of yield per unit gross DV01), turnover, cost
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

YEAR = 252


@dataclass(frozen=True)
class BondConfig:
    days: int = 10 * YEAR
    bonds: int = 40
    seed: int = 107
    decay: float = 1.5            # Nelson-Siegel decay time (years)
    level: float = 0.04
    slope: float = -0.015
    curve: float = 0.0
    kappa: float = 0.5            # mean reversion of the factors, per year
    vols: tuple = (0.0065, 0.0070, 0.0110)   # annual vols of level, slope and curvature
    err_sd: float = 0.0002        # sd of each bond's pricing error (2 bp)
    err_half_life: float = 40.0   # its half-life in days
    slow_sd: float = 0.0002       # sd of a slow part of each bond's error (supply, index events) ...
    slow_half_life: float = 250.0 # ... with this half-life in days
    noise: float = 0.00005        # noise in the yields the analyst fits (stale quotes), not in traded prices
    cost: float = 0.25            # cost per unit of DV01 traded, in basis points of yield (a half bid-ask)
    k: int = 5                    # bonds on each side
    every: int = 5                # rebalance every so many days


def loadings(tau, decay: float):
    x = np.asarray(tau, float) / decay
    f1 = np.where(x > 1e-8, (1 - np.exp(-x)) / np.maximum(x, 1e-8), 1.0)
    return np.stack([np.ones_like(x), f1, f1 - np.exp(-x)], axis=-1)


def simulate_market(cfg: BondConfig | None = None) -> dict:
    cfg = cfg or BondConfig()
    rng = np.random.default_rng(cfg.seed)
    T, n, dt = cfg.days, cfg.bonds, 1 / YEAR
    mean = np.array([cfg.level, cfg.slope, cfg.curve])
    f = np.empty((T, 3))
    f[0] = mean
    for t in range(1, T):
        shock = np.array(cfg.vols) * math.sqrt(dt) * rng.standard_normal(3)
        f[t] = f[t - 1] + cfg.kappa * (mean - f[t - 1]) * dt + shock
    tau = np.empty((T, n))
    tau[0] = np.linspace(1.0, 30.0, n)
    for t in range(1, T):
        tau[t] = tau[t - 1] - dt
        tau[t][tau[t] <= 0.25] = 30.0                                  # matured: a new thirty-year issue
    phi = 0.5 ** (1 / cfg.err_half_life)
    e = np.empty((T, n))
    e[0] = cfg.err_sd * rng.standard_normal(n)
    for t in range(1, T):
        e[t] = phi * e[t - 1] + cfg.err_sd * math.sqrt(1 - phi * phi) * rng.standard_normal(n)
    phs = 0.5 ** (1 / cfg.slow_half_life)
    slow = np.empty((T, n))
    slow[0] = cfg.slow_sd * rng.standard_normal(n)
    for t in range(1, T):
        slow[t] = phs * slow[t - 1] + cfg.slow_sd * math.sqrt(1 - phs * phs) * rng.standard_normal(n)
    reissued = np.vstack([np.zeros(n, bool), tau[1:] > tau[:-1]])
    e[reissued] = cfg.err_sd * rng.standard_normal(int(reissued.sum()))
    slow[reissued] = cfg.slow_sd * rng.standard_normal(int(reissued.sum()))
    y = (loadings(tau, cfg.decay) * f[:, None, :]).sum(axis=-1) + e + slow
    seen = y + cfg.noise * rng.standard_normal((T, n))
    return {"y": y, "seen": seen, "tau": tau, "factors": f, "errors": e, "slow": slow, "reissued": reissued}


def fit_residuals(yields, tau, decay: float):
    X = loadings(tau, decay)
    res = np.empty_like(yields)
    for t in range(yields.shape[0]):
        beta, *_ = np.linalg.lstsq(X[t], yields[t], rcond=None)
        res[t] = yields[t] - X[t] @ beta
    return res


def neutralise(w, X):
    """Remove from w (DV01 weights) its projection on the columns of X, so that X' w = 0."""
    beta, *_ = np.linalg.lstsq(X, w, rcond=None)
    return w - X @ beta


def book(sim: dict, cfg: BondConfig | None = None, hedge: str = "factors") -> dict:
    """Every `every` days, long the k cheapest bonds (residual yield above the curve) and short the k richest, equal
    DV01 each; hedge 'none' keeps only the long side, 'dv01' both sides, 'factors' both sides with the three curve
    exposures removed using all bonds. Gross DV01 is one. P&L is minus DV01 times the yield change, in bp."""
    cfg = cfg or BondConfig()
    y, tau = sim["y"], sim["tau"]
    res = fit_residuals(sim["seen"], tau, cfg.decay)
    T, n = y.shape
    pnl, turnover = np.zeros(T), np.zeros(T)
    w = np.zeros(n)
    for t in range(1, T - 1):
        if t % cfg.every == 0 or sim["reissued"][t].any():
            order = np.argsort(res[t])
            new = np.zeros(n)
            new[order[-cfg.k:]] = 1.0
            if hedge != "none":
                new[order[:cfg.k]] = -1.0
            if hedge == "factors":
                new = neutralise(new, loadings(tau[t], cfg.decay))
            new = new / np.abs(new).sum()
            turnover[t] = np.abs(new - w).sum()
            w = new
        moved = ~sim["reissued"][t + 1]                                 # a matured bond is closed at yesterday's mark
        pnl[t + 1] = -(w[moved] * (y[t + 1, moved] - y[t, moved])).sum() * 1e4
    cost = turnover * cfg.cost
    return {"pnl": pnl, "turnover": turnover, "cost": cost, "net": pnl - np.roll(cost, 1), "residuals": res}
