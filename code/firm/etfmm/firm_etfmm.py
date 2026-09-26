"""firm.etfmm -- quoting an ETF from a pricing basket (One Quant Book 11, chapter 12).

A synthetic bond ETF: n bonds with true values driven by one factor (plus idiosyncratic moves), each printing a
trade only now and then; a liquid proxy (a future on the factor) prints every minute. The official NAV and the
intraday indicative value use each bond's last print; a pricing basket moves each stale print by the proxy's move
since, times the bond's beta. A market maker quotes the ETF around either value, is picked off by arbitrageurs who
know the true value, hedges with the proxy, and flattens at the close by redeeming or creating in kind.

API (stable):
    closed_fair(last, beta, proxy_move, fx_move=0.0)  a stale component: last * (1 + beta * move) * (1 + fx)
    pricing_basket(last, t_last, beta, G, t)          sum_i w_i last_i (1 + beta_i (G_t - G_{t_last,i})), equal weights
    creation_decision(price, value, unit, fee, cost_bp)
                                                      'create' | 'redeem' | 'none', and the edge per unit in dollars
    Market(seed, days, freeze, ...)                   minute paths: true value, proxy, prints, NAV, pricing basket
    run_mm(market, estimator, hedge, flatten, ...) -> dict
                                                      daily P&L and its parts, and the quote path
Units: ETF price about 100 a share, trades of `lot` shares, creation unit `unit` shares, costs in basis points.
"""
from __future__ import annotations

import math

import numpy as np

MINUTES = 390


def closed_fair(last: float, beta: float, proxy_move: float, fx_move: float = 0.0) -> float:
    """A component whose market is closed: its last price moved by beta times the proxy's return since, in the
    ETF's currency (fx_move: the currency's return against the ETF's)."""
    return last * (1.0 + beta * proxy_move) * (1.0 + fx_move)


def pricing_basket(last, t_last, beta, G, t: int) -> float:
    last, t_last, beta = np.asarray(last, float), np.asarray(t_last, int), np.asarray(beta, float)
    return float(np.mean(last * (1.0 + beta * (G[t] - G[t_last]))))


def creation_decision(price: float, value: float, unit: int, fee: float, cost_bp: float) -> tuple[str, float]:
    """Create when the ETF trades above the basket's value by more than the fee and the cost of buying the basket;
    redeem when below by more than the fee and the cost of selling it. Edge per unit in dollars (0 if none)."""
    gap = (price - value) * unit
    cost = fee + cost_bp * 1e-4 * value * unit
    if gap > cost:
        return "create", gap - cost
    if -gap > cost:
        return "redeem", -gap - cost
    return "none", 0.0


class Market:
    """Minute paths over `days` sessions. The factor has daily volatility `sf` (x `stress_vol` and a drift of
    `stress_drift` in total during the freeze days); the proxy is the factor plus a basis that wanders as a random walk
    of daily volatility `basis`; bonds print with probability `p_print` a minute (divided by
    `freeze_print` during the freeze) at their true value plus a half-spread of `hb` (x `stress_hb`) of random sign."""

    def __init__(self, seed: int = 0, days: int = 60, n: int = 100, freeze: tuple[int, int] = (40, 45),
                 sf: float = 0.004, se: float = 0.003, stress_vol: float = 4.0, stress_drift: float = -0.05,
                 p_print: float = 1 / 120, freeze_print: float = 10.0, hb: float = 0.001, stress_hb: float = 6.0,
                 basis: float = 0.001):
        rng = np.random.default_rng(seed)
        m = days * MINUTES
        self.days, self.n, self.m, self.freeze = days, n, m, freeze
        day = np.arange(m) // MINUTES
        self.stress = (day >= freeze[0]) & (day < freeze[1])
        vol = np.where(self.stress, sf * stress_vol, sf) / math.sqrt(MINUTES)
        drift = np.where(self.stress, stress_drift / ((freeze[1] - freeze[0]) * MINUTES), 0.0)
        self.F = np.cumsum(rng.standard_normal(m) * vol + drift)
        self.beta = rng.uniform(0.6, 1.4, n)
        E = np.cumsum(rng.standard_normal((m, n)) * se / math.sqrt(MINUTES), axis=0)
        self.V = 100.0 * (1.0 + self.F[:, None] * self.beta + E)
        self.true = self.V.mean(axis=1)
        self.G = self.F + np.cumsum(rng.standard_normal(m) * basis / math.sqrt(MINUTES))
        p = np.where(self.stress, p_print / freeze_print, p_print)
        prints = rng.random((m, n)) < p[:, None]
        prints[0] = True
        self.hb = np.where(self.stress, hb * stress_hb, hb)
        px = self.V * (1.0 + self.hb[:, None] * rng.choice([-1.0, 1.0], (m, n)))
        idx = np.where(prints, np.arange(m)[:, None], 0)
        self.t_last = np.maximum.accumulate(idx, axis=0)
        self.last = np.take_along_axis(px, self.t_last, axis=0)
        self.nav = self.last.mean(axis=1)
        self.basket = np.mean(self.last * (1.0 + self.beta * (self.G[:, None] - self.G[self.t_last])), axis=1)
        self.age = (np.arange(m)[:, None] - self.t_last).mean(axis=1)


def run_mm(mk: Market, estimator: str = "basket", hedge: str = "future", flatten: str = "redeem", seed: int = 1,
           lot: int = 10000, unit: int = 100000, h_bp: float = 5.0, skew_bp: float = 2.0, lam: float = 0.5,
           sell_stress: float = 3.0, p_arb: float = 0.2, arb_bp: float = 5.0, c_fut_bp: float = 0.5,
           fee: float = 1000.0, elastic_bp: float = 5.0, panic_elastic_bp: float = 50.0, limit: int = 40,
           limit_bp: float = 10.0) -> dict:
    """Quote the ETF each minute at fair -+ half-spread, skewed by `skew_bp` per lot of inventory; clients buy and sell
    `lam` lots a minute each when the quote is `h_bp` from the true value, more when it is closer and fewer when it is
    farther (e-fold per `elastic_bp`); in the freeze, panic sellers add (sell_stress - 1) times the normal rate and
    care ten times less about the price (e-fold per `panic_elastic_bp`); past `limit` lots of inventory the quotes
    skew a further `limit_bp` per lot (the balance sheet is full); an arbitrageur arrives with probability
    `p_arb` and trades two lots against any quote `arb_bp` or more through the true value. 'future' hedges the
    inventory's beta in the proxy each minute; 'redeem' flattens whole creation units in kind at the close, paying
    the fee and the bonds' half-spread. P&L is marked to the true value."""
    rng = np.random.default_rng(seed)
    fair = mk.basket if estimator == "basket" else mk.nav
    bbar = float(mk.beta.mean())
    inv, cash, H, fut = 0.0, 0.0, 0.0, 0.0
    parts = {k: np.zeros(mk.days) for k in ("spread", "arb", "hedge", "flatten", "inventory", "total")}
    mid = np.empty(mk.m)
    prev_val = 0.0
    for t in range(mk.m):
        d = t // MINUTES
        T = mk.true[t]
        if t:
            dh = -H * 100.0 * (mk.G[t] - mk.G[t - 1])
            fut += dh
            parts["inventory"][d] += inv * (T - mk.true[t - 1]) + dh
        h = h_bp * 1e-4 * fair[t] * (3.0 if mk.stress[t] else 1.0)
        x = inv / lot
        over = math.copysign(max(abs(x) - limit, 0.0), x)
        c = fair[t] * (1.0 - 1e-4 * (skew_bp * x + limit_bp * over))
        mid[t] = c
        bid, ask = c - h, c + h
        hb0 = h_bp * 1e-4 * T
        eb = elastic_bp * 1e-4 * T
        nb = rng.poisson(lam * math.exp(min(-((ask - T) - hb0) / eb, 3.0)))
        ns = rng.poisson(lam * math.exp(min(-((T - bid) - hb0) / eb, 3.0)))
        if mk.stress[t]:
            pe = panic_elastic_bp * 1e-4 * T
            ns += rng.poisson(lam * (sell_stress - 1.0) * math.exp(min(-((T - bid) - hb0) / pe, 3.0)))
        for _ in range(nb):           # clients buy at the ask
            cash += ask * lot
            inv -= lot
            parts["spread"][d] += (ask - T) * lot
        for _ in range(ns):
            cash -= bid * lot
            inv += lot
            parts["spread"][d] += (T - bid) * lot
        if rng.random() < p_arb:
            if bid > T * (1 + arb_bp * 1e-4):
                cash -= bid * 2 * lot
                inv += 2 * lot
                parts["arb"][d] += (T - bid) * 2 * lot
            elif ask < T * (1 - arb_bp * 1e-4):
                cash += ask * 2 * lot
                inv -= 2 * lot
                parts["arb"][d] += (ask - T) * 2 * lot
        if hedge == "future":
            target = bbar * inv * T / 100.0        # proxy notional in units of 100 dollars
            if abs(target - H) * 100.0 >= lot * T:
                cost = c_fut_bp * 1e-4 * abs(target - H) * 100.0
                parts["hedge"][d] -= cost
                cash -= cost
                H = target
        if flatten == "redeem" and (t + 1) % MINUTES == 0:
            k = int(round(inv / unit))
            if k:
                cost = abs(k) * (fee + mk.hb[t] * unit * T)
                parts["flatten"][d] -= cost
                cash += k * unit * T - cost
                inv -= k * unit
                if hedge == "future":
                    target = bbar * inv * T / 100.0
                    parts["hedge"][d] -= c_fut_bp * 1e-4 * abs(target - H) * 100.0
                    cash -= c_fut_bp * 1e-4 * abs(target - H) * 100.0
                    H = target
        if (t + 1) % MINUTES == 0:
            val = cash + inv * T + fut
            parts["total"][d] = val - prev_val
            prev_val = val
    parts["mid"] = mid
    return parts
