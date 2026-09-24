"""firm.numeraire -- moving expectations between numeraires (One Quant Book 4, chapter 5).

If samples are drawn under the measure Q^N attached to a numeraire N, an expectation under the
measure of another numeraire M is a reweighted average with weights dQ^M/dQ^N = (M_T/M_0)/(N_T/N_0).
And a pricing library is only consistent if every traded price divided by the numeraire is a
martingale under the numeraire's measure: `deflated_martingale_test` checks that on simulated paths.

API (stable):
    change_of_numeraire_weights(m_T, m_0, n_T, n_0) -> weights, mean one under Q^N
    reweighted_mean(x, w)                            -> (estimate, standard error)
    girsanov_weights(dw, gamma, dt)                  -> exp(sum gamma dW - 1/2 sum gamma^2 dt) per path
    deflated_martingale_test(prices, numeraire)      -> dict: max |t| of E[V_t/N_t] - V_0/N_0 over dates
"""
from __future__ import annotations

import math

import numpy as np


def change_of_numeraire_weights(m_T, m_0, n_T, n_0) -> np.ndarray:
    """dQ^M/dQ^N on each path: (M_T / M_0) / (N_T / N_0)."""
    return (np.asarray(m_T, float) / m_0) / (np.asarray(n_T, float) / n_0)


def reweighted_mean(x, w) -> tuple[float, float]:
    """E^M[X] = E^N[W X] estimated from samples under Q^N, with its standard error."""
    y = np.asarray(x, float) * np.asarray(w, float)
    return float(y.mean()), float(y.std(ddof=1) / math.sqrt(y.size))


def girsanov_weights(dw: np.ndarray, gamma, dt: float) -> np.ndarray:
    """Density exp(sum_k gamma_k dW_k - 1/2 sum_k gamma_k^2 dt) of the measure under which
    W - int gamma dt is a Brownian motion; `dw` has one row per path, `gamma` is a scalar, a
    per-step vector, or an array shaped like dw (it must be adapted: gamma_k known before dW_k)."""
    g = np.broadcast_to(np.asarray(gamma, float), dw.shape)
    return np.exp((g * dw).sum(axis=1) - 0.5 * (g**2).sum(axis=1) * dt)


def deflated_martingale_test(prices: np.ndarray, numeraire: np.ndarray) -> dict:
    """prices and numeraire: arrays (paths, dates) simulated under the numeraire's measure, with the
    same value on every path at date 0. Returns the largest |t|-statistic of mean(V_t/N_t) against
    V_0/N_0 over the dates, and the dates' means."""
    ratio = np.asarray(prices, float) / np.asarray(numeraire, float)
    target = ratio[0, 0]
    means = ratio.mean(axis=0)
    se = ratio.std(axis=0, ddof=1) / math.sqrt(ratio.shape[0])
    tiny = 1e-12 * max(1.0, abs(target))           # a date where every path agrees (t = 0) has se ~ 0
    gap = means - target
    t = np.where(se > tiny, gap / np.maximum(se, tiny), np.where(np.abs(gap) < tiny, 0.0, np.inf))
    return {"max_abs_t": float(np.max(np.abs(t))), "means": means, "target": float(target)}
