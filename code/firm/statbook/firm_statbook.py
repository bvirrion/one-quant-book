"""firm.statbook -- the accounting of a stat-arb book (build of One Quant Book 8, chapter 1).

A long-short equity book financed at a prime broker: long positions bought partly with borrowed cash (a debit balance
charged at the benchmark rate plus a spread), short positions borrowed from lenders (a fee per name, low for general
collateral, high for names on the hard-to-borrow list) with the short sale proceeds earning the rebate rate (the
benchmark rate minus the fee), margin under Regulation T or a risk-based stress, and the daily P&L attributed to the
risk model's factors, specific returns, trading costs and financing, adding up to the book's P&L. NumPy only.

API (stable):
    borrow_fees(n, seed, htb_share, gc_fee, htb_median)   annual fee per name (GC for most, lognormal for the rest)
    hard_to_borrow(fees, threshold)                       boolean list of names whose fee exceeds the threshold
    reg_t_equity(long_mv, short_mv)                       equity Regulation T requires: 50% of long + 50% of short
    stress_equity(w, capital, move)                       risk-based requirement: the loss of the book if every long
                                                          falls and every short rises by `move` (a crude portfolio
                                                          margin, no netting)
    financing(w, capital, rate, long_spread, fees)        {'debit', 'long_cost', 'short_rebate', 'borrow_cost', 'total'}
                                                          annual rates -> one day's amounts as fractions of capital
    attribution(w, X, f, e, cost, fin)          {'factor', 'by_factor', 'specific', 'cost', 'financing', 'total'}
"""
from __future__ import annotations

import numpy as np

DAYS = 252


def borrow_fees(n: int, seed: int = 0, htb_share: float = 0.05, gc_fee: float = 0.0025,
                htb_median: float = 0.03):
    rng = np.random.default_rng(seed)
    fees = np.full(n, gc_fee)
    htb = rng.random(n) < htb_share
    fees[htb] = np.exp(np.log(htb_median) + 1.0 * rng.standard_normal(htb.sum()))
    return fees


def hard_to_borrow(fees, threshold: float = 0.01):
    return np.asarray(fees, float) > threshold


def reg_t_equity(long_mv: float, short_mv: float) -> float:
    """Regulation T: 50% of a long position's value, and 150% of a short's of which the sale proceeds supply 100%."""
    return 0.5 * long_mv + 0.5 * abs(short_mv)


def stress_equity(w, capital: float, move: float = 0.15) -> float:
    w = np.asarray(w, float)
    return float(move * np.abs(w).sum() * capital)


def financing(w, capital: float, rate: float, long_spread: float, fees):
    """One day's financing as fractions of capital, for weights w (fractions of capital). Cash left after buying the
    longs is L - 1 short of zero when L > 1 (a debit balance, charged rate + long_spread); short positions earn
    rebate = rate - fee on their proceeds, a cost where the fee exceeds the rate."""
    w, fees = np.asarray(w, float), np.asarray(fees, float)
    L = float(w[w > 0].sum())
    S = -w.clip(max=0)
    debit = max(L - 1.0, 0.0)
    long_cost = debit * (rate + long_spread) / DAYS
    rebate = float(S @ (rate - fees)) / DAYS
    borrow = float(S @ fees) / DAYS
    return {"debit": debit, "long_cost": long_cost, "short_rebate": rebate, "borrow_cost": borrow,
            "total": rebate - long_cost}


def attribution(w, X, f, e, cost: float = 0.0, fin: float = 0.0):
    """The day's P&L w'r with r = X f + e: factor part (X'w)'f by factor, specific w'e, minus trading costs, plus
    financing (fractions of capital)."""
    w, X, f, e = (np.asarray(a, float) for a in (w, X, f, e))
    x = X.T @ w
    by = x * f
    spec = float(np.nansum(w * e))
    out = {"factor": float(by.sum()), "by_factor": by, "specific": spec, "cost": -float(cost), "financing": float(fin)}
    out["total"] = out["factor"] + out["specific"] + out["cost"] + out["financing"]
    return out
