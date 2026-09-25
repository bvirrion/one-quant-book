"""Pairs and baskets (One Quant Book 8, chapter 4).

Gatev, Goetzmann and Rouwenhorst's rule on firm.synthmkt: in each cycle, pairs are formed over twelve months (252
days) and traded over the next six (126), from year 3 to year 10, sixteen cycles. Selection by distance (the 20 pairs
of distinct stocks with the smallest sum of squared differences of normalised prices), by Engle-Granger tests on all
same-industry pairs (p-values from a simulated null, Benjamini-Hochberg control; the 20 pairs with the smallest
p-values traded on their cointegration residual), by a Gaussian-copula mispricing index on the distance pairs, and a
synthetic twin for each of the 20 most liquid stocks (ridge regression on the 30 same-industry stocks most correlated
with it). Rules: open at two formation standard deviations, close at the next crossing or at the end of the cycle; $1
per leg; 5 basis points per unit traded. Run on the market with 10% of the initial listings paired as close
substitutes (MarketConfig.twin_share: 50 true pairs whose log price spread is a stationary AR(1)) and on the default
market, where no pair is cointegrated. NumPy only.
"""
from __future__ import annotations

import functools
import math
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np  # noqa: E402

HERE = pathlib.Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[3] / "firm" / "pairsel"))
sys.path.insert(0, str(HERE.parents[3] / "firm" / "synthmkt"))
from firm_pairsel import (  # noqa: E402
    bh,
    copula_fit,
    copula_h,
    eg_null,
    eg_tau,
    pvalue,
    top_pairs,
    trade_pair,
    twin,
)
from firm_synthmkt import MarketConfig, simulate  # noqa: E402

YEAR, START, FORM, HOLD, NPAIRS, COST, K = 252, 504, 252, 126, 20, 0.0005, 2.0
LAMBDA, PEERS, TWINS = 1e-3, 30, 0.1


@functools.lru_cache(maxsize=2)
def panel(share: float = TWINS):
    """The market with a share of the initial listings paired as close substitutes (twins), or none."""
    P = simulate(MarketConfig(twin_share=share))
    return P, np.where(P.listed, P.ret, np.nan)


def cycles(T: int):
    return list(range(START, T - HOLD + 1, HOLD))


@functools.lru_cache(maxsize=1)
def null252():
    return eg_null(FORM, 20000, 4)


def _index(R, lo, hi, ids):
    """Cumulative return index of the names over [lo, hi), 1 before the first day; flat after a delisting."""
    return np.vstack([np.ones(len(ids)), np.cumprod(1 + np.nan_to_num(R[lo:hi][:, ids]), axis=0)])


def sharpe(x) -> float:
    x = np.asarray(x, float)
    return float(x.mean() / x.std(ddof=1) * math.sqrt(YEAR))


@functools.lru_cache(maxsize=8)
def run(share: float = TWINS, method: str = "distance"):
    """Daily returns of the book (mean over its pairs of the P&L on $1 per leg), gross and net, and counts."""
    P, R = panel(share)
    T = R.shape[0]
    gross, net = [], []
    opened = never = merged = 0
    merged_loss = []
    for t0 in cycles(T):
        pairs = select(share, t0, method)
        G = np.zeros((HOLD, len(pairs)))
        C = np.zeros((HOLD, len(pairs)))
        for j, pair in enumerate(pairs):
            ra, rb, spread, sd, kk = legs(share, t0, method, pair)
            g, _, o, side = trade_pair(ra, rb, spread, sd, kk, 0.0)
            c, _, _, _ = trade_pair(ra, rb, spread, sd, kk, COST)
            G[:, j], C[:, j] = g, g - c
            opened += o
            never += side != 0
            if method != "twin":
                gone = [p for p in pair if P.end[p] >= t0 and P.end[p] < t0 + HOLD and P.delist.get(int(p), (0, ""))[1]
                        == "merger"]
                if gone:
                    merged += 1
                    merged_loss.append(float(g.sum()))
        gross.append(G.mean(axis=1))
        net.append(G.mean(axis=1) - C.mean(axis=1))
    g, n = np.concatenate(gross), np.concatenate(net)
    npairs = NPAIRS * len(cycles(T))
    return {"sr_gross": sharpe(g), "sr_net": sharpe(n), "ret_gross": float(g.mean() * YEAR),
            "ret_net": float(n.mean() * YEAR), "opened": opened / npairs, "never": never / npairs,
            "merged": merged, "merged_loss": float(np.mean(merged_loss)) if merged_loss else 0.0, "net": n}


def select(share: float, t0: int, method: str):
    P, R = panel(share)
    if method in ("distance", "copula"):
        ids = np.flatnonzero(P.listed[t0 - FORM:t0].all(axis=0))
        N = _index(R, t0 - FORM, t0, ids)
        return [(int(ids[a]), int(ids[b])) for a, b, _ in top_pairs(N, NPAIRS)]
    if method == "eg":
        return [(a, b) for a, b, _ in eg_select(share, t0)[:NPAIRS]]
    if method == "two-step":
        return two_step(share, t0)
    return twins(share, t0)


def true_selected(method: str, share: float = TWINS) -> int:
    """How many of the selected pairs, over all cycles, are planted substitutes."""
    P, R = panel(share)
    return sum(int(P.twin[a] == b) for t0 in cycles(R.shape[0]) for a, b in select(share, t0, method))


def legs(share, t0, method, pair):
    """Trading-period returns of the two legs, the spread known at each close, its formation sd and the threshold."""
    P, R = panel(share)
    lo, hi = t0 - FORM, t0 + HOLD
    if method == "twin":
        y, peers, w = pair
        ra = np.nan_to_num(R[t0:hi, y])
        rb = np.nan_to_num(R[t0:hi][:, peers]) @ w
        form = np.nan_to_num(R[lo:t0, y]) - np.nan_to_num(R[lo:t0][:, peers]) @ w
        return ra, rb, np.cumsum(ra - rb), float(np.cumsum(form).std()), K
    a, b = pair
    ra, rb = np.nan_to_num(R[t0:hi, a]), np.nan_to_num(R[t0:hi, b])
    Nf = _index(R, lo, t0, np.array([a, b]))
    if method == "distance":
        Nt = _index(R, t0, hi, np.array([a, b]))[1:]
        return ra, rb, Nt[:, 0] - Nt[:, 1], float((Nf[:, 0] - Nf[:, 1]).std()), K
    if method in ("eg", "two-step"):
        la, lb = np.log(Nf[1:, 0]), np.log(Nf[1:, 1])
        beta = np.cov(la, lb)[0, 1] / lb.var(ddof=1)
        alpha = la.mean() - beta * lb.mean()
        u = la - alpha - beta * lb
        Nt = _index(R, lo, hi, np.array([a, b]))[FORM + 1:]
        spread = np.log(Nt[:, 0]) - alpha - beta * np.log(Nt[:, 1])
        return ra, rb, spread, float(u.std()), K
    fa, fb = np.nan_to_num(R[lo:t0, a]), np.nan_to_num(R[lo:t0, b])
    fit = copula_fit(fa, fb)
    m = np.cumsum(copula_h(fit, ra, rb) - 0.5)                 # mispricing index: a rich relative to b when positive
    return ra, rb, m, 1.0, 0.5


@functools.lru_cache(maxsize=64)
def eg_select(share: float, t0: int):
    """All same-industry pairs listed over the formation year: (a, b, p) sorted by p, greedy unique legs."""
    P, R = panel(share)
    ids = np.flatnonzero(P.listed[t0 - FORM:t0].all(axis=0))
    L = np.log(_index(R, t0 - FORM, t0, ids)[1:])
    out = []
    for k in range(P.cfg.n_industries):
        loc = np.flatnonzero(P.industry[ids] == k)
        i, j = np.triu_indices(len(loc), 1)
        p = pvalue(eg_tau(L[:, loc[i]], L[:, loc[j]]), null252())
        out += list(zip(ids[loc[i]].tolist(), ids[loc[j]].tolist(), p.tolist(), strict=True))
    out.sort(key=lambda x: x[2])
    used, sel = set(), []
    for a, b, p in out:
        if a not in used and b not in used:
            sel.append((a, b, p))
            used |= {a, b}
    return sel


@functools.lru_cache(maxsize=64)
def two_step(share: float, t0: int, shortlist: int = 200):
    """The 20 pairs with the smallest Engle-Granger p-values among the `shortlist` pairs of smallest distance."""
    P, R = panel(share)
    ids = np.flatnonzero(P.listed[t0 - FORM:t0].all(axis=0))
    N = _index(R, t0 - FORM, t0, ids)
    sq = (N * N).sum(axis=0)
    D = sq[:, None] + sq[None, :] - 2 * N.T @ N
    i, j = np.triu_indices(len(ids), 1)
    best = np.argsort(D[i, j], kind="stable")[:shortlist]
    L = np.log(N[1:])
    p = pvalue(eg_tau(L[:, i[best]], L[:, j[best]]), null252())
    used, out = set(), []
    for o in np.argsort(p, kind="stable"):
        a, b = int(ids[i[best[o]]]), int(ids[j[best[o]]])
        if a not in used and b not in used:
            out.append((a, b))
            used |= {a, b}
        if len(out) == NPAIRS:
            break
    return out


@functools.lru_cache(maxsize=4)
def discoveries(share: float = TWINS):
    """Per cycle: pairs tested, raw rejections at 5%, Benjamini-Hochberg rejections at 5%; and of the raw rejections
    whose legs stay listed a year, the share rejected again over the next 252 days."""
    P, R = panel(share)
    T = R.shape[0]
    rows = []
    for t0 in cycles(T):
        ids = np.flatnonzero(P.listed[t0 - FORM:t0].all(axis=0))
        L = np.log(_index(R, t0 - FORM, t0, ids)[1:])
        tested = raw = fdr = again = followed = true_raw = true_fdr = true_again = true_followed = 0
        tw = P.twin if P.twin is not None else np.full(R.shape[1], -1)
        for k in range(P.cfg.n_industries):
            loc = np.flatnonzero(P.industry[ids] == k)
            i, j = np.triu_indices(len(loc), 1)
            p = pvalue(eg_tau(L[:, loc[i]], L[:, loc[j]]), null252())
            tested += len(p)
            real = tw[ids[loc[i]]] == ids[loc[j]]
            raw += int((p < 0.05).sum())
            fdr += int(bh(p, 0.05).sum())
            true_raw += int(((p < 0.05) & real).sum())
            true_fdr += int((bh(p, 0.05) & real).sum())
            if t0 + FORM <= T:
                sig = np.flatnonzero(p < 0.05)
                a, b = ids[loc[i[sig]]], ids[loc[j[sig]]]
                keep = P.listed[t0:t0 + FORM][:, a].all(axis=0) & P.listed[t0:t0 + FORM][:, b].all(axis=0)
                if keep.any():
                    Lf = np.log(np.cumprod(1 + R[t0:t0 + FORM][:, np.r_[a[keep], b[keep]]], axis=0))
                    n = keep.sum()
                    p2 = pvalue(eg_tau(Lf[:, :n], Lf[:, n:]), null252())
                    again += int((p2 < 0.05).sum())
                    followed += int(n)
                    r2 = real[sig][keep]
                    true_again += int(((p2 < 0.05) & r2).sum())
                    true_followed += int(r2.sum())
        rows.append({"t0": t0, "tested": tested, "raw": raw, "fdr": fdr, "again": again, "followed": followed,
                     "true_raw": true_raw, "true_fdr": true_fdr, "true_again": true_again,
                     "true_followed": true_followed,
                     "true_pairs": int(sum(1 for q in ids if tw[q] > q and tw[q] in set(ids.tolist())))})
    return rows


@functools.lru_cache(maxsize=16)
def twins(share: float, t0: int):
    """For the 20 most liquid names over the formation year: (target, peers, ridge weights)."""
    P, R = panel(share)
    ids = np.flatnonzero(P.listed[t0 - FORM:t0].all(axis=0))
    dv = np.nanmean(P.price[t0 - FORM:t0][:, ids] * P.volume[t0 - FORM:t0][:, ids], axis=0)
    Rf = np.nan_to_num(R[t0 - FORM:t0])
    out = []
    for y in ids[np.argsort(-dv)[:NPAIRS]]:
        same = ids[(P.industry[ids] == P.industry[y]) & (ids != y)]
        c = np.array([np.corrcoef(Rf[:, y], Rf[:, s])[0, 1] for s in same])
        peers = same[np.argsort(-c)[:PEERS]]
        w = twin(Rf[:, y], Rf[:, peers], LAMBDA)
        out.append((int(y), peers, w))
    return out


THRESHOLDS = (0.001, 0.005, 0.01, 0.02, 0.05, 0.1)


@functools.lru_cache(maxsize=2)
def calibration(share: float = 0.0):
    """Share of all tested same-industry pairs (none cointegrated when share = 0) with a p-value below each threshold:
    a valid test rejects each threshold's share."""
    P, R = panel(share)
    ps = []
    for t0 in cycles(R.shape[0]):
        ids = np.flatnonzero(P.listed[t0 - FORM:t0].all(axis=0))
        L = np.log(_index(R, t0 - FORM, t0, ids)[1:])
        for k in range(P.cfg.n_industries):
            loc = np.flatnonzero(P.industry[ids] == k)
            i, j = np.triu_indices(len(loc), 1)
            ps.append(pvalue(eg_tau(L[:, loc[i]], L[:, loc[j]]), null252()))
    p = np.concatenate(ps)
    return {x: float((p < x).mean()) for x in THRESHOLDS}


def takeover(share: float = TWINS, t0: int = 630, pair: tuple = (167, 190)):
    """The chapter's opening example: the planted substitutes 167 and 190, formed over the year to day 630 and traded
    over the next 126 days, when 167 is taken over. Returns the spread, its formation sd and the cumulative P&L."""
    P, R = panel(share)
    ra, rb, spread, sd, k = legs(share, t0, "distance", pair)
    g, trades, opened, side = trade_pair(ra, rb, spread, sd, k, 0.0)
    return {"spread": spread, "sd": sd, "pnl": np.cumsum(g), "day": int(P.end[pair[0]] - t0),
            "reason": P.delist[pair[0]][1], "opened": opened, "side": side, "twins": bool(P.twin[pair[0]] == pair[1])}
