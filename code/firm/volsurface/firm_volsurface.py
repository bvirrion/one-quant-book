"""Implied-volatility surface with static-arbitrage checks (build of Book 5, Chapter 7).

The surface stores total implied variance w(k, t) = sigma_imp^2 t on a grid of expiries and
log-moneyness k = ln(K / F(t)). Within an expiry w is interpolated by a not-a-knot cubic spline in
k (linear beyond the grid); between expiries it is linear in t at fixed k, which keeps the surface
free of calendar arbitrage whenever the slices are ordered. It conforms to the pricing library's
VolSurface protocol (implied_vol(strike, expiry), total_variance(k, t)).

Arbitrage checks: calendar, w non-decreasing in t at fixed k; butterfly, the density factor
g(k) = (1 - k w'/(2w))^2 - (w'^2/4)(1/w + 1/4) + w''/2 must be non-negative.
"""
import datetime as dt
import math
from dataclasses import dataclass

import numpy as np


def _natural_spline(x: np.ndarray, y: np.ndarray):
    """Second derivatives of the cubic spline through (x, y) with not-a-knot end conditions (the third
    derivative is continuous at the second and the penultimate knots). A natural spline (zero
    curvature at the ends) bends a convex smile the wrong way in its last interval and manufactures a
    butterfly arbitrage there."""
    n = len(x)
    h = np.diff(x)
    a = np.zeros((n, n))
    rhs = np.zeros(n)
    a[0, 0], a[0, 1], a[0, 2] = h[1], -(h[0] + h[1]), h[0]
    a[-1, -3], a[-1, -2], a[-1, -1] = h[-1], -(h[-2] + h[-1]), h[-2]
    for i in range(1, n - 1):
        a[i, i - 1], a[i, i], a[i, i + 1] = h[i - 1], 2 * (h[i - 1] + h[i]), h[i]
        rhs[i] = 6 * ((y[i + 1] - y[i]) / h[i] - (y[i] - y[i - 1]) / h[i - 1])
    return np.linalg.solve(a, rhs)


def _spline_eval(x, y, m, z: float) -> tuple[float, float, float]:
    """Value, first and second derivative of the spline at z; linear extrapolation beyond the ends."""
    if z < x[0] or z > x[-1]:
        i = 0 if z < x[0] else len(x) - 2
        h = x[i + 1] - x[i]
        s0 = (y[i + 1] - y[i]) / h - h * (2 * m[i] + m[i + 1]) / 6
        s1 = (y[i + 1] - y[i]) / h + h * (m[i] + 2 * m[i + 1]) / 6
        end, slope = (x[0], s0) if z < x[0] else (x[-1], s1)
        yend = y[0] if z < x[0] else y[-1]
        return yend + slope * (z - end), slope, 0.0
    i = min(max(int(np.searchsorted(x, z)) - 1, 0), len(x) - 2)
    h = x[i + 1] - x[i]
    a, b = (x[i + 1] - z) / h, (z - x[i]) / h
    val = a * y[i] + b * y[i + 1] + ((a ** 3 - a) * m[i] + (b ** 3 - b) * m[i + 1]) * h * h / 6
    d1 = (y[i + 1] - y[i]) / h + (-(3 * a * a - 1) * m[i] + (3 * b * b - 1) * m[i + 1]) * h / 6
    d2 = a * m[i] + b * m[i + 1]
    return val, d1, d2


@dataclass(frozen=True)
class Surface:
    asof: dt.date
    expiries: tuple[dt.date, ...]
    ks: tuple[float, ...]                      # log-moneyness grid, common to all expiries
    w: tuple[tuple[float, ...], ...]           # total variance w[i][j] at expiries[i], ks[j]
    forwards: tuple[float, ...]

    def t(self, d: dt.date) -> float:
        return (d - self.asof).days / 365.0

    def _times(self) -> list[float]:
        return [self.t(e) for e in self.expiries]

    def forward(self, t: float) -> float:
        return math.exp(float(np.interp(t, self._times(), [math.log(f) for f in self.forwards])))

    def _slice(self, i: int, k: float) -> tuple[float, float, float]:
        x, y = np.asarray(self.ks), np.asarray(self.w[i])
        return _spline_eval(x, y, _natural_spline(x, y), k)

    def total_variance(self, k: float, t: float) -> float:
        ts = self._times()
        if t <= ts[0]:
            return self._slice(0, k)[0] * t / ts[0]           # flat volatility before the first expiry
        if t >= ts[-1]:
            return self._slice(len(ts) - 1, k)[0] * t / ts[-1]
        i = next(i for i in range(1, len(ts)) if t <= ts[i])
        w0, w1 = self._slice(i - 1, k)[0], self._slice(i, k)[0]
        return w0 + (t - ts[i - 1]) / (ts[i] - ts[i - 1]) * (w1 - w0)

    def implied_vol(self, strike: float, expiry: dt.date) -> float:
        t = self.t(expiry)
        return math.sqrt(max(self.total_variance(math.log(strike / self.forward(t)), t), 0.0) / t)

    def to_dict(self) -> dict:
        return {"type": "Surface", "asof": self.asof.isoformat(), "expiries": [e.isoformat() for e in self.expiries],
                "ks": list(self.ks), "w": [list(r) for r in self.w], "forwards": list(self.forwards)}


def from_vols(asof: dt.date, expiries, forwards, ks, vols) -> Surface:
    """Build a surface from implied volatilities vols[i][j] at expiries[i] and log-moneyness ks[j]."""
    ts = [(e - asof).days / 365.0 for e in expiries]
    w = tuple(tuple(v * v * t for v in row) for row, t in zip(vols, ts, strict=True))
    return Surface(asof, tuple(expiries), tuple(ks), w, tuple(forwards))


def density_factor(w: float, w1: float, w2: float, k: float) -> float:
    """g(k): the risk-neutral density of k equals g(k) / sqrt(2 pi w) exp(-d2^2 / 2)."""
    return (1 - k * w1 / (2 * w)) ** 2 - w1 * w1 / 4 * (1 / w + 0.25) + w2 / 2


def arbitrage_report(s: Surface, k_grid=None) -> dict[str, list]:
    """Calendar violations (i, k) where w falls between expiries i-1 and i, and butterfly violations
    (i, k, g) where the density factor is negative."""
    k_grid = np.linspace(min(s.ks), max(s.ks), 81) if k_grid is None else k_grid
    cal, fly = [], []
    for i in range(len(s.expiries)):
        for k in k_grid:
            w, w1, w2 = s._slice(i, float(k))
            if i > 0 and w < s._slice(i - 1, float(k))[0] - 1e-12:
                cal.append((i, float(k)))
            g = density_factor(w, w1, w2, float(k))
            if g < -1e-10:
                fly.append((i, float(k), g))
    return {"calendar": cal, "butterfly": fly}


def risk_neutral_density(strikes, calls, df: float) -> list[tuple[float, float]]:
    """Breeden-Litzenberger by central second differences on a uniform strike grid: q(K) = C''(K) / P(0,T)."""
    k, c = np.asarray(strikes, float), np.asarray(calls, float)
    h = k[1] - k[0]
    return [(float(k[i]), float((c[i + 1] - 2 * c[i] + c[i - 1]) / (h * h) / df)) for i in range(1, len(k) - 1)]
