"""firm.consolidated -- one stock, many venues (build of One Quant Book 10, chapter 8).

Venue tops are structured arrays (t seconds, bid, bid_qty, ask, ask_qty), bid or ask 0 when a side is empty (the
format of firm.tape's `top` and of firm.exchsim's Result.tape(venue).top). The consolidated view is Book 1's
firm_nbbo (a quote is protected only from one round lot); a delayed view shifts each venue's updates by its delay,
as a consolidated feed receives them.

API (stable):
    nbbo_events(tops, delays=None, round_lot=100)   the NBBO after every venue update: (t, bid, bid_size, ask,
                                                    ask_size); -1 and 0 when a side has no protected quote
                                                    (firm_nbbo then has no NBBO at all)
    sample(nb, grid)                                the NBBO in force at each grid time
    disagreement(a, b, lo, hi)                      share of time on [lo, hi) when two NBBO paths differ in bid or ask
    locked_crossed(nb, lo, hi)                      time shares locked and crossed, episodes, median durations
    vecm(p, lags)                                   error-correction model of n prices with cointegrating vectors
                                                    p_1 - p_j: alpha (n x n-1), gammas, residual covariance omega
    information_shares(p, lags)                     Hasbrouck's information shares (bounds over the n! orderings)
                                                    and Gonzalo-Granger component shares
"""
from __future__ import annotations

import itertools
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "nbbo"))
from firm_nbbo import NbboBuilder, Quote  # noqa: E402

NBBO = np.dtype([("t", "f8"), ("bid", "i8"), ("bid_size", "i8"), ("ask", "i8"), ("ask_size", "i8")])


def nbbo_events(tops: dict, delays: dict | None = None, round_lot: int = 100) -> np.ndarray:
    delays = delays or {}
    ev = []
    for venue, top in tops.items():
        d = delays.get(venue, 0.0)
        for r in top:
            ev.append((float(r["t"]) + d, venue, int(r["bid"]), int(r["bid_qty"]), int(r["ask"]), int(r["ask_qty"])))
    ev.sort(key=lambda e: e[0])
    nb = NbboBuilder(round_lot)
    out = []
    for t, venue, b, bq, a, aq in ev:
        nb.update(Quote(venue, b if b > 0 else 1, bq if b > 0 else 0, a if a > 0 else 1, aq if a > 0 else 0))
        n = nb.nbbo()
        row = (t, n.bid, n.bid_size, n.ask, n.ask_size) if n is not None else (t, -1, 0, -1, 0)
        if out and out[-1][0] == t:
            out[-1] = row
        elif not out or out[-1][1:] != row[1:]:
            out.append(row)
    return np.array(out, dtype=NBBO)


def sample(nb: np.ndarray, grid) -> np.ndarray:
    i = np.searchsorted(nb["t"], np.asarray(grid, float), side="right") - 1
    return nb[np.clip(i, 0, len(nb) - 1)]


def disagreement(a: np.ndarray, b: np.ndarray, lo: float, hi: float) -> float:
    t = np.unique(np.concatenate([a["t"], b["t"], [lo, hi]]))
    t = t[(t >= lo) & (t <= hi)]
    sa, sb = sample(a, t[:-1]), sample(b, t[:-1])
    diff = (sa["bid"] != sb["bid"]) | (sa["ask"] != sb["ask"])
    dt = np.diff(t)
    return float(dt[diff].sum() / dt.sum())


def locked_crossed(nb: np.ndarray, lo: float, hi: float) -> dict:
    t = np.concatenate([nb["t"], [hi]])
    dt = np.diff(np.clip(t, lo, hi))
    ok = (nb["bid"] > 0) & (nb["ask"] > 0)
    out = {}
    for name, mask in (("locked", ok & (nb["bid"] == nb["ask"])), ("crossed", ok & (nb["bid"] > nb["ask"]))):
        starts = np.flatnonzero(mask & ~np.concatenate([[False], mask[:-1]]))
        durs = []
        for s in starts:
            e = s
            while e < len(mask) and mask[e]:
                e += 1
            durs.append(t[e] - t[s])
        out[name] = float(dt[mask].sum() / (hi - lo))
        out[name + "_episodes"] = len(starts)
        out[name + "_median_s"] = float(np.median(durs)) if durs else 0.0
    return out


def vecm(p, lags: int = 5) -> dict:
    p = np.asarray(p, float)
    T, n = p.shape
    dp = np.diff(p, axis=0)
    z = p[:-1, [0]] - p[:-1, 1:]                         # n - 1 cointegrating relations, lagged one step
    rows = range(lags, T - 1)
    X = np.array([np.concatenate([z[t], *[dp[t - k] for k in range(1, lags + 1)]]) for t in rows])
    Y = dp[lags:]
    B, *_ = np.linalg.lstsq(X, Y, rcond=None)
    resid = Y - X @ B
    alpha = B[: n - 1].T                                 # n x (n - 1)
    gammas = [B[n - 1 + (k - 1) * n: n - 1 + k * n].T for k in range(1, lags + 1)]
    return {"alpha": alpha, "gammas": gammas, "omega": resid.T @ resid / len(resid)}


def information_shares(p, lags: int = 5) -> dict:
    m = vecm(p, lags)
    alpha, omega = m["alpha"], m["omega"]
    n = alpha.shape[0]
    _, _, vt = np.linalg.svd(alpha.T)          # alpha_perp spans the null space of alpha'
    a_perp = vt[-1]
    gamma1 = np.eye(n) - sum(m["gammas"])
    psi = a_perp / (a_perp @ gamma1 @ np.ones(n))
    lo, hi = np.full(n, np.inf), np.full(n, -np.inf)
    for perm in itertools.permutations(range(n)):
        idx = list(perm)
        f = np.linalg.cholesky(omega[np.ix_(idx, idx)])
        share = (psi[idx] @ f) ** 2 / (psi @ omega @ psi)
        for k, j in enumerate(idx):
            lo[j], hi[j] = min(lo[j], share[k]), max(hi[j], share[k])
    cs = a_perp / a_perp.sum()
    return {"is_low": lo, "is_high": hi, "is_mid": 0.5 * (lo + hi),
            "component_share": cs, "psi": psi}
