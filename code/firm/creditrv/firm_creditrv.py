"""firm.creditrv -- bond-CDS basis, index against constituents, credit curves (build of One Quant Book 9, chapter 18).

Synthetic issuers, daily: each has a five-year CDS spread (a mean-reverting log process around its own level) and a
bond whose spread over the risk-free curve is the CDS spread plus a funding premium, the market's cost of financing
bonds, which is common to all issuers, plus an issuer-specific noise; the bond-CDS basis (CDS minus bond spread) is
therefore minus the funding premium, and it goes deeply negative when a planted funding crisis lifts the premium.
The negative-basis trade holds the bond financed at the trader's own funding spread with a haircut, and buys CDS
protection: it earns the basis less its funding and loses, marked at the bonds' spread duration, when the basis
widens. A CDS index trades at the average of its members' spreads plus a mean-reverting skew; a ten-year against
five-year curve slope mean-reverts around its level. NumPy only.

API (stable):
    CreditConfig(...)                          parameters (seed 151)
    simulate_credit(cfg)                       dict of CDS and bond spreads (T, N) in bp, funding premium (T,),
                                               index skew (T,), curve slope (T,)
    negative_basis(sim, cfg, own_funding)      daily P&L parts per unit notional (carry, marks) and return on capital
    index_arbitrage(sim, cfg)                  daily P&L (bp of notional) of trading the index against its members
    curve_trade(sim, cfg)                      daily P&L (bp of notional) of a DV01-matched curve trade on the slope
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

YEAR = 252


@dataclass(frozen=True)
class CreditConfig:
    days: int = 10 * YEAR
    issuers: int = 40
    seed: int = 151
    cds_level: float = 120.0      # median CDS level (bp)
    cds_disp: float = 0.5         # lognormal dispersion of issuers' levels
    cds_vol: float = 0.6          # annual vol of log CDS spreads
    cds_hl: float = 250.0         # half-life of the log CDS deviation (days)
    fund_normal: float = 15.0     # funding premium in bond spreads (bp), normally ...
    fund_stress: float = 150.0    # ... at the depth of the planted crisis
    stress_start: int = 5 * YEAR
    stress_ramp: int = 63
    stress_decay: int = YEAR
    bond_noise: float = 10.0      # issuer-specific bond-spread noise (bp), AR
    bond_noise_hl: float = 40.0
    duration: float = 4.5         # spread duration of the bond and the CDS
    haircut: float = 0.10         # repo haircut on the bond
    skew_sd: float = 4.0          # index skew (bp), AR, half-life 20 days
    skew_hl: float = 20.0
    slope_mean: float = 40.0      # ten-year minus five-year spread (bp)
    slope_sd: float = 8.0
    slope_hl: float = 60.0
    cost_bp: float = 1.0          # cost per unit of notional traded, in bp of spread (times duration: bp of notional)
    band: float = 1.0             # trade only when the skew or slope is beyond this many sds


def _ar(rng, T, n, sd, hl):
    phi = 0.5 ** (1 / hl)
    x = np.empty((T, n))
    x[0] = sd * rng.standard_normal(n)
    for t in range(1, T):
        x[t] = phi * x[t - 1] + sd * math.sqrt(1 - phi * phi) * rng.standard_normal(n)
    return x


def simulate_credit(cfg: CreditConfig | None = None) -> dict:
    cfg = cfg or CreditConfig()
    rng = np.random.default_rng(cfg.seed)
    T, N = cfg.days, cfg.issuers
    level = cfg.cds_level * np.exp(cfg.cds_disp * rng.standard_normal(N))
    lsd = cfg.cds_vol / math.sqrt(2 * math.log(2) / cfg.cds_hl * YEAR)       # stationary sd of the log deviation
    cds = level * np.exp(_ar(rng, T, N, lsd, cfg.cds_hl) - 0.5 * lsd**2)
    fund = np.full(T, cfg.fund_normal)
    a, b = cfg.stress_start, cfg.stress_start + cfg.stress_ramp
    fund[a:b] = np.linspace(cfg.fund_normal, cfg.fund_stress, b - a)
    fund[b:b + cfg.stress_decay] = np.linspace(cfg.fund_stress, cfg.fund_normal, cfg.stress_decay)[:max(0, T - b)]
    bond = cds + fund[:, None] * (level / cfg.cds_level) ** 0.5 + _ar(rng, T, N, cfg.bond_noise, cfg.bond_noise_hl)
    skew = _ar(rng, T, 1, cfg.skew_sd, cfg.skew_hl)[:, 0]
    slope = cfg.slope_mean + _ar(rng, T, 1, cfg.slope_sd, cfg.slope_hl)[:, 0]
    return {"cds": cds, "bond": bond, "fund": fund, "basis": cds - bond, "skew": skew, "slope": slope,
            "index": cds.mean(axis=1) + skew}


def negative_basis(sim: dict, cfg: CreditConfig | None = None, own_funding: float = 30.0) -> dict:
    """Hold one unit of every bond (equal weights) and CDS protection on each from day 0: daily carry is the bond spread
    less the CDS spread less the trader's funding spread on the financed part; marks are minus the spread duration
    times the change of (bond spread - CDS spread). Capital is the haircut."""
    cfg = cfg or CreditConfig()
    gap = (sim["bond"] - sim["cds"]).mean(axis=1)                        # minus the average basis, bp
    carry = (gap[:-1] - own_funding * (1 - cfg.haircut)) / 1e4 / YEAR
    marks = -cfg.duration * np.diff(gap) / 1e4
    return {"carry": carry, "marks": marks, "total": carry + marks, "on_capital": (carry + marks) / cfg.haircut}


def _banded(x, sd, band):
    """+1 or -1 once |x| passes band x sd, held until x crosses zero; 0 before the first signal."""
    pos, cur = np.zeros(len(x)), 0.0
    for t, v in enumerate(x):
        if abs(v) > band * sd:
            cur = float(np.sign(v))
        elif cur != 0 and np.sign(v) != cur:
            cur = 0.0
        pos[t] = cur
    return pos


def _trade(x, sd, cfg, sign):
    """Daily P&L (bp of notional) of trading x's reversion: short x when high (sign -1), costs on each unit traded."""
    pos = sign * _banded(x[:-1], sd, cfg.band)
    pnl = pos * cfg.duration * np.diff(x)
    return pnl - cfg.cost_bp * cfg.duration * np.abs(np.diff(np.concatenate([[0.0], pos])))


def index_arbitrage(sim: dict, cfg: CreditConfig | None = None) -> np.ndarray:
    """Sell index protection and buy it on the members when the skew is wide (index above its members), the reverse
    when it is narrow; one unit notional; bp of notional."""
    cfg = cfg or CreditConfig()
    return _trade(sim["skew"], cfg.skew_sd, cfg, -1.0)


def curve_trade(sim: dict, cfg: CreditConfig | None = None) -> np.ndarray:
    """A DV01-matched flattener when the slope is wide, a steepener when narrow; bp of notional."""
    cfg = cfg or CreditConfig()
    return _trade(sim["slope"] - cfg.slope_mean, cfg.slope_sd, cfg, -1.0)
