"""Residual and principal-component stat arb (One Quant Book 8, chapter 3).

Avellaneda and Lee's s-score strategy on firm.synthmkt (seed 1) with a planted mean-reverting level in each stock's
specific return (MarketConfig.ou_share of its variance, mean-reversion times lognormal around 20 days), and on the
default market without it: every day, each stock's last 60 returns are regressed on its sector index (cap-weighted
industry returns, the "ETF" version) or on 15 eigenportfolios of the last year's correlation matrix (re-estimated every
21 days, the "PCA" version); the cumulative residual's AR(1) fit gives kappa and the s-score; positions of 1% of capital
open at |s| > 1.25 and close at s > -0.5 (longs) or s < 0.75 (shorts), each hedged with its betas in the factors, only
in names with kappa above a threshold (252 / 30 in the paper) when the speed filter is on; 5 basis points per unit
traded in stocks and in the hedges. Years 3 to 10. NumPy only.
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

FIRM = pathlib.Path(__file__).resolve().parents[3] / "firm"
for c in ("residarb", "synthmkt"):
    sys.path.insert(0, str(FIRM / c))
from firm_residarb import eigenportfolios, ou_fit, regress, s_score, speed_ok, step, volume_adjust  # noqa: E402
from firm_synthmkt import MarketConfig, simulate  # noqa: E402

YEAR, START, W, K, LAM, COST, SHARE = 252, 2 * 252, 60, 15, 0.01, 0.0005, 0.3


@functools.lru_cache(maxsize=3)
def panel(share: float = SHARE):
    P = simulate(MarketConfig(ou_share=share))
    R = np.where(P.listed, P.ret, np.nan)
    cap = np.where(P.listed, P.price * P.shares, 0.0)
    cprev = np.vstack([cap[:1], cap[:-1]])
    Kn = P.cfg.n_industries
    ind = np.zeros((R.shape[0], Kn))
    for k in range(Kn):
        m = P.industry == k
        wk = cprev[:, m]
        ind[:, k] = np.nansum(wk * np.nan_to_num(R[:, m]), axis=1) / np.maximum(wk.sum(axis=1), 1e-12)
    vol = np.where(P.listed, P.volume, np.nan)
    return P, R, ind, vol


@functools.lru_cache(maxsize=3)
def avg_volume(share: float = SHARE, n: int = 10):
    vol = panel(share)[3]
    v, ok = np.nan_to_num(vol), np.isfinite(vol)
    cv, cn = np.cumsum(v, axis=0), np.cumsum(ok, axis=0)
    pad = lambda c: np.vstack([np.zeros((n, c.shape[1])), c[:-n]])  # noqa: E731
    return (cv - pad(cv)) / np.maximum(cn - pad(cn), 1)


def sharpe(x) -> float:
    x = np.asarray(x, float)
    return float(x.mean() / x.std(ddof=1) * math.sqrt(YEAR)) if x.std() > 0 else 0.0


@functools.lru_cache(maxsize=64)
def run(share: float = SHARE, method: str = "etf", s_open: float = 1.25, min_kappa: float = YEAR / 30,
        volume: bool = False):
    """One backtest; min_kappa 0 switches the speed filter off."""
    P, R, ind, vol = panel(share)
    T, M = R.shape
    truth = P.alpha.get("ou")
    pos = np.zeros(M, int)
    w0, h0 = np.zeros(M), np.zeros(K if method == "pca" else ind.shape[1])
    gross, costs, npos, passed, turn, corr, share_k = [], [], [], [], [], [], []
    Q, uni = None, None
    avg10 = avg_volume(share) if volume else None
    for t in range(START - 1, T - 1):
        full = P.listed[t - W + 1:t + 1].all(axis=0) & P.listed[t + 1]
        if method == "pca" and (Q is None or (t - START + 1) % 21 == 0):
            uni = P.listed[t - YEAR + 1:t + 1].all(axis=0)
            Q, ex = eigenportfolios(R[t - YEAR + 1:t + 1][:, uni], K)
            share_k.append(ex)
        if method == "pca":
            full &= uni
        idx = np.flatnonzero(full)
        Rw = R[t - W + 1:t + 1][:, idx]
        if volume:
            v = vol[t - W + 1:t + 1][:, idx]
            avg = avg10[t - W + 1:t + 1][:, idx]                       # the trailing 10-day mean volume
            Rw = volume_adjust(Rw, v, avg)
        if method == "etf":
            beta, e = regress(Rw, ind[t - W + 1:t + 1][:, P.industry[idx]], per_name=True)
        else:
            Fw = np.nan_to_num(R[t - W + 1:t + 1][:, uni]) @ Q.T
            beta, e = regress(Rw, Fw)
        fit = ou_fit(e)
        s = s_score(fit)
        ok = speed_ok(fit["kappa"], min_kappa)
        new = np.zeros(M, int)
        new[idx] = step(pos[idx], s, ok, s_open)
        pos = new
        w = LAM * pos
        r1 = np.nan_to_num(R[t + 1])
        if method == "etf":
            h = np.bincount(P.industry[idx], weights=w[idx] * beta, minlength=ind.shape[1])
            f1 = ind[t + 1]
        else:
            h = beta @ w[idx]
            f1 = np.nan_to_num(R[t + 1][uni]) @ Q.T
        gross.append(float(w @ r1 - h @ f1))
        costs.append(COST * (float(np.abs(w - w0).sum()) + float(np.abs(h - h0).sum())))
        npos.append(int((pos != 0).sum()))
        passed.append(float(ok.mean()))
        turn.append(float(np.abs(w - w0).sum()) / 2)
        if truth is not None and np.isfinite(s).sum() > 20:
            a = truth[t, idx]
            g = np.isfinite(s) & np.isfinite(a)
            corr.append(float(np.corrcoef(s[g], a[g])[0, 1]))
        w0, h0 = w * (1 + r1), h
    g, c = np.array(gross), np.array(costs)
    n = np.array(npos)
    return {"sr_gross": sharpe(g), "sr_net": sharpe(g - c), "ret_net": float((g - c).mean() * YEAR),
            "cost": float(c.mean() * YEAR), "vol": float((g - c).std(ddof=1) * math.sqrt(YEAR)),
            "positions": float(n.mean()), "passed": float(np.mean(passed)), "turnover": float(np.mean(turn[1:])),
            "explained": float(np.mean(share_k)) if share_k else float("nan"), "gross": LAM * float(n.mean()),
            "corr_truth": float(np.mean(corr)) if corr else float("nan"), "net": g - c}


def path(pid: int, share: float = SHARE, first: int = 5 * YEAR, days: int = YEAR):
    """One name's s-score, kappa and position over `days` from day `first` (sector-index version)."""
    P, R, ind, _ = panel(share)
    pos, out = np.zeros(1, int), []
    k = P.industry[pid]
    for t in range(first, first + days):
        beta, e = regress(R[t - W + 1:t + 1, [pid]], ind[t - W + 1:t + 1, [k]], per_name=True)
        fit = ou_fit(e)
        s = s_score(fit, center=False)
        pos = step(pos, s, speed_ok(fit["kappa"]))
        out.append((t, float(s[0]), float(fit["kappa"][0]), int(pos[0])))
    return out


@functools.lru_cache(maxsize=2)
def stability(share: float = SHARE, every: int = 21):
    """For each re-estimation: the top-15 explained share, and the overlap with the previous estimate on the names
    common to both (first eigenvector: |cos|; the 15-dimensional subspaces: trace(P1 P2) / 15)."""
    P, R, _, _ = panel(share)
    T = R.shape[0]
    rows, prev = [], None
    for t in range(START - 1, T - 1, every):
        uni = P.listed[t - YEAR + 1:t + 1].all(axis=0)
        X = R[t - YEAR + 1:t + 1][:, uni]
        Z = (X - X.mean(axis=0)) / X.std(axis=0, ddof=1)
        lam, V = np.linalg.eigh(Z.T @ Z / (len(Z) - 1))
        lam, V = lam[::-1], V[:, ::-1][:, :K]
        ids = np.flatnonzero(uni)
        row = {"t": t, "explained": float(lam[:K].sum() / lam.sum()), "first": float(lam[0] / lam.sum())}
        if prev is not None:
            common, i1, i2 = np.intersect1d(prev[0], ids, return_indices=True)
            A, B = prev[1][i1], V[i2]
            A, B = np.linalg.qr(A)[0], np.linalg.qr(B)[0]
            row["v1"] = float(abs(A[:, 0] @ B[:, 0]))
            row["subspace"] = float(np.sum((A.T @ B) ** 2) / K)
            s = np.linalg.svd(A.T @ B, compute_uv=False)
            row["min_cos"] = float(s.min())
        rows.append(row)
        prev = (ids, V)
    return rows
