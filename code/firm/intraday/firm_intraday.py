"""firm.intraday -- the trading day in half-hour bars (build of One Quant Book 8, chapter 13).

A day model for index-level studies: an overnight return, thirteen half-hour returns (the last one the closing half
hour), a U-shaped volume curve, dealers who are short gamma and hedge in the last half hour in the direction of the
day's move (so that the last half hour's return follows the rest of the day's), and a closing-auction imbalance that
pushes the close and partly reverts overnight. Decomposition of returns into overnight and intraday parts, and the
last-half-hour regression. NumPy only.

API (stable):
    DayConfig(...)                                 the day model's parameters
    simulate_days(n, cfg, rng)                     {'overnight' (n,), 'bars' (n, 13), 'imbalance' (n,), 'volume' (13,)}
    decompose(open_, close)                        (overnight log returns, intraday log returns) from prices
    last_half_hour(bars, overnight)                (slope, t) of the last bar on the rest of the day's return
    volume_curve(bars, u)                          U-shaped share of daily volume by bar
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

BARS = 13


@dataclass(frozen=True)
class DayConfig:
    mu: float = 0.07                   # annual expected log return, spread in proportion to variance
    vol: float = 0.16                  # annual volatility
    night_share: float = 0.25          # share of the daily variance that arrives overnight
    u: float = 1.5                     # U-shape of volume and volatility across the day
    gamma: float = 0.0                 # dealers' hedging in the last half hour, per unit of the rest of day's return
    imbalance_impact: float = 0.001    # close push per unit (standard deviation) of closing imbalance
    imbalance_revert: float = 0.6      # share of the push reversed overnight
    hedge_revert: float = 0.5          # share of the hedging push reversed the next day


def volume_curve(bars: int = BARS, u: float = 1.5):
    x = np.linspace(-1, 1, bars)
    w = 1 + u * x**2
    return w / w.sum()


def simulate_days(n: int, cfg: DayConfig | None = None, rng=None):
    cfg = cfg or DayConfig()
    rng = rng or np.random.default_rng(13)
    var_d = cfg.vol**2 / 252
    w = volume_curve(BARS, cfg.u)
    sd_bar = np.sqrt((1 - cfg.night_share) * var_d * w)
    sd_on = math.sqrt(cfg.night_share * var_d)
    mu_d = cfg.mu / 252
    on = mu_d * cfg.night_share + sd_on * rng.standard_normal(n)
    bars = mu_d * (1 - cfg.night_share) * w + sd_bar * rng.standard_normal((n, BARS))
    imb = rng.standard_normal(n)
    rest = on + bars[:, :-1].sum(axis=1)
    hedge = cfg.gamma * rest                                     # short-gamma dealers buy after rises, sell after falls
    bars[:, -1] += hedge + cfg.imbalance_impact * imb
    on[1:] -= cfg.imbalance_revert * cfg.imbalance_impact * imb[:-1] + cfg.hedge_revert * hedge[:-1]
    return {"overnight": on, "bars": bars, "imbalance": imb, "volume": w}


def decompose(open_, close):
    o, c = np.log(np.asarray(open_, float)), np.log(np.asarray(close, float))
    return o[1:] - c[:-1], c - o


def last_half_hour(bars, overnight):
    b = np.asarray(bars, float)
    x = np.asarray(overnight, float) + b[:, :-1].sum(axis=1)
    y = b[:, -1]
    slope, icpt = np.polyfit(x, y, 1)
    e = y - icpt - slope * x
    se = math.sqrt(e.var(ddof=2) / ((x - x.mean()) ** 2).sum())
    return float(slope), float(slope / se)
