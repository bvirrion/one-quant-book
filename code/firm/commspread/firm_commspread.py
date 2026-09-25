"""firm.commspread -- processing, location and quality spreads and the books that trade them (build of Book 9, ch. 21).

Spread construction by ratio (the 3-2-1 crack, the spark spread at a heat rate, the soybean board crush), and a
synthetic daily market of ten years: a crude price (log random walk), a crack spread with a seasonal cycle that
peaks before the summer driving season, a mean-reverting deviation and a planted negative response to crude moves
(product prices lag crude), a location spread (inland against seaborne crude) that mean-reverts around a level until
a planted pipeline bottleneck widens it over half a year, holds it and releases it, and a quality spread (sweet
against sour crude). Rules: fading a spread's deviation from its trailing mean (optionally after removing each
calendar month's trailing average), and a seasonal rule that holds the crack from February to April. P&L is in $/bbl
of crude per unit of spread held. NumPy.

API (stable):
    crack_321(crude, gasoline, diesel)          $/bbl, products in $/gal
    spark(power, gas, heat_rate)                $/MWh, gas in $/MMBtu, heat rate in MMBtu/MWh
    board_crush(beans, meal, oil)               $/bu: meal in $/short ton, oil in cents/lb, beans in $/bu
    SpreadConfig(...)                           parameters (seed 167)
    simulate_spreads(cfg)                       dict: crude, crack, season, location, quality (T,), month (T,)
    fade(x, cfg, month=None, delay=1)           (daily P&L, positions) of fading the deviation from the trailing mean
    seasonal(x, month, cfg)                     daily P&L of holding the spread long from February to April
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

YEAR = 252


def crack_321(crude, gasoline, diesel):
    return (2 * np.asarray(gasoline) + np.asarray(diesel)) * 42 / 3 - np.asarray(crude)


def spark(power, gas, heat_rate: float = 7.0):
    return np.asarray(power) - heat_rate * np.asarray(gas)


def board_crush(beans, meal, oil):
    """A 60 lb bushel yields about 44 lb of meal (0.022 short ton) and 11 lb of oil."""
    return 0.022 * np.asarray(meal) + 0.11 * np.asarray(oil) - np.asarray(beans)


@dataclass(frozen=True)
class SpreadConfig:
    days: int = 10 * YEAR
    seed: int = 167
    crude0: float = 75.0
    crude_vol: float = 0.35
    crack_mean: float = 20.0      # $/bbl
    season_amp: float = 5.0       # seasonal amplitude, peak in late April
    crack_sd: float = 6.0         # stationary sd of the crack's deviation ...
    crack_hl: float = 40.0        # ... and its half-life (days)
    crack_beta: float = -0.35     # crack change per $ of crude change (products lag)
    loc_mean: float = 4.0
    loc_sd: float = 2.5
    loc_hl: float = 20.0
    shock_start: int = 5 * YEAR   # a pipeline bottleneck widens the location spread's level over half a year ...
    shock_days: int = YEAR        # ... holds it for the rest of a year ...
    shock_size: float = 15.0      # ... by this much, and a new pipeline closes it over two months
    qual_mean: float = 3.0
    qual_sd: float = 1.5
    qual_hl: float = 60.0
    band: float = 1.5             # enter beyond this many sds of the trailing window
    window: int = YEAR
    cost: float = 0.10            # $/bbl per unit of spread traded


def _ou(rng, T, sd, hl):
    phi = 0.5 ** (1 / hl)
    x, e = np.empty(T), sd * math.sqrt(1 - phi * phi) * rng.standard_normal(T)
    x[0] = sd * rng.standard_normal()
    for t in range(1, T):
        x[t] = phi * x[t - 1] + e[t]
    return x


def simulate_spreads(cfg: SpreadConfig | None = None) -> dict:
    cfg = cfg or SpreadConfig()
    rng = np.random.default_rng(cfg.seed)
    T = cfg.days
    crude = cfg.crude0 * np.exp(np.cumsum(cfg.crude_vol / math.sqrt(YEAR) * rng.standard_normal(T)))
    month = (np.arange(T) % YEAR) * 12 // YEAR + 1
    season = cfg.season_amp * np.cos(2 * math.pi * ((np.arange(T) % YEAR) / YEAR - 0.31))
    dev = _ou(rng, T, cfg.crack_sd, cfg.crack_hl)
    lag = cfg.crack_beta * (crude - _ema(crude, cfg.crack_hl))            # products catch up with crude over weeks
    crack = cfg.crack_mean + season + dev + lag
    level = np.full(T, cfg.loc_mean)
    a, half = cfg.shock_start, cfg.shock_days // 2
    shock = np.concatenate([np.linspace(0, cfg.shock_size, half), np.full(cfg.shock_days - half, cfg.shock_size),
                            np.linspace(cfg.shock_size, 0, 42)])
    level[a:a + len(shock)] += shock[:max(0, min(a + len(shock), T) - a)]
    location = level + _ou(rng, T, cfg.loc_sd, cfg.loc_hl)
    quality = cfg.qual_mean + _ou(rng, T, cfg.qual_sd, cfg.qual_hl)
    return {"crude": crude, "crack": crack, "season": season, "location": location, "quality": quality,
            "month": month, "level": level}


def _ema(x, hl):
    a, out = 1 - 0.5 ** (1 / hl), np.empty(len(x))
    out[0] = x[0]
    for t in range(1, len(x)):
        out[t] = out[t - 1] + a * (x[t] - out[t - 1])
    return out


def fade(x, cfg: SpreadConfig | None = None, month=None, delay: int = 1):
    """Short the spread when it is more than `band` trailing sds above its trailing mean, long when below, out when it
    crosses the mean; with `month`, first subtract each calendar month's average over the trailing window. The
    position decided at a close earns from `delay` days later; costs per unit traded."""
    cfg = cfg or SpreadConfig()
    x = np.asarray(x, float)
    T, w = len(x), cfg.window
    y = x.copy()
    if month is not None:
        for t in range(w, T):
            past = x[t - w:t]
            y[t] = x[t] - past[month[t - w:t] == month[t]].mean() + past.mean()
    pos, cur = np.zeros(T), 0.0
    for t in range(w, T):
        past = y[t - w:t]
        z = (y[t] - past.mean()) / past.std()
        if z > cfg.band:
            cur = -1.0
        elif z < -cfg.band:
            cur = 1.0
        elif cur != 0 and np.sign(z) == cur:
            cur = 0.0
        pos[t] = cur
    held = np.concatenate([np.zeros(delay), pos[:-delay]])
    pnl = held * np.diff(x, prepend=x[0]) - cfg.cost * np.abs(np.diff(pos, prepend=0.0))
    return pnl, pos


def seasonal(x, month, cfg: SpreadConfig | None = None):
    """Long one unit of the spread from the first day of February to the last of April each year."""
    cfg = cfg or SpreadConfig()
    x = np.asarray(x, float)
    pos = ((month >= 2) & (month <= 4)).astype(float)
    held = np.concatenate([[0.0], pos[:-1]])
    return held * np.diff(x, prepend=x[0]) - cfg.cost * np.abs(np.diff(pos, prepend=0.0))
