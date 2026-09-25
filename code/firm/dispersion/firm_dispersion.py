"""firm.dispersion -- dispersion and correlation trading (build of One Quant Book 9, chapter 2).

Implied and realised average correlation of an index's members from the index's variance and the members'
(Markowitz's decomposition, as in Cboe's implied correlation indices), and dispersion books of variance swaps:
short the index's variance and long the members', with the members' variance notionals either equal to their index
weights (a trade on correlation and on the level of variance) or scaled so that the book's vega is zero. P&L per
period decomposes into a correlation part and a volatility part. NumPy only.

API (stable):
    average_corr(var_index, var_members, w)          (var_I - sum w_i^2 var_i) / (sum_{i != j} w_i w_j vol_i vol_j)
    realised_var(R, start, n)                         annualised realised variance of each column over n days
    dispersion_pnl(iv_index, iv_members, rv_index, rv_members, w, vega_neutral)
                                                     per-period P&L of short index variance, long member variance
    corr_swap_pnl(implied, realised)                 short correlation swap: implied minus realised correlation
"""
from __future__ import annotations

import numpy as np


def average_corr(var_index, var_members, w):
    var_members, w = np.asarray(var_members, float), np.asarray(w, float)
    vol = np.sqrt(var_members)
    own = (w**2 * var_members).sum(-1)
    cross = (w * vol).sum(-1) ** 2 - own
    return (np.asarray(var_index, float) - own) / cross


def realised_var(R, start: int, n: int, year: int = 252):
    x = np.asarray(R, float)[start + 1:start + 1 + n]
    return (x**2).sum(0) * year / n


def dispersion_pnl(iv_index, iv_members, rv_index, rv_members, w, vega_neutral: bool = False):
    """Variance-swap legs in annual variance units (multiply by the period's length for P&L). A variance swap on
    notional n has vega 2 n iv; with vega_neutral the members' notionals n_i = c w_i are scaled so that
    sum_i n_i iv_i = iv_index, otherwise n_i = w_i."""
    w, iv_m = np.asarray(w, float), np.asarray(iv_members, float)
    iv_i = np.asarray(iv_index, float)
    n = w * (iv_i / (w * iv_m).sum(-1))[..., None] if vega_neutral else w
    index_leg = iv_i**2 - np.asarray(rv_index, float)
    member_leg = (n * (np.asarray(rv_members, float) - iv_m**2)).sum(-1)
    return index_leg + member_leg


def corr_swap_pnl(implied, realised):
    return np.asarray(implied, float) - np.asarray(realised, float)
