"""firm.syscredit -- credit factors, stale bond prices and bond-ETF arbitrage (build of Book 9, chapter 19).

A synthetic panel of corporate bonds, daily: each bond's excess return over Treasuries is minus its spread duration
times its spread change plus its spread as carry. Spreads move with a market credit factor, an issuer trend that
persists for months (momentum) and an issuer gap from fair value that reverts over a year (value); expected excess
returns rise with spread duration less than one for one, so short, safe bonds earn more per unit of risk (low
risk). Bonds trade on a share of days only, so their observed prices are stale. A bond ETF holds the panel; its NAV
is computed from the stale prices, its market price follows the bonds' true value, and in a planted stress, when
investors sell ETF shares to raise cash, the price also falls below true value before recovering. An authorised
participant buys ETF shares at a discount, redeems them for bonds and sells the bonds at their true value less a
cost that widens in the stress. NumPy only.

API (stable):
    SysCreditConfig(...)                       parameters (seed 157)
    simulate_bonds(cfg)                        dict: returns (T, N), spreads, durations, true and stale values, gap,
                                               trend, NAV (T,), ETF price (T,), true basket value (T,), stress
    factor_book(sim, cfg, name)                (T,) daily return of a long-short factor book (value, momentum, lowrisk)
    ap_arbitrage(sim, cfg)                     per-day profit of redeeming ETF shares bought at a discount (bp)
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

YEAR = 252


@dataclass(frozen=True)
class SysCreditConfig:
    days: int = 8 * YEAR
    bonds: int = 300
    seed: int = 157
    market_vol: float = 40.0      # annual vol of the market spread factor (bp)
    trend_sd: float = 60.0        # annual sd of issuers' spread drifts (bp a year), persistent ...
    trend_hl: float = 126.0       # ... with this half-life (days)
    gap_sd: float = 55.0          # stationary sd of the gap from fair spread (bp) ...
    gap_hl: float = 250.0         # ... reverting with this half-life
    idio_vol: float = 150.0       # annual vol of other issuer spread noise (bp)
    premium_per_sqrt_dur: float = 0.012   # expected excess return: this times sqrt(duration), a year
    trade_prob: float = 0.25      # share of days a bond trades
    stress_start: int = 6 * YEAR
    stress_days: int = 15
    stress_move: float = 150.0    # market spreads widen this much over the stress (bp) ...
    stress_back: int = 40         # ... and half of it returns over this many days
    etf_dislocation: float = 0.03   # extra fall of the ETF price below true value at the stress's depth
    cost_normal: float = 0.003    # the AP's cost of selling the basket, as a share of value
    cost_stress: float = 0.015


def simulate_bonds(cfg: SysCreditConfig | None = None) -> dict:
    cfg = cfg or SysCreditConfig()
    rng = np.random.default_rng(cfg.seed)
    T, N = cfg.days, cfg.bonds
    dur = rng.uniform(1.0, 12.0, N)
    base = 60 + 12 * dur + 40 * rng.standard_normal(N).clip(-1.2, 3)
    dt = 1 / YEAR
    mkt = cfg.market_vol * math.sqrt(dt) * rng.standard_normal(T)
    a, b = cfg.stress_start, cfg.stress_start + cfg.stress_days
    mkt[a:b] += cfg.stress_move / cfg.stress_days
    mkt[b:b + cfg.stress_back] -= 0.5 * cfg.stress_move / cfg.stress_back
    pt, pg = 0.5 ** (1 / cfg.trend_hl), 0.5 ** (1 / cfg.gap_hl)
    trend, gap = np.empty((T, N)), np.empty((T, N))
    trend[0] = cfg.trend_sd * rng.standard_normal(N)
    gap[0] = cfg.gap_sd * rng.standard_normal(N)
    for t in range(1, T):
        trend[t] = pt * trend[t - 1] + cfg.trend_sd * math.sqrt(1 - pt * pt) * rng.standard_normal(N)
        gap[t] = pg * gap[t - 1] + cfg.gap_sd * math.sqrt(1 - pg * pg) * rng.standard_normal(N)
    dspread = mkt[:, None] + trend * dt + np.vstack([np.zeros(N), np.diff(gap, axis=0)]) \
        + cfg.idio_vol * math.sqrt(dt) * rng.standard_normal((T, N))
    spread = base + np.cumsum(dspread, axis=0) + gap
    premium = cfg.premium_per_sqrt_dur * np.sqrt(dur) * dt
    ret = -dur * dspread / 1e4 + premium                               # excess return over Treasuries
    true_v = np.exp(np.cumsum(np.log1p(ret), axis=0))
    trades = rng.random((T, N)) < cfg.trade_prob
    stale = true_v.copy()
    for t in range(1, T):
        stale[t] = np.where(trades[t], true_v[t], stale[t - 1])
    basket = true_v.mean(axis=1)
    nav = stale.mean(axis=1)
    disl = np.zeros(T)
    down, up = np.linspace(0, cfg.etf_dislocation, b - a), np.linspace(cfg.etf_dislocation, 0, cfg.stress_back)
    disl[a:b] = down[:max(0, min(b, T) - a)]
    disl[b:b + cfg.stress_back] = up[:max(0, min(b + cfg.stress_back, T) - b)]
    price = basket * (1 - disl) * np.exp(0.0005 * rng.standard_normal(T))
    return {"ret": ret, "spread": spread, "dur": dur, "gap": gap, "trend": trend, "true": true_v, "stale": stale,
            "nav": nav, "price": price, "basket": basket, "stress": (a, b)}


def factor_book(sim: dict, cfg: SysCreditConfig | None = None, name: str = "value", every: int = 21) -> np.ndarray:
    """Long the top fifth and short the bottom fifth of bonds by the signal, duration-neutral within each side by
    weighting with 1 / duration, rebalanced monthly; value: spread over the fitted spread-duration line less its
    three-month change, so that value is not recent losers; momentum:
    minus the six-month spread change; low risk: minus duration (long short bonds, short long ones, equal risk)."""
    cfg = cfg or SysCreditConfig()
    ret, dur, sp = sim["ret"], sim["dur"], sim["spread"]
    T, N = ret.shape
    out = np.zeros(T)
    w = np.zeros(N)
    for t in range(127, T):
        if (t - 127) % every == 0:
            if name == "value":
                fit = np.polyval(np.polyfit(dur, sp[t - 1], 1), dur)
                sig = sp[t - 1] - fit - (sp[t - 1] - sp[t - 64])              # cheap, less its last three months' move
            elif name == "momentum":
                sig = -(sp[t - 1] - sp[t - 127])
            else:
                sig = -dur
            q = np.quantile(sig, [0.2, 0.8])
            long, short = sig >= q[1], sig <= q[0]
            w = np.zeros(N)
            w[long] = (1 / dur[long]) / (1 / dur[long]).sum()
            w[short] = -(1 / dur[short]) / (1 / dur[short]).sum()
            if name == "lowrisk":                                       # equal risk: scale each side by duration
                w[long] = 1 / long.sum() / dur[long].mean()
                w[short] = -1 / short.sum() / dur[short].mean()
        out[t] = w @ ret[t]
    return out


def ap_arbitrage(sim: dict, cfg: SysCreditConfig | None = None) -> dict:
    """Each day the ETF trades below the basket's true value by more than the AP's cost, the AP buys shares and
    redeems them, selling the bonds at true value less the cost: profit in bp of the redeemed value."""
    cfg = cfg or SysCreditConfig()
    a, b = sim["stress"]
    cost = np.full(len(sim["price"]), cfg.cost_normal)
    cost[a:b + cfg.stress_back] = cfg.cost_stress
    edge = sim["basket"] / sim["price"] - 1 - cost
    profit = np.where(edge > 0, edge, 0.0) * 1e4
    discount = (sim["price"] / sim["nav"] - 1) * 1e4
    return {"profit": profit, "discount": discount, "cost": cost}
