"""firm.synthvol -- a synthetic index option market (build of One Quant Book 9, chapter 1).

An equity index made of `members` stocks, daily, whose truth is kept: a common factor with Heston-like stochastic
variance (mean reversion, volatility of variance, a leverage correlation), negative jumps and planted crash
episodes; each member adds a specific return. Implied volatilities are set from the truth: the index's at-the-money
implied variance for a maturity is the expected integrated variance times (1 + vrp), members' with a smaller
premium, so that implied correlation exceeds the correlation that follows (a correlation premium); a skew and a
curvature in standardised moneyness shape each smile. Options are priced by Black-Scholes at the surface's vol.
Rates and dividends are zero. NumPy only.

API (stable):
    VolConfig(...)                       parameters (defaults: 20 years of 252 days, 30 members, seed 91)
    simulate_vol(cfg) -> dict            r (T,) index log returns, v (T,) factor variance (annual, truth), R (T, N)
                                         member log returns, spec (N,) specific vols, crashes [(start, end)]
    expected_var(v0, cfg, tau)           E[integrated factor variance] / tau under the variance dynamics (annual)
    atm_iv(v0, cfg, tau, member)         at-the-money implied vol of the index (member False) or a member
    smile_iv(atm, k, tau, cfg)           vol at log-moneyness k: atm (1 + skew x + curv x^2), x = k / (atm sqrt tau)
    bs_price(S, K, tau, vol, right)      Black-Scholes price with zero rates (vectorised)
    bs_delta(S, K, tau, vol, right)      Black-Scholes delta (vectorised)
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

YEAR = 252
_erfc = np.frompyfunc(math.erfc, 1, 1)


def _ncdf(x):
    return 0.5 * np.asarray(_erfc(-np.asarray(x, float) / math.sqrt(2)), float)


@dataclass(frozen=True)
class VolConfig:
    days: int = 20 * YEAR
    members: int = 30
    seed: int = 91
    theta: float = 0.16**2        # long-run annual variance of the common factor
    kappa: float = 4.0            # mean reversion of variance, per year
    xi: float = 0.5               # volatility of variance
    rho: float = -0.7             # correlation of variance shocks with returns (leverage)
    mu: float = 0.06              # expected annual return of the factor
    jump_rate: float = 1.0        # negative jumps a year
    jump_mean: float = -0.03
    jump_sd: float = 0.02
    crashes: tuple = ((1500, -0.25), (3200, -0.20), (4400, -0.30))   # (start day, total fall)
    crash_days: int = 10
    crash_var: float = 0.60**2    # factor variance jumps to this at a crash's start
    spec_vol: float = 0.25        # median specific volatility of members
    vrp: float = 0.30             # index implied variance = expected variance x (1 + vrp)
    member_vrp: float = 0.10      # members' premium (smaller: a correlation premium)
    skew: float = -0.12           # smile slope per unit of standardised moneyness
    curv: float = 0.02            # smile curvature


def expected_var(v0, cfg: VolConfig, tau):
    """Mean integrated variance over tau years divided by tau, jumps included (annual units)."""
    k = cfg.kappa * np.asarray(tau, float)
    diff = np.where(k > 1e-12, (1 - np.exp(-k)) / np.maximum(k, 1e-12), 1.0)
    jumps = cfg.jump_rate * (cfg.jump_mean**2 + cfg.jump_sd**2)
    return cfg.theta + (np.asarray(v0, float) - cfg.theta) * diff + jumps


def atm_iv(v0, cfg: VolConfig, tau, member: bool = False, spec=None):
    ev = expected_var(v0, cfg, tau)
    if member:
        return np.sqrt((ev + np.asarray(spec, float) ** 2) * (1 + cfg.member_vrp))
    return np.sqrt(ev * (1 + cfg.vrp))


def smile_iv(atm, k, tau, cfg: VolConfig):
    x = np.asarray(k, float) / (np.asarray(atm, float) * np.sqrt(tau))
    return np.asarray(atm, float) * np.maximum(1 + cfg.skew * x + cfg.curv * x * x, 0.2)


def bs_price(S, K, tau, vol, right="C"):
    S, K, vol = (np.asarray(a, float) for a in (S, K, vol))
    sd = vol * np.sqrt(tau)
    d1 = (np.log(S / K) + 0.5 * sd * sd) / sd
    d2 = d1 - sd
    call = S * _ncdf(d1) - K * _ncdf(d2)
    return call if right == "C" else call - S + K


def bs_delta(S, K, tau, vol, right="C"):
    S, K, vol = (np.asarray(a, float) for a in (S, K, vol))
    sd = vol * np.sqrt(tau)
    d1 = (np.log(S / K) + 0.5 * sd * sd) / sd
    return _ncdf(d1) - (0.0 if right == "C" else 1.0)


def simulate_vol(cfg: VolConfig | None = None) -> dict:
    cfg = cfg or VolConfig()
    rng = np.random.default_rng(cfg.seed)
    T, N, dt = cfg.days, cfg.members, 1 / YEAR
    v = np.empty(T)
    r = np.empty(T)
    starts = {s: move for s, move in cfg.crashes}
    drift_left, vt = 0.0, cfg.theta
    for t in range(T):
        if t in starts:
            vt = max(vt, cfg.crash_var)
            drift_left = cfg.crash_days
            crash_move = starts[t]
        z1, z2 = rng.standard_normal(2)
        zv = cfg.rho * z1 + math.sqrt(1 - cfg.rho**2) * z2
        jump = rng.normal(cfg.jump_mean, cfg.jump_sd) if rng.random() < cfg.jump_rate * dt else 0.0
        r[t] = (cfg.mu - 0.5 * vt) * dt + math.sqrt(vt * dt) * z1 + jump
        if drift_left > 0:
            r[t] += crash_move / cfg.crash_days
            drift_left -= 1
        v[t] = vt
        vt = max(vt + cfg.kappa * (cfg.theta - vt) * dt + cfg.xi * math.sqrt(vt * dt) * zv, 1e-4)
    spec = cfg.spec_vol * np.exp(0.3 * rng.standard_normal(N))
    R = r[:, None] + spec[None, :] * math.sqrt(dt) * rng.standard_normal((T, N)) - 0.5 * spec**2 * dt
    return {"r": r, "v": v, "R": R, "spec": spec,
            "crashes": [(s, s + cfg.crash_days) for s, _ in cfg.crashes]}
