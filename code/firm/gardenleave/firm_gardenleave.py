"""firm.gardenleave -- what keeping a departing person out of the market is worth (analytical tool of One Quant
Book 16, chapter 11; the chapter's subject is legal and has no build in the running-project sense).

A strategy earns P a year today and its edge decays at rate lam (half-life ln 2 / lam) whatever happens. If a
departing employee takes what they know to a competitor that starts trading it at time T, the firm loses a share L
of the strategy's remaining profits from T on. Paying the employee to stay out of the market for T years (garden
leave, or a paid non-compete) costs S a year. With discount rate r:

    loss if the competitor starts at T  = L * P * exp(-(lam + r) T) / (lam + r)
    value protected by a leave of T     = L * P * (1 - exp(-(lam + r) T)) / (lam + r)
    cost of the leave                   = S * (1 - exp(-r T)) / r
    best length                         T* = ln(L P / S) / lam          (marginal protection = marginal cost)

The decay rate is estimated from the strategy's own history with One Quant Book 7's firm.decay.half_life_fit.

API (stable):
    loss_if_start(P, L, lam, r, T) ; protected(P, L, lam, r, T) ; leave_cost(S, r, T) ; net(P, L, lam, r, S, T)
    best_length(P, L, lam, S) ; half_life_from_series(months, edge) -> (half-life in months, level)
"""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "decay"))
import firm_decay as fd  # noqa: E402


def loss_if_start(P, L, lam, r, T):
    return L * P * math.exp(-(lam + r) * T) / (lam + r)


def protected(P, L, lam, r, T):
    return L * P * (1 - math.exp(-(lam + r) * T)) / (lam + r)


def leave_cost(S, r, T):
    return S * T if r == 0 else S * (1 - math.exp(-r * T)) / r


def net(P, L, lam, r, S, T):
    return protected(P, L, lam, r, T) - leave_cost(S, r, T)


def best_length(P, L, lam, S):
    """Where the discounted marginal protection L P e^{-(lam+r)T} equals the discounted marginal cost S e^{-rT}."""
    if L * P <= S:
        return 0.0
    return math.log(L * P / S) / lam


def half_life_from_series(months, edge):
    """Half-life (in the units of `months`) of a decaying edge series by firm.decay's grid least squares."""
    level, hl = fd.half_life_fit(np.asarray(months, float), np.asarray(edge, float))
    return float(hl), float(level)
