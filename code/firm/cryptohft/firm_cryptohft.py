"""firm.cryptohft -- cross-exchange market making in crypto (One Quant Book 11, chapter 24).

Built on Book 3's firm.perp (funding payments), firm.ratelimit (the request budget) and firm.mmprogram (uptime).
One coin, two venues, one-second steps around the clock. The hedge venue's spot book shows the fair price first; the
market maker quotes the quote venue's perpetual around it, but can only move its quotes as often as its request
budget allows. Every fill on the perpetual is hedged at once by taking on the hedge venue. Funding is paid on the
perpetual position every eight hours. A planted liquidation cascade pushes the perpetual below spot and sends forced
sells into the maker's bid. Amounts in dollars; prices in dollars; spreads and fees in basis points.

API (stable):
    Week(seed, days, sigma_day, cascade_day, ...)      the fair price path, client flow, arbitrage opportunities,
                                                       funding rates and the cascade's basis
    run(week, half_bp, requote_per_s, inv_limit, absorb, ...)
                                                       P&L by component (spread, adverse, hedge, funding, cascade),
                                                       uptime, requests used
    budget_from(governor, instruments)                 requotes a second allowed by a firm.ratelimit governor
"""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

FIRM = pathlib.Path(__file__).resolve().parents[1]
for comp in ("perp", "ratelimit", "mmprogram"):
    sys.path.insert(0, str(FIRM / comp))
import firm_mmprogram as mp  # noqa: E402
import firm_perp as fperp  # noqa: E402
import firm_ratelimit as rl  # noqa: E402

DAY = 86400


class Week:
    """`days` of one-second steps. Fair price: geometric random walk of daily volatility sigma_day from 60,000.
    Client orders on the quote venue: Poisson, `clients_per_s` a second, $`clip` each, buys with probability
    `buy_share`. Funding every eight hours at 1 bp plus N(0, 1 bp). Cascade: on `cascade_day` at noon, the
    perpetual's basis to spot falls to -`cascade_depth_bp` over five minutes and recovers exponentially (ten-minute
    time constant) over the next 55, while forced
    sells of $`forced_per_s` a second arrive for five minutes."""

    def __init__(self, seed: int = 0, days: int = 7, sigma_day: float = 0.03, clients_per_s: float = 0.5,
                 clip: float = 10000.0, buy_share: float = 0.52, cascade_day: int | None = 3,
                 cascade_depth_bp: float = 80.0, forced_per_s: float = 50000.0):
        rng = np.random.default_rng(seed)
        n = days * DAY
        self.n, self.days, self.clip = n, days, clip
        self.fair = 60000.0 * np.exp(np.cumsum(rng.standard_normal(n) * sigma_day / math.sqrt(DAY)))
        self.clients = rng.poisson(clients_per_s, n)
        self.buy = rng.random(n) < buy_share
        self.funding = 1e-4 + 1e-4 * rng.standard_normal(days * 3)
        self.basis = np.zeros(n)
        self.forced = np.zeros(n)
        if cascade_day is not None:
            t0 = cascade_day * DAY + DAY // 2
            down = np.linspace(0.0, 1.0, 300)
            up = np.exp(-np.arange(3300) / 600.0)
            self.basis[t0:t0 + 300] = -cascade_depth_bp * 1e-4 * down
            self.basis[t0 + 300:t0 + 3600] = -cascade_depth_bp * 1e-4 * up
            self.forced[t0:t0 + 300] = forced_per_s
            self.t0 = t0
        self.hedge_noise = rng.standard_normal(n)


def run(w: Week, half_bp: float = 2.0, requote_per_s: float = 5.0, inv_limit: float = 200000.0, absorb: bool = True,
        absorb_limit: float = 5000000.0, absorb_from_bp: float = 0.0, record: tuple[int, int] | None = None,
        taker_bp: float = 1.0, maker_bp: float = -0.5, hedge_half_bp: float = 0.5, hedge_latency_s: float = 0.02,
        sigma_day: float = 0.03, arb_threshold_bp: float = 1.0, arb_clip: float = 20000.0,
        max_spread_bp: float = 10.0) -> dict:
    """Quote the perpetual at quote_mid -+ half_bp, where quote_mid is the fair price (plus the perpetual's basis) as
    of the last requote; requote every 1/requote_per_s seconds (two requests: cancel and new). Client orders fill at
    the quote; an arbitrageur takes $arb_clip whenever a quote is stale beyond the half-spread plus the arbitrageur's
    threshold. Every fill is hedged on spot at the fair price plus hedge_half_bp and a latency slippage. Positions are
    marked to the fair price; the perpetual's basis P&L is booked in 'cascade'. While forced sells arrive the bid is
    pulled, unless `absorb` and the perpetual trades at least absorb_from_bp below spot: then the bid's inventory
    limit is absorb_limit (liquidation absorption)."""
    n = w.n
    period = max(int(round(1.0 / requote_per_s)), 1)          # seconds between requotes (at most one a second)
    perp = 0.0          # perpetual position, coins (+ long)
    parts = {k: 0.0 for k in ("spread", "adverse", "hedge", "fees", "funding", "cascade")}
    quote_mid = w.fair[0]
    requests = 0
    on = up_ok = 0
    slip_sd = sigma_day * math.sqrt(hedge_latency_s / DAY)
    path = []
    for t in range(n):
        f = w.fair[t]
        perp_mid = f * (1.0 + w.basis[t])
        if t % period == 0:
            quote_mid = perp_mid
            requests += 2
        hs = half_bp * 1e-4 * quote_mid
        bid, ask = quote_mid - hs, quote_mid + hs
        deep = w.basis[t] <= -absorb_from_bp * 1e-4
        lim_bid = absorb_limit if (absorb and w.basis[t] < 0.0 and deep) else inv_limit
        quoting_bid = (perp * f < lim_bid) and (w.forced[t] == 0.0 or (absorb and deep))
        quoting_ask = perp * f > -inv_limit
        on += 1
        up_ok += quoting_bid and quoting_ask and 2 * hs / quote_mid * 1e4 <= max_spread_bp
        fills = []                                   # (coins, price): + the maker buys
        for _ in range(int(w.clients[t])):
            if w.buy[t] and quoting_ask:
                fills.append((-w.clip / ask, ask))
            elif (not w.buy[t]) and quoting_bid:
                fills.append((w.clip / bid, bid))
        if w.forced[t] > 0.0 and quoting_bid:
            fills.append((w.forced[t] / bid, bid))
        thr = arb_threshold_bp * 1e-4 * perp_mid
        if ask < perp_mid - thr and quoting_ask:
            fills.append((-arb_clip / ask, ask))
        elif bid > perp_mid + thr and quoting_bid:
            fills.append((arb_clip / bid, bid))
        for coins, px in fills:
            parts["spread"] += abs(coins) * hs
            parts["adverse"] += coins * (perp_mid - px) - abs(coins) * hs     # value vs the perp mid, net of spread
            parts["fees"] -= abs(coins) * px * maker_bp * 1e-4
            # hedge on spot at once: sell spot if the maker bought the perp
            slip = abs(coins) * f * (hedge_half_bp * 1e-4 + slip_sd * abs(w.hedge_noise[t]))
            parts["hedge"] -= slip + abs(coins) * f * taker_bp * 1e-4
            perp += coins
        if record is not None and record[0] <= t < record[1]:
            path.append((t, w.basis[t], perp * f))
        # basis P&L of the hedged book (long perp, short spot): the perp's move relative to spot
        if t + 1 < n:
            parts["cascade"] += perp * w.fair[t + 1] * (w.basis[t + 1] - w.basis[t])
        if (t + 1) % (8 * 3600) == 0:
            i = (t + 1) // (8 * 3600) - 1
            if i < len(w.funding):
                parts["funding"] -= fperp.funding_payment(perp, perp_mid, w.funding[i])   # paid by the holder
    total = sum(parts.values())
    return {**parts, "total": total, "uptime": up_ok / on, "requests": requests, "end_position_usd": perp * w.fair[-1],
            "path": path}


def budget_from(gov: rl.Governor, instruments: int = 1) -> float:
    """Requotes a second (two orders each: cancel and replace) inside the governor's tightest order rule."""
    return mp.requote_budget(gov, instruments) / 2.0
