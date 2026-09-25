"""Cross-sectional and cross-asset features (One Quant Book 7, chapter 10).

Three studies. (1) Real data: the lead of large US stocks over small ones in the size quintiles of the Kenneth French
library, read from the derived statistics in data/research/ff_size_leadlag.csv (written by rs_fetch_size.py).
(2) firm.synthmkt with planted customer-supplier links: the supplier's delayed response to its customer's news, the
customer-momentum feature, and what mining all lagged cross-correlations finds without the link data. (3) Two
firm.tape instruments on one efficient price, the second delayed by a planted latency: the Hayashi-Yoshida
lead-lag estimate against the latency, and the directional predictability left at each sampling interval.
NumPy (and pandas for the CSV) only.
"""
from __future__ import annotations

import functools
import pathlib
import sys

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[3] / "firm"
for c in ("tape", "synthmkt", "leadlag", "predictor"):
    sys.path.insert(0, str(ROOT / c))
from firm_leadlag import (  # noqa: E402
    directional_corr,
    hy_ccf,
    lagged_corr_matrix,
    lead_estimate,
    lead_lag_ratio,
    lead_symmetric,
    linked_feature,
    peer_relative,
)
from firm_synthmkt import MarketConfig, simulate  # noqa: E402
from firm_tape import TapeConfig, simulate_pair  # noqa: E402

DATA = pathlib.Path(__file__).resolve().parents[4] / "data" / "research" / "ff_size_leadlag.csv"
LINKS = MarketConfig(link_share=0.3)
MONTH = 21
LAGS = np.round(np.arange(-3.0, 3.001, 0.05), 2)


# ------------------------------------------------------------------------------------------------ size quintiles
def size_table() -> pd.DataFrame:
    return pd.read_csv(DATA)


# ------------------------------------------------------------------------------------------------ economic links
@functools.lru_cache(maxsize=4)
def panel(cfg: MarketConfig = LINKS):
    return simulate(cfg)


def _rank_ic(x, y) -> float:
    rx, ry = np.argsort(np.argsort(x)), np.argsort(np.argsort(y))
    return float(np.corrcoef(rx, ry)[0, 1])


def customer_momentum(cfg: MarketConfig = LINKS):
    """Each month-end e from year 1: suppliers whose customer is listed; the customer's return over the last month
    (raw, and relative to its industry peers), and the truth (the planted link part of the supplier's expected return
    summed over the next month); against the supplier's return over the next month. Rank ICs and the long-short
    quintile spread of the raw feature (monthly, and its annualised Sharpe ratio)."""
    P = panel(cfg)
    R, c = P.ret, P.customer
    rel = peer_relative(R, P.industry)
    out = {"raw": [], "peer": [], "truth": [], "spread": []}
    for e in range(12 * MONTH, R.shape[0] - MONTH, MONTH):
        s = np.flatnonzero((c >= 0) & P.listed[e] & P.listed[e + MONTH])
        s = s[P.listed[e, c[s]] & P.listed[e - MONTH + 1, c[s]]]
        past = linked_feature(np.nansum(R[e - MONTH + 1:e + 1], axis=0), c)[s]
        past_rel = linked_feature(np.nansum(rel[e - MONTH + 1:e + 1], axis=0), c)[s]
        truth = np.nansum(P.alpha["link"][e:e + MONTH, s], axis=0)
        fut = np.nansum(R[e + 1:e + MONTH + 1, s], axis=0)
        out["raw"].append(_rank_ic(past, fut))
        out["peer"].append(_rank_ic(past_rel, fut))
        out["truth"].append(_rank_ic(truth, fut))
        lo, hi = np.quantile(past, [0.2, 0.8])
        out["spread"].append(fut[past >= hi].mean() - fut[past <= lo].mean())
    sp = np.array(out["spread"])
    return {"n_suppliers": int((c >= 0).sum()), "n_listings": len(c), "months": len(sp),
            **{k: float(np.mean(v)) for k, v in out.items() if k != "spread"},
            "ic_t": float(np.mean(out["raw"]) / np.std(out["raw"]) * np.sqrt(len(sp))),
            "spread": float(sp.mean()), "sharpe": float(sp.mean() / sp.std() * np.sqrt(12))}


def event_study(before: int = 5, after: int = 40):
    """Around each customer earnings day: the market-adjusted return (beta times the market removed) of the customer
    and of each of its suppliers on each day of the window, regressed across events on the true surprise; the
    cumulative slopes (return per unit of surprise) and the number of events."""
    P = panel()
    R, c, T = P.ret, P.customer, P.ret.shape[0]
    adj = R - P.beta[None, :] * P.mkt[:, None]
    sup_of = {}
    for s in np.flatnonzero(c >= 0):
        sup_of.setdefault(int(c[s]), []).append(int(s))
    win = np.arange(-before, after + 1)
    rows = {"customer": ([], []), "supplier": ([], [])}
    for t, p, sur in P.earnings:
        if t - before < 0 or t + after >= T or p not in sup_of:
            continue
        for who, names in (("customer", [p]), ("supplier", sup_of[p])):
            for q in names:
                x = adj[t + win, q]
                if not np.isnan(x).any():
                    rows[who][0].append(x)
                    rows[who][1].append(sur)
    out = {}
    for who, (X, s) in rows.items():
        X, s = np.array(X), np.array(s)
        slope = ((s - s.mean()) @ (X - X.mean(axis=0))) / np.sum((s - s.mean()) ** 2)
        out[who] = np.cumsum(slope)
        out["n_" + who] = len(s)
    return win, out


def mining():
    """Names listed on every day: rank all ordered pairs by the lagged correlation of daily returns (one day) and of
    non-overlapping monthly returns (one month); how many planted links are among the top k."""
    P = panel()
    full = np.flatnonzero(P.listed.all(axis=0))
    pos = {int(p): k for k, p in enumerate(full)}
    true = np.zeros((len(full), len(full)), bool)
    for k, p in enumerate(full):
        if P.customer[p] >= 0 and int(P.customer[p]) in pos:
            true[k, pos[int(P.customer[p])]] = True
    X = P.ret[:, full]
    monthly = np.add.reduceat(X, np.arange(0, X.shape[0] - MONTH + 1, MONTH), axis=0)[: X.shape[0] // MONTH]
    out = {"names": len(full), "pairs": len(full) * (len(full) - 1), "links": int(true.sum())}
    for name, M in (("daily", X), ("monthly", monthly)):
        C = lagged_corr_matrix(M, 1)
        v = np.where(np.isnan(C), -np.inf, C).ravel()
        order = np.argsort(-v)
        out[name] = {k: int(true.ravel()[order[:k]].sum()) for k in (100, 1000, 10_000)}
        out[name + "_true_mean"] = float(np.nanmean(C[true]))
        out[name + "_sd"] = float(np.nanstd(C))
    return out


# ------------------------------------------------------------------------------------------------ the tape pair
@functools.cache
def pair(latency: float, v_rate: float = 1.0, seed: int = 10):
    cfg = TapeConfig(seconds=3600.0, news_at=None, v_rate=v_rate, seed=seed)
    a, b = simulate_pair(cfg, latency=latency, seed_b=seed + 1)
    return _mids(a), _mids(b)


def _mids(tp):
    m = 0.5 * (tp.top["bid"] + tp.top["ask"])
    keep = np.r_[True, np.diff(m) != 0]
    return tp.top["t"][keep], m[keep]


def ccf(latency: float, v_rate: float = 1.0, seed: int = 10):
    (ta, ma), (tb, mb) = pair(latency, v_rate, seed)
    c = hy_ccf(ta, ma, tb, mb, LAGS, norm_step=60.0)
    return {"ccf": c, "argmax": lead_estimate(LAGS, c), "centre": lead_symmetric(LAGS, c, 20),
            "llr": lead_lag_ratio(LAGS, c), "changes_per_s": (len(ta) + len(tb)) / 7200.0}


def lead_recovery(latencies=(0.0, 0.25, 0.5, 1.0, 2.0), seeds=(10, 20, 30)):
    """Lead estimates (seconds; argmax and symmetric centre) for each planted latency and seed, on the fast pair
    (efficient-price jumps once a second) and on the default slow one (0.12 a second)."""
    return {v: {L: [(ccf(L, v, s)["argmax"], ccf(L, v, s)["centre"]) for s in seeds] for L in latencies}
            for v in (1.0, 0.12)}


def interval_table(latency: float = 0.5, steps=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0)):
    """At each sampling interval: corr(B's return, A's previous return), the reverse, and B's own first-order
    autocorrelation."""
    (ta, ma), (tb, mb) = pair(latency)
    out = {}
    for d in steps:
        ab, ba = directional_corr(ta, ma, tb, mb, d)
        g = np.arange(0.0, 3600.0 + 1e-9, d)
        rb = np.diff(mb[np.searchsorted(tb, g, side="right") - 1])
        out[d] = {"a_to_b": ab, "b_to_a": ba, "own_b": float(np.corrcoef(rb[1:], rb[:-1])[0, 1])}
    return out
