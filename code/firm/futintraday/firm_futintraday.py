"""firm.futintraday -- intraday futures sessions and strategies (build of One Quant Book 8, chapter 25).

A bar-level model of an index future's regular session: one-minute log returns with a U-shaped volatility profile,
an overnight gap, a daily trend drift (a "trend day" component whose sign the session reveals gradually), a small
mean-reverting component in one-minute returns (bid-ask bounce and liquidity provision), and scheduled announcements
eight times a year, before which a drift is planted over the previous afternoon and the announcement day's morning; a
crowding date after which that drift shrinks. Strategy toolkit: the opening-range breakout, an intraday fade of large
short moves, and the pre-announcement hold, each returning daily P&L net of a cost per unit traded. NumPy only.
(Book 7's message-level firm.tape and event-driven firm.evbt are the level-2 tools; this module works on bars so
that ten years of sessions run in seconds, and takes its cost per trade from them as a parameter.)

API (stable):
    SessionConfig(...)                    parameters: days, minutes, volatility, profile, trend, reversal, announcements
    simulate_sessions(cfg, rng)           dict: r (days, minutes) one-minute returns, gap (days,), ann (days,) bool,
                                          ann_minute, drift (days,) planted trend (truth)
    orb(S, window, cost)                  daily P&L of the opening-range breakout held to the close
    fade(S, lookback, z, hold, cost)      daily P&L of fading moves beyond z standard deviations over `lookback` minutes
    pre_announcement(S, cost)             P&L of holding from the previous day's midday to the announcement minute
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SessionConfig:
    days: int = 2520
    minutes: int = 390
    vol: float = 0.16                 # annual volatility of the day (session plus gap) before the bounce
    gap_share: float = 0.25           # share of daily variance in the overnight gap
    u_shape: float = 2.0              # volatility at the open and close relative to midday
    trend_sd: float = 0.004           # standard deviation of a day's planted drift over the session
    reversal: float = -0.1            # autocorrelation of one-minute returns from bounce
    every: int = 32                   # trading days between announcements (about eight a year)
    ann_minute: int = 270             # minute of the announcement in the session
    pre_drift: float = 0.005          # total planted drift before each announcement
    crowd_day: int = 1260             # from this day the drift is multiplied by crowd_after
    crowd_after: float = 0.3


def _profile(cfg: SessionConfig):
    x = np.linspace(-1, 1, cfg.minutes)
    p = 1 + (cfg.u_shape - 1) * x**2
    return p / np.sqrt(np.mean(p**2))


def simulate_sessions(cfg: SessionConfig | None = None, rng=None):
    cfg = cfg or SessionConfig()
    rng = rng or np.random.default_rng(25)
    D, M = cfg.days, cfg.minutes
    day_sd = cfg.vol / math.sqrt(252)
    m_sd = day_sd * math.sqrt(1 - cfg.gap_share) / math.sqrt(M) * _profile(cfg)
    e = rng.standard_normal((D, M)) * m_sd
    r = e.copy()
    r[:, 1:] += cfg.reversal * e[:, :-1]                      # MA(1) bounce: negative autocorrelation
    drift = cfg.trend_sd * rng.standard_normal(D)
    r += drift[:, None] / M
    gap = day_sd * math.sqrt(cfg.gap_share) * rng.standard_normal(D)
    ann = np.zeros(D, bool)
    ann[cfg.every // 2::cfg.every] = True
    size = np.where(np.arange(D) >= cfg.crowd_day, cfg.crowd_after, 1.0) * cfg.pre_drift
    for d in np.flatnonzero(ann):
        if d == 0:
            continue
        k = size[d] / 3                                       # a third on the previous afternoon, two thirds before
        r[d - 1, M // 2:] += k / (M - M // 2)
        r[d, :cfg.ann_minute] += 2 * k / cfg.ann_minute
    return {"r": r, "gap": gap, "ann": ann, "ann_minute": cfg.ann_minute, "drift": drift}


def orb(S, window: int = 30, cost: float = 0.0):
    r = S["r"]
    p = np.cumsum(r, axis=1)
    hi, lo = p[:, :window].max(1), p[:, :window].min(1)
    out = np.zeros(len(r))
    for d in range(len(r)):
        after = p[d, window:]
        up = np.flatnonzero(after > hi[d])
        dn = np.flatnonzero(after < lo[d])
        first = min(up[0] if len(up) else 10**9, dn[0] if len(dn) else 10**9)
        if first == 10**9:
            continue
        side = 1.0 if len(up) and up[0] == first else -1.0
        entry = window + first
        out[d] = side * (p[d, -1] - p[d, entry]) - 2 * cost
    return out


def fade(S, lookback: int = 5, z: float = 2.0, hold: int = 5, cost: float = 0.0):
    r = S["r"]
    sd = r.std(axis=0)
    out = np.zeros(len(r))
    c = np.concatenate([np.zeros((len(r), 1)), np.cumsum(r, axis=1)], axis=1)
    band = z * sd.mean() * math.sqrt(lookback)
    for d in range(len(r)):
        t = lookback
        while t + hold < r.shape[1]:
            m = c[d, t] - c[d, t - lookback]
            if abs(m) > band:
                out[d] += -np.sign(m) * (c[d, t + hold] - c[d, t]) - 2 * cost
                t += hold
            else:
                t += 1
    return out


def pre_announcement(S, cost: float = 0.0):
    r, ann, a = S["r"], S["ann"], S["ann_minute"]
    out = np.zeros(len(r))
    half = r.shape[1] // 2
    for d in np.flatnonzero(ann):
        if d > 0:
            out[d] = r[d - 1, half:].sum() + S["gap"][d] + r[d, :a].sum() - 2 * cost
    return out
