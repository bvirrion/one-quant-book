"""firm.vendoreval -- a vendor-trial harness for alternative data (build of One Quant Book 7, chapter 12).

A trial file is rows (entity, period, value) with, when the vendor says so, the date each row was first delivered. The
harness measures coverage through time, the share of history delivered after the fact (backfill), a break in the
panel's relation to a reported truth (panel drift, located by a CUSUM of the residuals), the information coefficient
by year, the incremental IC after residualising on signals already owned, the long-short return of the new
information, and the break-even annual price of the dataset. Text: dictionary tone scores. NumPy only.

API (stable):
    coverage(period)                          {period: number of rows}
    backfill_share(period, delivered, lag)    share of rows first delivered more than `lag` after their period
    fit_by_group(x, y, group)                 {group: (slope, intercept, corr)} of y on x
    cusum_break(resid)                        (index, statistic) of the largest cumulative mean shift
    rank_ic(x, y)                             Spearman correlation, NaN-safe
    ic_by_group(x, y, group)                  {group: rank IC}
    residualise(f, X, group)                  f minus its OLS fit on X within each group
    incremental_ic(f, X, y, group)            (mean rank IC of the residualised f, t statistic, n groups)
    long_short(f, y, group, q)                mean over groups of top-q minus bottom-q mean of y
    breakeven(annual, capital, cost, half_life, years)
                                              the annual fee that makes the contract's expected value zero
    tone(counts, vocab, words)                share of the words of a document found in a word list
"""
from __future__ import annotations

import numpy as np


def coverage(period) -> dict:
    u, c = np.unique(np.asarray(period), return_counts=True)
    return dict(zip(u.tolist(), c.tolist(), strict=True))


def backfill_share(period, delivered, lag) -> float:
    return float(np.mean(np.asarray(delivered) - np.asarray(period) > lag))


def fit_by_group(x, y, group) -> dict:
    x, y, group = np.asarray(x, float), np.asarray(y, float), np.asarray(group)
    out = {}
    for g in np.unique(group):
        m = group == g
        b, a = np.polyfit(x[m], y[m], 1)
        out[g.item() if hasattr(g, "item") else g] = (float(b), float(a), float(np.corrcoef(x[m], y[m])[0, 1]))
    return out


def cusum_break(resid) -> tuple[int, float]:
    """The split that maximises |S_k| / (sigma sqrt(n)), S_k the cumulative sum of demeaned residuals: the most likely
    single shift in the mean. Returns the first index after the break and the statistic (about 1.36 at 5%)."""
    e = np.asarray(resid, float)
    s = np.cumsum(e - e.mean())
    k = int(np.argmax(np.abs(s[:-1])))
    return k + 1, float(np.abs(s[k]) / (e.std(ddof=1) * np.sqrt(len(e))))


def rank_ic(x, y) -> float:
    x, y = np.asarray(x, float), np.asarray(y, float)
    ok = ~np.isnan(x) & ~np.isnan(y)
    rx, ry = np.argsort(np.argsort(x[ok])), np.argsort(np.argsort(y[ok]))
    return float(np.corrcoef(rx, ry)[0, 1])


def ic_by_group(x, y, group) -> dict:
    group = np.asarray(group)
    return {g.item() if hasattr(g, "item") else g: rank_ic(np.asarray(x)[group == g], np.asarray(y)[group == g])
            for g in np.unique(group)}


def residualise(f, X, group) -> np.ndarray:
    f, X, group = np.asarray(f, float), np.asarray(X, float), np.asarray(group)
    X = X.reshape(len(f), -1)
    out = np.empty(len(f))
    for g in np.unique(group):
        m = group == g
        A = np.column_stack([np.ones(m.sum()), X[m]])
        out[m] = f[m] - A @ np.linalg.lstsq(A, f[m], rcond=None)[0]
    return out


def incremental_ic(f, X, y, group) -> tuple[float, float, int]:
    r = residualise(f, X, group)
    ics = np.array(list(ic_by_group(r, y, group).values()))
    return float(ics.mean()), float(ics.mean() / ics.std(ddof=1) * np.sqrt(len(ics))), len(ics)


def long_short(f, y, group, q: float = 0.2) -> float:
    f, y, group = np.asarray(f, float), np.asarray(y, float), np.asarray(group)
    out = []
    for g in np.unique(group):
        m = group == g
        lo, hi = np.quantile(f[m], [q, 1.0 - q])
        out.append(y[m][f[m] >= hi].mean() - y[m][f[m] <= lo].mean())
    return float(np.mean(out))


def breakeven(annual: float, capital: float, cost: float, half_life: float, years: int) -> float:
    """annual: the strategy's gross annual return on capital in the first year; cost: annual trading cost as a
    return; the edge decays with `half_life` years (others buy the data). The fee that equals the mean annual net
    profit over `years` years."""
    t = np.arange(years) + 0.5
    return float(np.mean((annual * 0.5 ** (t / half_life) - cost) * capital))


def tone(counts, vocab, words) -> np.ndarray:
    """counts (documents x vocabulary); the share of each document's words that are in `words`."""
    counts = np.asarray(counts, float)
    cols = np.isin(np.asarray(vocab), list(words))
    return counts[:, cols].sum(axis=1) / counts.sum(axis=1)
