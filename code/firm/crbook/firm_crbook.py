"""firm.crbook -- a central risk book: pooling desks' risk, netting, factor hedges and patient hedging (Book 9, ch. 25).

Several desks receive client flows in the same stocks every day (dollars, mostly independent across desks, with a
small common part). Desk by desk, each hedges its own flow in the stocks at the day's close; pooled, the central
book hedges only the net. The central book can also keep the net: it hedges the market factor at once with an index
future, which costs little, and trades out a fraction of the remaining stock positions each day, carrying residual
risk to save cost. Costs use Book 7's model (`firm_tcost.trade_cost`: half-spread plus square-root impact on each
name's daily volume); returns follow a three-factor model with idiosyncratic noise. NumPy only.

API (stable):
    CRBConfig(...)                             parameters (seed 181)
    simulate_desks(cfg)                        dict: flows (desks, days, names) in $, betas, factor loadings, returns
    hedge_cost(trade, cfg, u)                  cost in $ of a vector of stock trades ($) on universe u
    desk_by_desk(sim, cfg), pooled(sim, cfg)   daily hedging cost in $ when every flow is hedged at once
    central(sim, cfg, rate, futures)           daily stock and futures costs and the daily P&L of the risk carried
                                               when the book trades out `rate` of its stock positions a day
"""
from __future__ import annotations

import math
import pathlib
import sys
from dataclasses import dataclass

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tcost"))
from firm_tcost import trade_cost  # noqa: E402


@dataclass(frozen=True)
class CRBConfig:
    names: int = 100
    desks: int = 5
    days: int = 500
    seed: int = 181
    flow_sd: float = 5e5          # $ of client flow per desk, name and day
    common: float = 0.1           # share of flow variance common to all desks
    factor_vol: tuple = (0.010, 0.005, 0.005)   # daily vols: market and two styles
    idio_vol: float = 0.015       # daily idiosyncratic vol
    adv: tuple = (2e7, 2e8)       # range of names' daily traded value ($), log-uniform
    half_spread: float = 3e-4     # stocks' half-spread
    eta: float = 0.7              # impact coefficient (Book 7's fitted 0.71)
    futures_cost: float = 5e-5    # index future: cost per $ traded


def simulate_desks(cfg: CRBConfig | None = None) -> dict:
    cfg = cfg or CRBConfig()
    rng = np.random.default_rng(cfg.seed)
    N, D, T = cfg.names, cfg.desks, cfg.days
    beta = 1 + 0.3 * rng.standard_normal(N)
    load = np.column_stack([beta, rng.standard_normal((N, 2))])
    adv = np.exp(rng.uniform(math.log(cfg.adv[0]), math.log(cfg.adv[1]), N))
    sigma = np.sqrt((load ** 2) @ np.array(cfg.factor_vol) ** 2 + cfg.idio_vol ** 2)
    common = rng.standard_normal((1, T, N))
    flows = cfg.flow_sd * (math.sqrt(cfg.common) * common + math.sqrt(1 - cfg.common) * rng.standard_normal((D, T, N)))
    f = rng.standard_normal((T, 3)) * np.array(cfg.factor_vol)
    ret = f @ load.T + cfg.idio_vol * rng.standard_normal((T, N))
    return {"flows": flows, "beta": beta, "load": load, "adv": adv, "sigma": sigma, "ret": ret, "market": f[:, 0]}


def hedge_cost(trade: np.ndarray, sim: dict, cfg: CRBConfig) -> float:
    """$ cost of trading `trade` ($ per name) at the day's close with Book 7's model."""
    return trade_cost(trade, 1.0, sim["sigma"], sim["adv"], cfg.half_spread, cfg.eta)


def desk_by_desk(sim: dict, cfg: CRBConfig | None = None) -> np.ndarray:
    cfg = cfg or CRBConfig()
    fl = sim["flows"]
    return np.array([sum(hedge_cost(fl[d, t], sim, cfg) for d in range(fl.shape[0])) for t in range(fl.shape[1])])


def pooled(sim: dict, cfg: CRBConfig | None = None) -> np.ndarray:
    cfg = cfg or CRBConfig()
    net = sim["flows"].sum(axis=0)
    return np.array([hedge_cost(net[t], sim, cfg) for t in range(net.shape[0])])


def central(sim: dict, cfg: CRBConfig | None = None, rate: float = 1.0, futures: bool = True) -> dict:
    """Each day the net flow joins the inventory x ($ per name, the bank taking the clients' other side); the book sells
    `rate` of x in the stocks at the close and, with `futures`, holds an index future of minus the remaining
    beta-weighted exposure. The next day's P&L on what is carried: x . r + future x market return."""
    cfg = cfg or CRBConfig()
    net = -sim["flows"].sum(axis=0)
    T, N = net.shape
    x, h = np.zeros(N), 0.0
    stock_cost, fut_cost, pnl = np.zeros(T), np.zeros(T), np.zeros(T)
    for t in range(T):
        pnl[t] = x @ sim["ret"][t] + h * sim["market"][t]
        x = x + net[t]
        trade = -rate * x
        stock_cost[t] = hedge_cost(trade, sim, cfg)
        x = x + trade
        if futures:
            target = -(sim["beta"] @ x)
            fut_cost[t] = cfg.futures_cost * abs(target - h)
            h = target
    return {"stock_cost": stock_cost, "futures_cost": fut_cost, "pnl": pnl}
