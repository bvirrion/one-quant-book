"""firm.drarb -- depositary receipts and dual listings (One Quant Book 11, chapter 14).

A company's shares trade at home in a foreign currency; its receipt trades in dollars, one receipt for `ratio` shares.
While both markets are open the receipt's fair value is the home price times the ratio times the exchange rate; when
the home market has closed it is the home close moved by a proxy that still trades (an index future or a
home-market fund) and by the currency.

API (stable):
    dr_fair(home, ratio, fx)                              home * ratio * fx (fx: dollars per unit of home currency)
    closed_fair(home_close, ratio, fx, proxy_move, beta)  dr_fair(home_close, ratio, fx) * (1 + beta * proxy_move)
    conversion_edge(dr, home, ratio, fx, fee_per_dr, cost_bp, days, rate)
                                                          dollars per receipt from converting: issue receipts when the
                                                          receipt is dear (buy shares, deposit, sell receipts), cancel
                                                          when it is cheap; net of the depositary fee, trading costs
                                                          and financing over the settlement lag; returns (action, edge)
    threshold_bp(dr_price, fee_per_dr, cost_bp, days, rate)
                                                          gap (basis points of the receipt) at which conversion pays
    Pair(days, seed, ...)                                 minute paths over the receipt's session: true value, home
                                                          mid (open for the first `overlap` minutes), currency, proxy
    Pair.quote(method)                                    'home' (last home mid x fx), 'proxy' (plus the proxy's move
                                                          after the home close) -> fair value path
"""
from __future__ import annotations

import math

import numpy as np

SESSION = 390


def dr_fair(home: float, ratio: float, fx: float) -> float:
    return home * ratio * fx


def closed_fair(home_close: float, ratio: float, fx: float, proxy_move: float, beta: float = 1.0) -> float:
    return dr_fair(home_close, ratio, fx) * (1.0 + beta * proxy_move)


def threshold_bp(dr_price: float, fee_per_dr: float, cost_bp: float, days: int = 2, rate: float = 0.05) -> float:
    return 1e4 * fee_per_dr / dr_price + cost_bp + 1e4 * rate * days / 360.0


def conversion_edge(dr: float, home: float, ratio: float, fx: float, fee_per_dr: float, cost_bp: float,
                    days: int = 2, rate: float = 0.05) -> tuple[str, float]:
    parity = dr_fair(home, ratio, fx)
    cost = fee_per_dr + (cost_bp * 1e-4 + rate * days / 360.0) * parity
    if dr - parity > cost:
        return "issue", dr - parity - cost
    if parity - dr > cost:
        return "cancel", parity - dr - cost
    return "none", 0.0


class Pair:
    """`days` receipt sessions of 390 minutes; the home market is open for the first `overlap` minutes of each.
    The company's value in home currency has a market part (daily volatility `sm`, which the proxy follows with a
    basis of daily volatility `basis`) and its own part (`si`); the currency has daily volatility `sfx`. The home mid
    carries microstructure noise of `noise_bp`; the receipt itself has its own noise of `dr_noise_bp`. The nights are
    left out: each session starts where the last ended."""

    def __init__(self, days: int = 40, seed: int = 0, overlap: int = 120, ratio: float = 2.0, home0: float = 10.0,
                 fx0: float = 1.25, sm: float = 0.01, si: float = 0.012, sfx: float = 0.006, basis: float = 0.002,
                 noise_bp: float = 2.0, dr_noise_bp: float = 4.0):
        rng = np.random.default_rng(seed)
        m = days * SESSION
        self.days, self.m, self.overlap, self.ratio = days, m, overlap, ratio
        minute = np.arange(m) % SESSION
        self.open = minute < overlap
        dt = 1.0 / SESSION
        mkt = np.cumsum(rng.standard_normal(m) * sm * math.sqrt(dt))
        own = np.cumsum(rng.standard_normal(m) * si * math.sqrt(dt))
        self.fx = fx0 * np.exp(np.cumsum(rng.standard_normal(m) * sfx * math.sqrt(dt)))
        self.home_true = home0 * np.exp(mkt + own)
        self.proxy = mkt + np.cumsum(rng.standard_normal(m) * basis * math.sqrt(dt))
        self.true = self.home_true * ratio * self.fx
        self.home_mid = self.home_true * (1.0 + noise_bp * 1e-4 * rng.standard_normal(m))
        self.dr_mid = self.true * (1.0 + dr_noise_bp * 1e-4 * rng.standard_normal(m))
        # index of the last open minute at or before each minute (the home close once the home market has shut)
        idx = np.where(self.open, np.arange(m), 0)
        self.t_home = np.maximum.accumulate(idx)

    def quote(self, method: str = "proxy") -> np.ndarray:
        last = self.home_mid[self.t_home] * self.ratio * self.fx
        if method == "home":
            return last
        return last * (1.0 + (self.proxy - self.proxy[self.t_home]))

    def error_bp(self, method: str = "proxy") -> np.ndarray:
        return 1e4 * (self.quote(method) - self.true) / self.true
