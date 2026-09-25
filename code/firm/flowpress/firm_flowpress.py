"""firm.flowpress -- mutual-fund flows and the price pressure they cause (build of One Quant Book 8, chapter 9).

Simulated funds on a price panel: each fund holds an equal-weighted book of stocks chosen at random or with a tilt
toward its own style, and replaces a share of them every quarter, owns a share of each stock in proportion to its
assets, and receives quarterly flows that chase its trailing one-year return (fund sizes are held fixed: the flows are
trades, not a change of size); its flows are traded in proportion to its holdings. Flow-induced trading (Lou, 2012) of
a stock is the sum over funds of the fund's ownership of the stock times the fund's flow: the fraction of the stock's
shares the funds must buy or sell. Each quarter's flow-induced trading pushes the stock's price by `impact` per unit,
spread over the quarter, and the push decays with a half-life. NumPy only.

API (stable):
    FlowConfig(...)                           funds, holdings, flow and impact parameters
    fit(own, flow)                            flow-induced trading: own (F, N) ownership shares, flow (F,) -> (N,)
    flow_rule(trailing, beta, noise, rng)     flows (share of assets) chasing standardised trailing returns
    simulate_flows(R, listed, style, cfg)     {'R': returns with the pressure, 'fit' (Q, N), 'flow' (Q, F),
                                               'trailing' (Q, F), 'own' (Q, F, N), 'quarters', 'pressure' (T, N)}
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class FlowConfig:
    funds: int = 200
    holdings: int = 60
    tilt: float = 0.0                  # strength of each fund's style tilt in choosing stocks (0: at random)
    turnover: float = 0.25             # share of each fund's holdings replaced every quarter
    chase: int = 4                     # quarters of trailing fund return that flows chase
    fund_share: float = 0.20           # average share of each stock owned by the funds together
    beta: float = 0.05                 # quarterly flow (share of assets) per standard deviation of trailing return
    noise: float = 0.03                # idiosyncratic quarterly flow
    impact: float = 1.5                # price push per unit of flow-induced trading (share of shares outstanding)
    half_life: float = 126.0           # days for half of the push to reverse, after the quarter
    quarter: int = 63
    seed: int = 9


def fit(own, flow):
    return np.asarray(flow, float) @ np.asarray(own, float)


def flow_rule(trailing, beta: float, noise: float, rng):
    t = np.asarray(trailing, float)
    z = (t - t.mean()) / (t.std() + 1e-12)
    return beta * z + noise * rng.standard_normal(len(t))


def _pick(listed, style, d, k, tilt, rng):
    ok = np.flatnonzero(listed)
    s = np.nan_to_num(style[ok] @ d)
    p = np.exp(tilt * (s - s.max()))
    return rng.choice(ok, size=min(k, len(ok)), replace=False, p=p / p.sum())


def simulate_flows(R, listed, style, cfg: FlowConfig | None = None):
    """R (T, N) returns (NaN where not listed), style (N, K) exposures used for the tilts."""
    cfg = cfg or FlowConfig()
    R, listed = np.asarray(R, float), np.asarray(listed, bool)
    T, N = R.shape
    rng = np.random.default_rng(cfg.seed)
    dirs = rng.standard_normal((cfg.funds, style.shape[1]))
    books = [_pick(listed[0], style, dirs[f], cfg.holdings, cfg.tilt, rng) for f in range(cfg.funds)]
    aum = np.exp(0.8 * rng.standard_normal(cfg.funds))
    Q = T // cfg.quarter
    own_hist, fit_hist, flow_hist, trail_hist = [], [], [], []
    Rn = R.copy()
    pressure = np.zeros((T, N))
    level = np.zeros(N)                                     # the push accumulated so far (log price)
    decay = 0.5 ** (1 / cfg.half_life)
    fund_ret = np.zeros((T, cfg.funds))
    pending = np.zeros(N)                                   # this quarter's flow-induced trading, spread over its days
    for q in range(Q):
        t0 = q * cfg.quarter
        for f in range(cfg.funds):                          # replace delisted holdings and a share of the rest
            b = books[f]
            gone = ~listed[t0, b] | ((rng.random(len(b)) < cfg.turnover) if q > 0 else np.zeros(len(b), bool))
            if gone.any():
                keep = b[~gone]
                pool = listed[t0].copy()
                pool[keep] = False
                books[f] = np.r_[keep, _pick(pool, style, dirs[f], int(gone.sum()), cfg.tilt, rng)]
        W = np.zeros((cfg.funds, N))
        for f in range(cfg.funds):
            W[f, books[f]] = 1.0 / len(books[f])
        own = aum[:, None] * W
        own *= cfg.fund_share * listed[t0].sum() / own.sum()
        if q > 0:
            trailing = np.sum(fund_ret[max(0, t0 - cfg.chase * cfg.quarter):t0], axis=0)
            flow = flow_rule(trailing, cfg.beta, cfg.noise, rng)
            pending = fit(own, flow)
            trail_hist.append(trailing)
            flow_hist.append(flow)
            fit_hist.append(pending)
            own_hist.append(own)
        for t in range(t0, min(t0 + cfg.quarter, T)):
            step = cfg.impact * pending / cfg.quarter if q > 0 else np.zeros(N)
            new = level * decay + step
            dp = new - level
            level = new
            Rn[t] = np.where(listed[t], (1 + np.nan_to_num(R[t])) * np.exp(dp) - 1, np.nan)
            pressure[t] = level
            fund_ret[t] = W @ np.nan_to_num(np.log1p(Rn[t]))
    return {"R": Rn, "fit": np.array(fit_hist), "flow": np.array(flow_hist), "trailing": np.array(trail_hist),
            "own": np.array(own_hist), "quarters": np.arange(1, Q) * cfg.quarter, "pressure": pressure}
