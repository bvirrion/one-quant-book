"""firm.spreadmodels -- why there is a spread: the classic models (build of One Quant Book 10, chapter 4).

API (stable):
    gm_quotes(delta, mu, v_low, v_high) -> (bid, ask)      Glosten-Milgrom with a two-point value: delta = P(v_high),
                                                          mu = share of informed traders, noise traders buy or sell
                                                          with probability 1/2
    gm_update(delta, side, mu) -> delta                   Bayes after a buy (+1) or a sell (-1)
    gm_path(v_is_high, mu, n, seed, delta0=0.5) -> dict   quotes, trades and beliefs along n arrivals
    kyle_one_period(sigma_v, sigma_u) -> dict             beta, lambda, posterior variance, insider's expected profit
    kyle_simulate(sigma_v, sigma_u, n, seed) -> dict      draws of (v, u, x, p) and the regression slope of p on x + u
    inventory_quotes(v, q, size, gamma, sigma, horizon)   (bid, ask) of a mean-variance dealer holding q
    roll_spread(prices) -> float                          2 sqrt(-Cov(dp_t, dp_t-1)) (One Quant Book 4, chapter 21)
    pin_loglik(theta, buys, sells) -> float               Easley-Kiefer-O'Hara-Paperman; theta = (alpha, delta, mu,
                                                          eb, es)
    pin_fit(buys, sells, starts=...) -> dict              maximum likelihood (L-BFGS-B, several starts); PIN
    pin(theta) -> float                                   alpha mu / (alpha mu + eb + es)
    simulate_days(n, theta, seed, activity_sd=0.0)        daily buy and sell counts; activity_sd > 0 multiplies both
                                                          uninformed rates by a common lognormal day factor
"""
from __future__ import annotations

import math

import numpy as np
from scipy.optimize import minimize
from scipy.special import gammaln, logsumexp


def gm_quotes(delta: float, mu: float, v_low: float = 0.0, v_high: float = 1.0) -> tuple[float, float]:
    dv = v_high - v_low
    ask = v_low + dv * delta * (1 + mu) / (delta * (1 + mu) + (1 - delta) * (1 - mu))
    bid = v_low + dv * delta * (1 - mu) / (delta * (1 - mu) + (1 - delta) * (1 + mu))
    return bid, ask


def gm_update(delta: float, side: int, mu: float) -> float:
    ph = (1 + mu) / 2 if side > 0 else (1 - mu) / 2        # P(side | v_high)
    pl = (1 - mu) / 2 if side > 0 else (1 + mu) / 2        # P(side | v_low)
    return delta * ph / (delta * ph + (1 - delta) * pl)


def gm_path(v_is_high: bool, mu: float, n: int = 200, seed: int = 1, delta0: float = 0.5) -> dict:
    rng = np.random.default_rng(seed)
    d = delta0
    bids, asks, deltas, sides = [], [], [], []
    for _ in range(n):
        b, a = gm_quotes(d, mu)
        bids.append(b)
        asks.append(a)
        deltas.append(d)
        if rng.random() < mu:
            side = 1 if v_is_high else -1
        else:
            side = 1 if rng.random() < 0.5 else -1
        sides.append(side)
        d = gm_update(d, side, mu)
    return {"bid": np.array(bids), "ask": np.array(asks), "delta": np.array(deltas), "side": np.array(sides)}


def kyle_one_period(sigma_v: float, sigma_u: float) -> dict:
    beta = sigma_u / sigma_v
    lam = sigma_v / (2.0 * sigma_u)
    return {"beta": beta, "lambda": lam, "posterior_var": sigma_v**2 / 2.0, "profit": sigma_v * sigma_u / 2.0}


def kyle_simulate(sigma_v: float, sigma_u: float, n: int = 100_000, seed: int = 1, p0: float = 0.0) -> dict:
    k = kyle_one_period(sigma_v, sigma_u)
    rng = np.random.default_rng(seed)
    v = p0 + sigma_v * rng.standard_normal(n)
    u = sigma_u * rng.standard_normal(n)
    x = k["beta"] * (v - p0)
    y = x + u
    p = p0 + k["lambda"] * y
    slope = float(np.cov(p, y)[0, 1] / np.var(y, ddof=1))
    resid_var = float(np.var(v - p))
    profit = float(np.mean(x * (v - p)))
    return {"slope": slope, "posterior_var": resid_var, "profit": profit, "v": v, "p": p, "y": y}


def inventory_quotes(v: float, q: float, size: float, gamma: float, sigma: float,
                     horizon: float) -> tuple[float, float]:
    """Quotes of a dealer who marks inventory to v and charges gamma/2 sigma^2 horizon q^2 for holding q: the price
    at which a trade of `size` leaves its mean-variance utility unchanged (the ask for a client buy, the bid for a
    sale)."""
    k = gamma * sigma**2 * horizon
    ask = v + k * (size / 2.0 - q)
    bid = v - k * (size / 2.0 + q)
    return bid, ask


def roll_spread(prices) -> float:
    dp = np.diff(np.asarray(prices, float))
    c = np.cov(dp[1:], dp[:-1])[0, 1]
    return float(2.0 * math.sqrt(-c)) if c < 0 else float("nan")


def pin(theta) -> float:
    a, _, mu, eb, es = theta
    return a * mu / (a * mu + eb + es)


def _logpois(k, lam):
    return k * np.log(lam) - lam - gammaln(k + 1)


def pin_loglik(theta, buys, sells) -> float:
    a, d, mu, eb, es = theta
    b = np.asarray(buys, float)
    s = np.asarray(sells, float)
    terms = np.stack([np.log(1 - a) + _logpois(b, eb) + _logpois(s, es),
                      np.log(a * d) + _logpois(b, eb) + _logpois(s, es + mu),
                      np.log(a * (1 - d)) + _logpois(b, eb + mu) + _logpois(s, es)])
    return float(logsumexp(terms, axis=0).sum())


def pin_fit(buys, sells, starts=((0.3, 0.5), (0.5, 0.3), (0.7, 0.7))) -> dict:
    b, s = np.asarray(buys, float), np.asarray(sells, float)
    mb, ms = b.mean(), s.mean()
    best = None
    for a0, d0 in starts:
        x0 = np.array([a0, d0, max(abs(mb - ms), 0.5 * min(mb, ms)), 0.75 * mb, 0.75 * ms])
        res = minimize(lambda th: -pin_loglik(th, b, s), x0, method="L-BFGS-B",
                       bounds=[(1e-4, 1 - 1e-4), (1e-4, 1 - 1e-4), (1e-3, None), (1e-3, None), (1e-3, None)])
        if best is None or res.fun < best.fun:
            best = res
    th = best.x
    return {"theta": tuple(float(x) for x in th), "pin": pin(th), "loglik": -float(best.fun)}


def simulate_days(n: int, theta, seed: int = 1, activity_sd: float = 0.0) -> tuple[np.ndarray, np.ndarray]:
    a, d, mu, eb, es = theta
    rng = np.random.default_rng(seed)
    buys, sells = np.zeros(n, int), np.zeros(n, int)
    for i in range(n):
        f = math.exp(activity_sd * rng.standard_normal() - 0.5 * activity_sd**2) if activity_sd else 1.0
        lb, ls = eb * f, es * f
        if rng.random() < a:
            if rng.random() < d:
                ls += mu
            else:
                lb += mu
        buys[i], sells[i] = rng.poisson(lb), rng.poisson(ls)
    return buys, sells
