"""firm.optarb -- options arbitrage at speed: parity, boxes, jelly rolls, the dividend play (One Quant Book 11, ch. 20).

Built on firm.parity (Book 1: conversion and reversal edges on European parity), firm.american (Book 5: the exercise
decision before an ex-dividend date) and firm.optmm (Book 5: the dividend play's assignment arithmetic).

API (stable):
    box_rate(k1, k2, price, years)                  the rate implied by a box: price = (k2 - k1) e^{-rT}
    box_edge(box_ask, box_bid, k1, k2, years, rate) (lend through the box: buy it below its value at `rate`;
                                                     borrow: sell it above), dollars per box
    jelly_roll(c1, p1, c2, p2, k, t1, t2, rate)     the carry (r - q) implied between two expiries by the synthetic
                                                     forwards C - P at the same strike
    Listings(n_venues, strikes, seed, ...)          call and put quotes for one expiry on several venues, each venue's
                                                     mid off the fair value by its own noise
    scan(listings, spot_bid, spot_ask, fee, lag_rho, seed)
                                                    conversions and reversals across venues (best bid and ask of each
                                                     option on any venue) net of fees, and the share still profitable
                                                     after one refresh of the quotes (noise correlation lag_rho)
    dividend_curve(fails, public, gain, trade_fee, exercise_fee)
                                                    the dividend play's best size and net profit per contract of public
                                                     open interest, for each share of holders who fail to exercise
"""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

FIRM = pathlib.Path(__file__).resolve().parents[1]
for comp in ("parity", "american", "optmm"):
    sys.path.insert(0, str(FIRM / comp))
import firm_american as fam  # noqa: E402
import firm_optmm as om  # noqa: E402
import firm_parity as fp  # noqa: E402


def box_rate(k1: float, k2: float, price: float, years: float) -> float:
    return -math.log(price / (k2 - k1)) / years


def box_edge(box_ask: float, box_bid: float, k1: float, k2: float, years: float, rate: float) -> tuple[float, float]:
    """(lend edge, borrow edge): buying the box at its ask earns (k2 - k1) at expiry, worth PV at `rate`."""
    pv = (k2 - k1) * math.exp(-rate * years)
    return pv - box_ask, box_bid - pv


def jelly_roll(c1: float, p1: float, c2: float, p2: float, k: float, t1: float, t2: float, rate: float) -> float:
    """C - P = e^{-rT}(F - K) at each expiry; the two forwards give the carry r - q between t1 and t2."""
    f1 = fp.implied_forward(c1, p1, k, t1, rate)
    f2 = fp.implied_forward(c2, p2, k, t2, rate)
    return math.log(f2 / f1) / (t2 - t1)


class Listings:
    """One expiry, `strikes`, on `n_venues`: fair values from firm.parity's Black-76 price on forward F; each venue
    quotes fair -+ half_spread shifted by its own noise (standard deviation `noise`), for calls and puts apart."""

    def __init__(self, n_venues: int = 3, strikes=tuple(range(80, 121, 5)), seed: int = 0, spot: float = 100.0,
                 rate: float = 0.04, div_pv: float = 0.5, years: float = 0.25, vol: float = 0.25,
                 half_spread: float = 0.05, noise: float = 0.03):
        self.rng = np.random.default_rng(seed)
        self.n, self.strikes, self.spot = n_venues, strikes, spot
        self.rate, self.div_pv, self.years = rate, div_pv, years
        self.forward = (spot - div_pv) * math.exp(rate * years)
        self.fair = {(k, r): fp.price(self.forward, k, years, rate, vol, r) for k in strikes for r in ("C", "P")}
        self.hs, self.noise_sd = half_spread, noise
        self.noise = self.rng.normal(0.0, noise, (n_venues, len(strikes), 2))

    def refresh(self, rho: float) -> None:
        self.noise = rho * self.noise + math.sqrt(1 - rho * rho) * self.rng.normal(0.0, self.noise_sd, self.noise.shape)

    def best(self, k, right) -> tuple[float, float]:
        i, j = self.strikes.index(k), 0 if right == "C" else 1
        mids = self.fair[(k, right)] + self.noise[:, i, j]
        return float(np.max(mids - self.hs)), float(np.min(mids + self.hs))


def scan(ls: Listings, spot_bid: float = 99.99, spot_ask: float = 100.01, fee: float = 0.01, lag_rho: float = 0.5,
         rounds: int = 2000) -> dict:
    """Over `rounds` independent snapshots: conversions (sell call bid, buy put ask, buy share) and reversals across
    venues net of `fee` a leg (three legs); for each found, refresh once and test it again."""
    found = survived = 0
    edges = []
    for _ in range(rounds):
        ls.refresh(0.0)
        hits = []
        for k in ls.strikes:
            cb, ca = ls.best(k, "C")
            pb, pa = ls.best(k, "P")
            conv = fp.conversion_edge(cb, pa, spot_ask, k, ls.years, ls.rate, ls.div_pv) - 3 * fee
            rev = fp.reversal_edge(ca, pb, spot_bid, k, ls.years, ls.rate, ls.div_pv) - 3 * fee
            if conv > 0:
                hits.append((k, "conv"))
                edges.append(conv)
            if rev > 0:
                hits.append((k, "rev"))
                edges.append(rev)
        found += len(hits)
        if hits:
            ls.refresh(lag_rho)
            for k, kind in hits:
                cb, ca = ls.best(k, "C")
                pb, pa = ls.best(k, "P")
                e = (fp.conversion_edge(cb, pa, spot_ask, k, ls.years, ls.rate, ls.div_pv) if kind == "conv"
                     else fp.reversal_edge(ca, pb, spot_bid, k, ls.years, ls.rate, ls.div_pv)) - 3 * fee
                survived += e > 0
    return {"per_snapshot": found / rounds, "mean_edge": float(np.mean(edges)) if edges else 0.0,
            "survive": survived / found if found else 0.0}


def dividend_curve(fails, public: float = 10000.0, gain: float = 0.30, trade_fee: float = 0.002,
                   exercise_fee: float = 0.001) -> dict:
    """firm.optmm.best_play per share of holders failing to exercise; gain and fees in dollars per share (x100 a
    contract). Returns q (contracts traded by each of the two market makers) and net dollars per public contract."""
    out = {}
    for f in fails:
        q, r = om.best_play(public, f, gain * 100, trade_fee * 100, exercise_fee * 100)
        out[f] = {"q": q, "net": r["net"], "per_public": r["net"] / public, "captured": r["captured"]}
    return out


def exercise_threshold(spot: float = 60.0, strike: float = 40.0, t_left: float = 30 / 365, r: float = 0.04,
                       vol: float = 0.25) -> float:
    """The smallest dividend that makes early exercise optimal (firm.american.dividend_threshold)."""
    return fam.dividend_threshold(spot, strike, t_left, r, vol)
