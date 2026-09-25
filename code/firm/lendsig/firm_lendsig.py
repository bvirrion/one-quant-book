"""firm.lendsig -- a synthetic stock-lending market and short-selling signals (build of One Quant Book 8, chapter 8).

A lending layer on a price panel: each stock has a lendable supply (a share of its shares outstanding); short demand is
the sum of an informed part, proportional to how negative the stock's expected return is (short sellers who know
something), and an uninformed part (persistent noise); short interest is the demand the supply can meet; the borrow fee
rises steeply with utilisation above a threshold; loans are recalled more often when utilisation is high. Signals:
short interest as a share of shares outstanding, days to cover, the fee, and a crowding score. A squeeze stress: the
loss of a short book when short sellers in its names must cover part of their positions, priced by square-root impact.
NumPy only.

API (stable):
    LendingConfig(...)                        supply, demand, fee and recall parameters
    simulate_lending(alpha, listed, shares, cfg)
                                              {'si' (T, N) short interest / shares, 'util', 'fee' (annual), 'recall'}
    days_to_cover(si, shares, adv_shares)     short interest in days of average volume
    crowding(si, util, dtc)                   mean of the three cross-sectional ranks, in [0, 1]
    fee_of(util, cfg)                         the fee schedule
    squeeze_loss(w, si, shares, adv_shares, sigma, cover, days, eta)
                                              loss (fraction of capital) of short weights w when a share `cover` of each
                                              name's short interest is bought back over `days` days
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class LendingConfig:
    supply_median: float = 0.20        # lendable supply as a share of shares outstanding
    supply_disp: float = 0.5
    informed: float = 60.0             # informed short demand per unit of negative expected daily return (x shares)
    noise_median: float = 0.02         # uninformed short interest, median share of shares outstanding
    noise_disp: float = 0.8
    noise_phi: float = 0.99            # daily persistence of the uninformed part (log)
    smooth: float = 20.0               # half-life (days) with which informed shorts follow the expected return
    gc_fee: float = 0.0025
    fee_max: float = 0.40              # annual fee at full utilisation
    fee_start: float = 0.6             # utilisation above which the fee rises
    fee_power: float = 3.0
    recall_base: float = 0.0005        # daily recall probability of a loan
    recall_top: float = 0.02           # ... at full utilisation
    seed: int = 8


def fee_of(util, cfg: LendingConfig):
    u = np.clip(np.asarray(util, float), 0.0, 1.0)
    x = np.clip((u - cfg.fee_start) / (1 - cfg.fee_start), 0.0, 1.0)
    return cfg.gc_fee + (cfg.fee_max - cfg.gc_fee) * x**cfg.fee_power


def simulate_lending(alpha, listed, shares, cfg: LendingConfig | None = None):
    cfg = cfg or LendingConfig()
    alpha, listed = np.asarray(alpha, float), np.asarray(listed, bool)
    T, N = alpha.shape
    rng = np.random.default_rng(cfg.seed)
    supply = np.clip(cfg.supply_median * np.exp(cfg.supply_disp * rng.standard_normal(N)), 0.02, 0.6)
    lam = 0.5 ** (1 / cfg.smooth)
    a = np.zeros(N)
    z = cfg.noise_disp * rng.standard_normal(N)
    si, util, fee, recall = (np.full((T, N), np.nan) for _ in range(4))
    for t in range(T):
        a = lam * a + (1 - lam) * np.nan_to_num(alpha[t])
        z = cfg.noise_phi * z + math.sqrt(1 - cfg.noise_phi**2) * cfg.noise_disp * rng.standard_normal(N)
        demand = cfg.informed * np.maximum(-a, 0.0) + cfg.noise_median * np.exp(z)
        s = np.minimum(demand, supply)
        u = s / supply
        ok = listed[t]
        si[t, ok], util[t, ok] = s[ok], u[ok]
        fee[t, ok] = fee_of(u[ok], cfg)
        p = cfg.recall_base + (cfg.recall_top - cfg.recall_base) * np.clip((u - 0.8) / 0.2, 0, 1)
        recall[t, ok] = (rng.random(N) < p)[ok]
    return {"si": si, "util": util, "fee": fee, "recall": recall, "supply": supply}


def days_to_cover(si, shares, adv_shares):
    return np.asarray(si, float) * np.asarray(shares, float) / np.maximum(np.asarray(adv_shares, float), 1.0)


def _rank01(x):
    out = np.full(x.shape, np.nan)
    for t in range(x.shape[0]):
        ok = np.isfinite(x[t])
        if ok.sum() > 1:
            out[t, ok] = np.argsort(np.argsort(x[t, ok])) / (ok.sum() - 1)
    return out


def crowding(si, util, dtc):
    return (_rank01(np.asarray(si, float)) + _rank01(np.asarray(util, float)) + _rank01(np.asarray(dtc, float))) / 3


def squeeze_loss(w, si, shares, adv_shares, sigma, cover: float, days: int, eta: float = 0.7):
    """Square-root impact of buying back cover x si x shares over `days` days: eta sigma sqrt(Q / (days V)) per day,
    summed over the days (a price that keeps rising while the buying lasts); the loss of short weights w (< 0)."""
    q = cover * np.asarray(si, float) * np.asarray(shares, float)
    per_day = eta * np.asarray(sigma, float) * np.sqrt(q / (days * np.maximum(np.asarray(adv_shares, float), 1.0)))
    move = np.expm1(days * per_day)
    return float(np.sum(np.minimum(np.asarray(w, float), 0.0) * move))
