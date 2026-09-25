"""firm.xasset -- intermarket signals (build of One Quant Book 8, chapter 22).

Daily: plant slow diffusion (a follower's return includes beta times the average of a leader's returns over the
previous `lag` days), scan every leader-follower pair and lag for lagged correlation with a Bonferroni threshold,
map the detected links into signals (the leader's past return over the diffusion window), and check their stability
across two halves. Intraday: simulate two assets whose efficient prices share one Brownian motion, the second
following the first by `lead` seconds, observed at Poisson tick times with noise; the lead is then estimated with
firm.leadlag's Hayashi-Yoshida cross-correlation, and a trader who acts `latency` seconds after the leader's move
buys or sells the follower and pays half the spread each way. NumPy only.

API (stable):
    diffuse(follow, lead, links, beta, lag)       follower returns plus planted diffusion; links [(leader, follower)]
    lead_scan(lead, follow, lags)                 t-statistics of corr(follow_t, lead_{t-lag}): (lags, n_lead, n_follow)
    detect(tstats, n_tests, alpha)                (lag, leader, follower) above the Bonferroni threshold
    signal(lead, links, window, n_follow)         (T, n_follow): the linked leader's return over the last `window` days
    simulate_pair(seconds, lead, vol, noise, rate, rng)   tick times and log prices (t1, x1, t2, x2)
    lead_trades(g1, g2, window, latency, hold, threshold, half_spread)   per-trade net returns on a 1-second grid
"""
from __future__ import annotations

import math

import numpy as np


def diffuse(follow, lead, links, beta: float, lag: int):
    out = np.array(follow, float, copy=True)
    lead = np.asarray(lead, float)
    for i, j in links:
        c = np.concatenate([[0.0], np.cumsum(lead[:, i])])
        past = np.zeros(len(lead))
        t = np.arange(len(lead))
        lo = np.maximum(t - lag, 0)
        past[1:] = (c[t[1:]] - c[lo[1:]]) / lag                     # mean of lead returns t-lag .. t-1
        out[:, j] += beta * past
    return out


def lead_scan(lead, follow, lags):
    lead, follow = np.asarray(lead, float), np.asarray(follow, float)
    z = lambda x: (x - x.mean(0)) / x.std(0)  # noqa: E731
    out = np.zeros((len(lags), lead.shape[1], follow.shape[1]))
    for k, L in enumerate(lags):
        a, b = z(lead[:-L]), z(follow[L:])
        c = a.T @ b / len(a)
        out[k] = c * math.sqrt(len(a))
    return out


def detect(tstats, n_tests: int, alpha: float = 0.05):
    from statistics import NormalDist
    thr = NormalDist().inv_cdf(1 - alpha / (2 * n_tests))
    idx = np.argwhere(np.abs(tstats) > thr)
    return [tuple(int(v) for v in row) for row in idx], thr


def signal(lead, links, window: int, n_follow: int):
    lead = np.asarray(lead, float)
    c = np.cumsum(lead, axis=0)
    s = np.zeros((len(lead), n_follow))
    for i, j in links:
        s[window:, j] = c[window:, i] - c[:-window, i]
    return s


def simulate_pair(seconds: int, lead: float, vol: float, noise: float, rate: float, rng=None):
    rng = rng or np.random.default_rng(22)
    lag = int(round(lead))
    w = np.concatenate([[0.0], np.cumsum(vol * rng.standard_normal(seconds + lag))])
    p1, p2 = w[lag:lag + seconds + 1], w[:seconds + 1]              # asset 2 sees the path `lag` seconds late
    out = []
    for p in (p1, p2):
        n = rng.poisson(rate * seconds)
        t = np.sort(rng.uniform(0, seconds, n))
        x = p[np.floor(t).astype(int)] + noise * rng.standard_normal(n)
        out += [t, x]
    return tuple(out)


def lead_trades(g1, g2, window: int, latency: int, hold: int, threshold: float, half_spread: float):
    """g1, g2: log prices on a 1-second grid. At each second t, if the leader moved more than `threshold` over the last
    `window` seconds, buy (or sell) the follower at t + latency and exit `hold` seconds later; one trade at a time."""
    g1, g2 = np.asarray(g1, float), np.asarray(g2, float)
    out, t = [], window
    while t + latency + hold < len(g1):
        m = g1[t] - g1[t - window]
        if abs(m) > threshold:
            a = t + latency
            out.append(np.sign(m) * (g2[a + hold] - g2[a]) - 2 * half_spread)
            t = a + hold
        else:
            t += 1
    return np.array(out)
