"""firm.carrystrat -- carry across asset classes (build of One Quant Book 8, chapter 20).

Carry is the return a futures position earns if prices stay unchanged. From a curve it is the log slope between two
deliveries, annualised; for a currency it is the forward discount; for an equity index the dividend yield minus the
financing rate. Carry books are built class by class, long high carry and short low carry with weights proportional
to the carry's cross-sectional rank, scaled to a volatility; a diversified book gives each class the same risk.
Crash diagnostics measure the books over given windows and the skewness of their monthly returns. NumPy only.

API (stable):
    curve_carry(f_near, f_far, days)            annual carry from two log futures prices `days` apart
    forward_discount(log_spot, log_fwd, days)   annual carry of a currency forward (the interest differential)
    dividend_carry(div_yield, rate)             annual carry of an equity index future
    rank_weights(x, groups)                     per group, centred ranks scaled to a gross of one (NaN ignored)
    book(r, w, cost)                            daily P&L of weights set at t over t + 1, net of costs per unit traded
    scale(pnl, target, start)                   P&L scaled to an annual volatility measured from `start` (in sample)
    windows(pnl, spans)                         cumulative P&L over each (start, end) window
    skew_monthly(pnl, start, days)              skewness of non-overlapping `days`-day sums
"""
from __future__ import annotations

import math

import numpy as np


def curve_carry(f_near, f_far, days: float):
    return (np.asarray(f_near, float) - np.asarray(f_far, float)) * 252.0 / days


def forward_discount(log_spot, log_fwd, days: float):
    return (np.asarray(log_spot, float) - np.asarray(log_fwd, float)) * 252.0 / days


def dividend_carry(div_yield, rate):
    return np.asarray(div_yield, float) - np.asarray(rate, float)


def rank_weights(x, groups):
    x, groups = np.asarray(x, float), np.asarray(groups)
    w = np.zeros(x.shape)
    for g in np.unique(groups):
        m = groups == g
        xs = x[..., m]
        rk = np.argsort(np.argsort(xs, axis=-1), axis=-1).astype(float)
        c = rk - rk.mean(axis=-1, keepdims=True)
        w[..., m] = c / np.abs(c).sum(axis=-1, keepdims=True)
    return w


def book(r, w, cost):
    r, w = np.asarray(r, float), np.asarray(w, float)
    pnl = np.zeros(len(r))
    pnl[1:] = (w[:-1] * r[1:]).sum(1)
    pnl -= (np.abs(np.diff(w, axis=0, prepend=np.zeros((1, w.shape[1])))) * np.asarray(cost)).sum(1)
    return pnl


def scale(pnl, target: float = 0.10, start: int = 0):
    pnl = np.asarray(pnl, float)
    return pnl * target / (pnl[start:].std() * math.sqrt(252))


def windows(pnl, spans):
    return [float(np.sum(pnl[s:e])) for s, e in spans]


def skew_monthly(pnl, start: int = 0, days: int = 21):
    x = np.asarray(pnl, float)[start:]
    m = x[: len(x) // days * days].reshape(-1, days).sum(1)
    d = m - m.mean()
    return float((d**3).mean() / (d**2).mean() ** 1.5)
