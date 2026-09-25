"""firm.tcost -- transaction costs in research (build of One Quant Book 7, chapter 27).

A cost model per trade: half the spread, fees, and a square-root impact eta * sigma * sqrt(Q / V) (as a fraction of
the traded value), with eta and the exponent fitted from the firm's own fills; the cost of a vector of weight changes
for a book of given size; cost-aware mean-variance optimisation with these (non-quadratic) costs inside the objective,
solved by accelerated proximal gradient with the exact proximal step of s|x| + c|x|^(3/2); the netting of several
strategies' trade lists with the saving shared out; signal smoothing and the break-even cost. NumPy only.

API (stable):
    impact_bp(eta, sigma, participation, exponent)      eta * sigma * participation ** exponent (fractions)
    fit_impact(cost, sigma, participation, half_spread)  {'eta', 'exponent', 'se_exponent', 'eta_fixed', 'se_eta'}:
                                                         log-log fit on binned averages, and eta with exponent 1/2
    trade_cost(dw, aum, sigma, adv, half_spread, eta, fee)   total cost as a fraction of capital
    cost_aware(alpha, Sigma, w0, aum, sigma, adv, half_spread, eta, gamma, neutral, iters)
                                                         max alpha'w - gamma/2 w'Sigma w - cost(w - w0)
    prox_cost(v, s, c)                                   argmin_x (x - v)^2 / 2 + s|x| + c|x|^(3/2), elementwise
    net_trades(lists)                                    (net trade, per-strategy gross) of aligned trade vectors
    netting_saving(lists, cost_fn)                       {'standalone', 'netted', 'saving', 'shares'}: saving shared
                                                         in proportion to each strategy's standalone cost
    smooth(signal, half_life)                            exponentially weighted signal along axis 0
    breakeven_cost(gross_return, turnover)               cost per unit traded at which the net return is zero
"""
from __future__ import annotations

import math

import numpy as np


def impact_bp(eta: float, sigma, participation, exponent: float = 0.5):
    return eta * np.asarray(sigma, float) * np.asarray(participation, float) ** exponent


def fit_impact(cost, sigma, participation, half_spread, bins: int = 20):
    """cost: realised cost of each parent order as a fraction of value (signed so that positive is a loss), sigma:
    daily volatility, participation: Q / V. Averages within participation bins remove most of the price noise; the
    exponent comes from log(mean cost - half spread) on log participation, eta from the fit with exponent 1/2."""
    c, s, p = (np.asarray(a, float) for a in (cost, sigma, participation))
    y = (c - half_spread) / s
    edges = np.quantile(p, np.linspace(0, 1, bins + 1))
    idx = np.clip(np.searchsorted(edges, p, side="right") - 1, 0, bins - 1)
    xm = np.array([p[idx == k].mean() for k in range(bins)])
    ym = np.array([y[idx == k].mean() for k in range(bins)])
    se_m = np.array([y[idx == k].std(ddof=1) / math.sqrt((idx == k).sum()) for k in range(bins)])
    ok = ym > 0
    X = np.column_stack([np.ones(ok.sum()), np.log(xm[ok])])
    wts = (ym[ok] / se_m[ok]) ** 2                                       # delta method: var(log m) = (se / m)^2
    A = X.T @ (wts[:, None] * X)
    beta = np.linalg.solve(A, X.T @ (wts * np.log(ym[ok])))
    cov = np.linalg.inv(A)
    root = np.sqrt(p)
    eta = float(root @ y / (root @ root))
    resid = y - eta * root
    se_eta = float(math.sqrt((root**2 * resid**2).sum()) / (root @ root))      # robust: the noise grows with size
    return {"eta": float(math.exp(beta[0])), "exponent": float(beta[1]), "se_exponent": float(math.sqrt(cov[1, 1])),
            "eta_fixed": eta, "se_eta": se_eta}


def trade_cost(dw, aum: float, sigma, adv, half_spread, eta: float, fee: float = 0.0) -> float:
    """sum_i |dw_i| (half_spread_i + fee) + eta sigma_i |dw_i| sqrt(|dw_i| aum / adv_i): the cost of the trade as a
    fraction of capital (impact on each name's traded value)."""
    a = np.abs(np.asarray(dw, float))
    lin = np.asarray(half_spread, float) + fee
    return float(np.sum(a * lin + eta * np.asarray(sigma, float) * a * np.sqrt(a * aum / np.asarray(adv, float))))


def prox_cost(v, s, c):
    """Minimise (x - v)^2 / 2 + s|x| + c|x|^(3/2): shrink |v| by s, then y = sqrt(x) solves y^2 + 1.5 c y = |v| - s."""
    v, s, c = (np.asarray(a, float) for a in (v, s, c))
    r = np.maximum(np.abs(v) - s, 0.0)
    y = (-1.5 * c + np.sqrt((1.5 * c) ** 2 + 4 * r)) / 2
    return np.sign(v) * y * y


def cost_aware(alpha, Sigma, w0, aum: float, sigma, adv, half_spread, eta: float, gamma: float,
               neutral: float = 0.0, iters: int = 500, tol: float = 1e-12):
    """FISTA on f(w) = gamma/2 w'Sigma w - alpha'w + neutral/2 (1'w)^2 with the separable cost as the proximal term
    (in d = w - w0: s_i |d_i| + c_i |d_i|^(3/2), c_i = eta sigma_i sqrt(aum / adv_i))."""
    alpha, Sigma, w0 = (np.asarray(a, float) for a in (alpha, Sigma, w0))
    n = len(alpha)
    Hm = gamma * Sigma + neutral * np.ones((n, n))
    L = float(np.linalg.eigvalsh(Hm).max())
    s = np.asarray(half_spread, float) * np.ones(n)
    c = eta * np.asarray(sigma, float) * np.sqrt(aum / np.asarray(adv, float))
    w = w0.copy()
    z, tk = w.copy(), 1.0
    for _ in range(iters):
        g = Hm @ z - alpha
        new = w0 + prox_cost(z - g / L - w0, s / L, c / L)
        t1 = (1 + math.sqrt(1 + 4 * tk * tk)) / 2
        z = new + (tk - 1) / t1 * (new - w)
        if np.abs(new - w).max() < tol:
            w = new
            break
        w, tk = new, t1
    return w


def net_trades(lists):
    T = np.asarray(lists, float)
    return T.sum(axis=0), T


def netting_saving(lists, cost_fn):
    net, T = net_trades(lists)
    alone = np.array([cost_fn(t) for t in T])
    netted = cost_fn(net)
    saving = float(alone.sum() - netted)
    return {"standalone": alone, "netted": float(netted), "saving": saving, "shares": saving * alone / alone.sum()}


def smooth(signal, half_life: float):
    x = np.asarray(signal, float)
    lam = 0.5 ** (1.0 / half_life) if half_life > 0 else 0.0
    out = np.empty_like(x)
    acc = x[0]
    for t in range(len(x)):
        acc = lam * acc + (1 - lam) * x[t] if t else x[0]
        out[t] = acc
    return out


def breakeven_cost(gross_return: float, turnover: float) -> float:
    return gross_return / turnover
