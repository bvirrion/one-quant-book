"""firm.mergerarb -- deal spreads and a portfolio of deals (build of One Quant Book 8, chapter 11).

A target trades between what it will be worth if the deal completes (the offer) and if it breaks (a break price, which
moves with the market). With a risk-neutral break probability q the price is the discounted mix, so the spread
measures q; the arbitrageur earns the difference between q and the true, lower break probability, and loses when deals
break, which they do more often when the market falls. Stock deals pay a ratio of the acquirer's shares, hedged by
shorting them; a collar fixes the ratio inside a band of acquirer prices and the value outside it. NumPy only.

API (stable):
    spread(price, offer)                         offer / price - 1
    annualised(spread, days)                     (1 + spread) ** (252 / days) - 1
    implied_probability(price, offer, break_price, rate, days)
                                                 completion probability implied by the price
    collar_value(acquirer, ratio, low, high)     consideration per target share under a fixed-ratio collar
    collar_hedge(acquirer, ratio, low, high)     acquirer shares to short per target share (the collar's delta)
    DealConfig(...)                              deal generation parameters
    simulate_deals(mkt, cfg, rng)                list of deals with their daily target prices and outcome
    portfolio(deals, T)                          equal-weighted daily return of the active deals, and their count
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


def spread(price, offer):
    return np.asarray(offer, float) / np.asarray(price, float) - 1


def annualised(s, days):
    return (1 + np.asarray(s, float)) ** (252 / np.asarray(days, float)) - 1


def implied_probability(price, offer, break_price, rate: float = 0.0, days: float = 0.0):
    disc = math.exp(-rate * days / 252)
    return (np.asarray(price, float) - disc * np.asarray(break_price, float)) / \
        (disc * (np.asarray(offer, float) - np.asarray(break_price, float)))


def collar_value(acquirer, ratio: float, low: float, high: float):
    return ratio * np.clip(np.asarray(acquirer, float), low, high)


def collar_hedge(acquirer, ratio: float, low: float, high: float):
    a = np.asarray(acquirer, float)
    return np.where((a > low) & (a < high), ratio, 0.0)


@dataclass(frozen=True)
class DealConfig:
    per_year: float = 50.0             # announcements a year
    premium: tuple = (0.2, 0.4)        # offer premium over the undisturbed price, uniform
    days_median: float = 110.0         # trading days to completion, lognormal
    days_disp: float = 0.4
    q: float = 0.12                    # risk-neutral break probability priced into the spread
    base_break: float = 0.06           # true break probability in a flat market
    crash_break: float = 1.5           # extra break probability per unit of market fall over the deal
    beta: float = 1.0                  # beta of the break price to the market
    idio: float = 0.02                 # daily specific volatility of the break price
    rate: float = 0.04


def simulate_deals(mkt, cfg: DealConfig | None = None, rng=None):
    cfg = cfg or DealConfig()
    rng = rng or np.random.default_rng(11)
    mkt = np.asarray(mkt, float)
    T = len(mkt)
    lm = np.concatenate([[0.0], np.cumsum(np.log1p(mkt))])
    deals = []
    for t0 in np.flatnonzero(rng.random(T) < cfg.per_year / 252):
        n = int(np.clip(round(cfg.days_median * math.exp(cfg.days_disp * rng.standard_normal())), 20, 400))
        if t0 + n >= T:
            continue
        prem = rng.uniform(*cfg.premium)
        offer = 1.0 + prem                                       # the undisturbed price is 1
        walk = np.cumsum(cfg.idio * rng.standard_normal(n + 1))
        brk = np.exp(cfg.beta * (lm[t0:t0 + n + 1] - lm[t0]) + walk)
        tau = n - np.arange(n + 1)
        disc = np.exp(-cfg.rate * tau / 252)
        price = disc * ((1 - cfg.q) * offer + cfg.q * brk)
        fall = max(-(lm[t0 + n] - lm[t0]), 0.0)
        broke = rng.random() < min(cfg.base_break + cfg.crash_break * fall, 0.95)
        price[-1] = brk[-1] if broke else offer
        deals.append({"start": int(t0), "end": int(t0 + n), "offer": offer, "price": price, "broke": bool(broke),
                      "implied": float(implied_probability(price[0], offer, brk[0], cfg.rate, n))})
    return deals


def portfolio(deals, T: int):
    """Equal weights across the deals held on each day (entered at the announcement's close, held to resolution)."""
    s, c = np.zeros(T), np.zeros(T)
    for d in deals:
        r = d["price"][1:] / d["price"][:-1] - 1
        s[d["start"] + 1:d["end"] + 1] += r
        c[d["start"] + 1:d["end"] + 1] += 1
    return np.where(c > 0, s / np.maximum(c, 1), 0.0), c
