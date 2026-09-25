"""firm.sysmacro -- value, momentum, carry and macro-surprise signals across countries (build of Book 9, ch. 16).

On firm.synthfut's equity, bond and currency markets (ten countries, one market of each class per country), two
more planted effects: a valuation gap per market that mean-reverts over years (its reversion is the value premium;
the price includes the gap), and an economic-surprise index per country that mean-reverts over months and moves the
country's markets the next days (equities and the currency up, bonds down when surprises are positive), observed with
noise. Four signals, each traded long-short within each asset class every month: value (minus the price's gap to a
fair-value anchor that each market's analyst gets wrong by a persistent error),
momentum (the twelve-month return, skipping the last month), carry (firm.synthfut's carry) and surprise (the observed
index); each is scaled to a target volatility on its own trailing volatility, and the combination gives each an equal
risk budget. NumPy only.

API (stable):
    MacroConfig(...)                           parameters (seed 139)
    macro_market(cfg)                          dict: r (T, 30) daily returns with the planted effects, carry, cls,
                                               country, gap, surprise and observed surprise
    signal(m, name, t)                         (30,) signal on day t: value, reversal, momentum, carry, surprise
    portfolio(m, name, cfg)                    (T,) daily returns of one signal's long-short book, vol-targeted
    combine(books, cfg)                        (T,) equal-risk combination of several books
"""
from __future__ import annotations

import math
import pathlib
import sys
from dataclasses import dataclass

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "synthfut"))
from firm_synthfut import YEAR, FutConfig, simulate_futures  # noqa: E402


@dataclass(frozen=True)
class MacroConfig:
    seed: int = 139
    trend_half_life: float = 252.0     # firm.synthfut's drift half-life (days)
    gap_sd: float = 0.10          # stationary sd of the valuation gap (log)
    gap_half_life: float = 3.0    # years
    surprise_half_life: float = 60.0   # days
    surprise_beta: tuple = (0.04, -0.03, 0.03)   # expected annual return per unit surprise: equity, bond, currency
    surprise_noise: float = 0.5   # noise in the observed surprise index
    anchor_noise: float = 0.10    # sd of each market's persistent error in the fair-value anchor
    every: int = 21
    target_vol: float = 0.10
    lookback: int = 63


def macro_market(cfg: MacroConfig | None = None) -> dict:
    cfg = cfg or MacroConfig()
    F = simulate_futures(FutConfig(trend_half_life=cfg.trend_half_life))
    keep = F["cls"] < 3
    r, carry, cls = F["r"][:, keep].copy(), F["carry"][:, keep], F["cls"][keep]
    T, N = r.shape
    country = np.concatenate([np.arange(10)] * 3)
    rng = np.random.default_rng(cfg.seed)
    phi = 0.5 ** (1 / (cfg.gap_half_life * YEAR))
    gap = np.empty((T, N))
    gap[0] = cfg.gap_sd * rng.standard_normal(N)
    for t in range(1, T):
        gap[t] = phi * gap[t - 1] + cfg.gap_sd * math.sqrt(1 - phi * phi) * rng.standard_normal(N)
    ps = 0.5 ** (1 / cfg.surprise_half_life)
    s = np.empty((T, 10))
    s[0] = rng.standard_normal(10)
    for t in range(1, T):
        s[t] = ps * s[t - 1] + math.sqrt(1 - ps * ps) * rng.standard_normal(10)
    beta = np.array(cfg.surprise_beta)[cls]
    r[1:] += np.diff(gap, axis=0) + beta * s[:-1, country] / YEAR
    seen = s + cfg.surprise_noise * rng.standard_normal(s.shape)
    anchor = gap + cfg.anchor_noise * rng.standard_normal(N)                # each market's model error, persistent
    return {"r": r, "carry": carry, "cls": cls, "country": country, "gap": gap, "surprise": s, "seen": seen,
            "logp": np.cumsum(r, axis=0), "spot": np.cumsum(r - carry / YEAR, axis=0), "anchor_gap": anchor}


def signal(m: dict, name: str, t: int):
    lp = m["logp"]
    if name == "value":                                                  # price against a noisy fundamental anchor
        return -m["anchor_gap"][t]
    if name == "reversal":                                               # value from prices: minus the 5-year spot move
        return -(m["spot"][t] - m["spot"][t - 5 * YEAR])
    if name == "momentum":
        return lp[t - 21] - lp[t - YEAR]
    if name == "carry":
        return m["carry"][t]
    return m["seen"][t, m["country"]]


def _within_class(x, cls):
    """Cross-sectional ranks within each class, centred and scaled to unit gross exposure per class."""
    w = np.zeros_like(x, dtype=float)
    for c in np.unique(cls):
        idx = np.where(cls == c)[0]
        rk = np.argsort(np.argsort(x[idx])).astype(float)
        rk -= rk.mean()
        w[idx] = rk / np.abs(rk).sum()
    return w


def portfolio(m: dict, name: str, cfg: MacroConfig | None = None) -> np.ndarray:
    cfg = cfg or MacroConfig()
    r = m["r"]
    T, N = r.shape
    start = 5 * YEAR + 1
    raw = np.zeros(T)
    w = np.zeros(N)
    for t in range(start, T):
        if (t - start) % cfg.every == 0:
            w = _within_class(signal(m, name, t - 1), m["cls"])
        raw[t] = w @ r[t]
    out = np.zeros(T)
    for t in range(start + cfg.lookback, T):
        vol = raw[t - cfg.lookback:t].std() * math.sqrt(YEAR)
        out[t] = raw[t] * (cfg.target_vol / vol if vol > 0 else 0.0)
    return out


def combine(books: list, cfg: MacroConfig | None = None) -> np.ndarray:
    cfg = cfg or MacroConfig()
    x = np.mean(np.vstack(books), axis=0)
    out = np.zeros_like(x)
    first = int(np.argmax(np.all(np.vstack(books) != 0, axis=0)))      # once every book is trading
    for t in range(first + cfg.lookback, len(x)):
        vol = x[t - cfg.lookback:t].std() * math.sqrt(YEAR)
        out[t] = x[t] * (cfg.target_vol / vol if vol > 0 else 0.0)
    return out
