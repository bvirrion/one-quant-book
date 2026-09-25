"""firm.intraml -- machine-learned intraday alphas (build of One Quant Book 8, chapter 14).

Features sampled every second from a message-level tape (firm.tape): the top-of-book imbalance, the spread, order-flow
imbalance (Cont, Kukanov and Stoikov) over 1, 5 and 30 seconds, the signed trade volume over 5 and 30 seconds, the mid's
return over 5 and 30 seconds, and the microprice's distance from the mid; targets are the mid's change over the next h
seconds, in ticks. Models: ridge regression and a small gradient-boosted ensemble of depth-two regression trees, in
NumPy. Execution: an aggressive order crosses the spread when the forecast exceeds a threshold; a passive order joins
the touch and is filled only if the market trades through it within a wait, with the exit crossing the spread. NumPy
only.

API (stable):
    features(tape, step)                     (times (n,), X (n, 10), names, mid ticks at those times)
    targets(tape, times, horizons)           {h: mid change over the next h seconds, in ticks}
    ridge(X, y, lam) / ridge_predict(b, X)   standardised ridge with intercept
    gbm(X, y, trees, rate, bins) / gbm_predict(model, X)
                                             boosted depth-two trees on quantile split points
    r2(y, yhat)                              out-of-sample R-squared against zero
    aggressive(pred, fwd, spread, threshold) per-trade P&L in ticks: sign x move minus the spread paid
    passive(tape, times, pred, h, threshold, wait)
                                             per-fill P&L in ticks for touch-joining entries with a crossing exit
"""
from __future__ import annotations

import numpy as np

NAMES = ("imbalance", "spread", "ofi_1", "ofi_5", "ofi_30", "flow_5", "flow_30", "ret_5", "ret_30", "micro")


def _at(t_src, t_query):
    """Index of the last source time at or before each query time."""
    return np.maximum(np.searchsorted(t_src, t_query, side="right") - 1, 0)


def features(tape, step: float = 1.0):
    top = tape.top
    t = top["t"]
    bid, ask = top["bid"].astype(float), top["ask"].astype(float)
    bq, aq = top["bid_qty"].astype(float), top["ask_qty"].astype(float)
    e = np.zeros(len(t))                                          # order-flow imbalance increments
    e[1:] = ((bid[1:] >= bid[:-1]) * bq[1:] - (bid[1:] <= bid[:-1]) * bq[:-1]
             - (ask[1:] <= ask[:-1]) * aq[1:] + (ask[1:] >= ask[:-1]) * aq[:-1])
    ce = np.cumsum(e)
    tr = tape.trades
    cf = np.concatenate([[0.0], np.cumsum(tr["sign"] * tr["qty"].astype(float))])
    times = np.arange(30.0, tape.cfg.seconds - 1e-9, step)
    i = _at(t, times)
    mid = 0.5 * (bid + ask)

    def lag(k, arr):
        return arr[i] - arr[_at(t, times - k)]

    def flow(k):
        return cf[np.searchsorted(tr["t"], times, side="right")] - cf[np.searchsorted(tr["t"], times - k, side="right")]

    depth = np.maximum(bq[i] + aq[i], 1.0)
    X = np.column_stack([(bq[i] - aq[i]) / depth, ask[i] - bid[i], lag(1, ce) / depth, lag(5, ce) / depth,
                         lag(30, ce) / depth, flow(5) / depth, flow(30) / depth, lag(5, mid), lag(30, mid),
                         (bid[i] * aq[i] + ask[i] * bq[i]) / depth - mid[i]])
    return times, X, NAMES, mid[i]


def targets(tape, times, horizons=(5, 30, 120)):
    top = tape.top
    mid = 0.5 * (top["bid"].astype(float) + top["ask"].astype(float))
    now = mid[_at(top["t"], times)]
    return {h: np.where(times + h <= tape.cfg.seconds, mid[_at(top["t"], times + h)] - now, np.nan) for h in horizons}


def ridge(X, y, lam: float = 1.0):
    mu, sd = X.mean(axis=0), X.std(axis=0) + 1e-12
    Z = (X - mu) / sd
    b = np.linalg.solve(Z.T @ Z + lam * np.eye(Z.shape[1]), Z.T @ (y - y.mean()))
    return {"mu": mu, "sd": sd, "b": b, "c": float(y.mean())}


def ridge_predict(m, X):
    return m["c"] + ((X - m["mu"]) / m["sd"]) @ m["b"]


def _best_split(X, g, cuts):
    best = (0.0, None, None)
    for j in range(X.shape[1]):
        for c in cuts[j]:
            left = X[:, j] <= c
            nl, nr = left.sum(), (~left).sum()
            if nl < 50 or nr < 50:
                continue
            gain = g[left].sum() ** 2 / nl + g[~left].sum() ** 2 / nr
            if gain > best[0]:
                best = (gain, j, c)
    return best[1], best[2]


def _tree(X, g, cuts):
    j, c = _best_split(X, g, cuts)
    if j is None:
        return (None, None, float(g.mean()), float(g.mean()), None)
    left = X[:, j] <= c
    kids = []
    for side in (left, ~left):
        jj, cc = _best_split(X[side], g[side], cuts)
        if jj is None:
            kids.append((None, None, float(g[side].mean()), float(g[side].mean())))
        else:
            s2 = X[side][:, jj] <= cc
            kids.append((jj, cc, float(g[side][s2].mean()), float(g[side][~s2].mean())))
    return (j, c, None, None, kids)


def _tree_predict(tree, X):
    j, c, a, b, kids = tree
    if j is None:
        return np.full(len(X), a)
    left = X[:, j] <= c
    out = np.empty(len(X))
    for side, (jj, cc, va, vb) in zip((left, ~left), kids, strict=True):
        if jj is None:
            out[side] = va
        else:
            out[side] = np.where(X[side][:, jj] <= cc, va, vb)
    return out


def gbm(X, y, trees: int = 60, rate: float = 0.1, bins: int = 16):
    cuts = [np.unique(np.quantile(X[:, j], np.linspace(0.05, 0.95, bins))) for j in range(X.shape[1])]
    f0 = float(y.mean())
    pred = np.full(len(y), f0)
    model = []
    for _ in range(trees):
        tree = _tree(X, y - pred, cuts)
        pred += rate * _tree_predict(tree, X)
        model.append(tree)
    return {"f0": f0, "rate": rate, "trees": model}


def gbm_predict(m, X):
    out = np.full(len(X), m["f0"])
    for tree in m["trees"]:
        out += m["rate"] * _tree_predict(tree, X)
    return out


def r2(y, yhat):
    ok = np.isfinite(y)
    return float(1 - np.sum((y[ok] - yhat[ok]) ** 2) / np.sum(y[ok] ** 2))


def aggressive(pred, fwd, spread, threshold: float):
    """Enter across the spread and exit across it h seconds later: P&L = sign x move - spread (ticks per share)."""
    go = (np.abs(pred) > threshold) & np.isfinite(fwd)
    return np.sign(pred[go]) * fwd[go] - spread[go]


def passive(tape, times, pred, h: float, threshold: float, wait: float = 10.0):
    """Join the touch in the forecast's direction; filled if a trade prints through the price within `wait`; exit across
    the spread h seconds after the fill."""
    top, tr = tape.top, tape.trades
    tt = top["t"]
    out = []
    for k in np.flatnonzero(np.abs(pred) > threshold):
        t0 = times[k]
        i = _at(tt, t0)
        side = 1 if pred[k] > 0 else -1
        px = top["bid"][i] if side > 0 else top["ask"][i]
        a, b = np.searchsorted(tr["t"], t0, side="right"), np.searchsorted(tr["t"], t0 + wait, side="right")
        hit = np.flatnonzero((tr["sign"][a:b] == -side) & (side * (tr["price"][a:b] - px) <= 0))
        if len(hit) == 0 or tr["t"][a + hit[0]] + h > tape.cfg.seconds:
            continue
        j = _at(tt, tr["t"][a + hit[0]] + h)
        exit_px = top["bid"][j] if side > 0 else top["ask"][j]
        out.append(side * (exit_px - px))
    return np.array(out, float)
