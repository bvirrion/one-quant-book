"""firm.xexec -- execution adapters for markets that are not an equity order book: futures with implied spreads, FX
aggregated over last-look streams, bonds by request for quote, crypto across an exchange and an AMM pool (build of One
Quant Book 10, chapter 21; on Books 1-3's firm.match, firm.lastlook, firm.rfq, firm.amm and firm.ratelimit).

Costs in basis points of notional, positive when paid, against the mid at the start.

API (stable):
    Market(name, half_spread_bp, sigma_day_bp, adv, y=0.7)   a market's spread, daily volatility and daily volume
    sqrt_impact_bp(market, notional)          y sigma sqrt(notional / adv): the parent order's impact (chapter 11)
    children(notional, scheduler, n)          child notionals from a firm.acexec scheduler over n equal intervals
    roll(front, back, spread, lots, tick)     rolling a long position (sell front, buy back): {'legs': cost in price
                                              units a lot, 'spread_book': the direct spread book then legging,
                                              'implied': the direct and implied spread book (firm.match.best_of) then
                                              legging}; books are firm.match Quotes, each level backed by one more
                                              level a tick worse of the same size
    LP(name, half_bp, hold_ms, threshold_bp, policy)   a liquidity provider's stream; policy 'none' is firm liquidity
    fx_child(lps, sigma_bp_sqrt_ms, rng)      one request routed to the cheapest stream; each last-look rejection
                                              (firm.lastlook.check) costs the move that caused it and the request
                                              goes to the next stream: (cost bp, rejections)
    rfq(n, markup, sigma, leak)               firm.rfq's expected cost of selling a block to n dealers, split into
                                              markup, competition (minus sigma E[max of n]) and leakage
    amm_cost_bp(notional, reserve_in, reserve_out, fee_bps)   buying with a constant-product pool (firm.amm), against
                                              the pool's starting price
    cex_amm_split(notional, market, reserve_in, reserve_out, fee_bps, grid)   the share sent to the pool that
                                              minimises exchange impact + pool cost, and the costs
    orders_allowed(governor, horizon_ms, n)   whether n evenly spaced orders fit a firm.ratelimit governor
"""
from __future__ import annotations

import math
import pathlib
import sys
from dataclasses import dataclass

import numpy as np

_FIRM = pathlib.Path(__file__).resolve().parents[1]
for c in ("match", "lastlook", "rfq", "amm", "ratelimit", "acexec"):
    sys.path.insert(0, str(_FIRM / c))
from firm_amm import cp_amount_out  # noqa: E402
from firm_lastlook import check  # noqa: E402
from firm_match import Quote, best_of, implied_in  # noqa: E402
from firm_rfq import expected_cost, expected_max_normal  # noqa: E402


@dataclass(frozen=True)
class Market:
    name: str
    half_spread_bp: float
    sigma_day_bp: float
    adv: float
    y: float = 0.7


def sqrt_impact_bp(m: Market, notional: float) -> float:
    return m.y * m.sigma_day_bp * math.sqrt(notional / m.adv)


def children(notional: float, scheduler, n: int) -> np.ndarray:
    t = np.linspace(0.0, scheduler.h, n + 1)
    return -np.diff(scheduler.targets(t)) * notional / scheduler.x


# -- futures -------------------------------------------------------------------------------------------------
def _sell(bid, qty, lots, tick):
    """Proceeds of selling `lots` into a bid of `qty` at `bid`, the rest a tick lower."""
    first = min(lots, qty)
    return first * bid + (lots - first) * (bid - tick)


def _buy(ask, qty, lots, tick):
    first = min(lots, qty)
    return first * ask + (lots - first) * (ask + tick)


def roll(front: Quote, back: Quote, spread: Quote, lots: int, tick: int) -> dict:
    mid = (front.bid + front.ask) / 2 - (back.bid + back.ask) / 2

    def legs(n):                                 # sell the front, buy the back
        sold = _sell(front.bid, front.bid_qty, n, tick)
        return sold - _buy(back.ask, back.ask_qty, n, tick)

    def via(book):                               # sell the spread, leg the rest
        got = min(lots, book.bid_qty) if book.bid is not None else 0
        return got * (book.bid or 0) + legs(lots - got)
    implied = best_of(spread, implied_in(front, back))
    out = {"legs": legs(lots), "spread_book": via(spread), "implied": via(implied)}
    return {k: mid - v / lots for k, v in out.items()} | {"mid": mid}


# -- FX ------------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class LP:
    name: str
    half_bp: float
    hold_ms: float
    threshold_bp: float
    policy: str = "asymmetric"


def fx_child(lps, sigma_bp_sqrt_ms: float, rng) -> tuple[float, int]:
    """Buy at the cheapest stream; a rejection after its hold costs the (client-favourable)
    move and the request goes on to the next stream, at the new price."""
    moved, rejections = 0.0, 0
    for lp in sorted(lps, key=lambda x: x.half_bp):
        if lp.policy == "none":
            return moved + lp.half_bp, rejections
        m = rng.normal(0.0, sigma_bp_sqrt_ms * math.sqrt(lp.hold_ms))
        if check(m, lp.threshold_bp, lp.policy):
            return moved + lp.half_bp, rejections
        moved += m
        rejections += 1
    raise ValueError("every stream rejected and there is no firm liquidity")


# -- bonds ---------------------------------------------------------------------------------------------------
def rfq(n: int, markup: float, sigma: float, leak: float) -> dict:
    return {"markup": markup, "competition": -sigma * expected_max_normal(n), "leakage": leak * (n - 1),
            "total": expected_cost(n, markup, sigma, leak)}


# -- crypto --------------------------------------------------------------------------------------------------
def amm_cost_bp(notional: float, reserve_in: float, reserve_out: float, fee_bps: int) -> float:
    if notional <= 0:
        return 0.0
    unit = 1e6                                     # integer amounts in micro-units, as on chain
    out = cp_amount_out(int(notional * unit), int(reserve_in * unit), int(reserve_out * unit), fee_bps)
    price0 = reserve_in / reserve_out
    return ((notional / (out / unit)) / price0 - 1.0) * 1e4


def cex_amm_split(notional: float, market: Market, reserve_in: float, reserve_out: float, fee_bps: int,
                  grid: int = 401) -> dict:
    """Send x to the pool and the rest to the exchange; the pool's price starts at the exchange's mid."""
    best = None
    for x in np.linspace(0.0, notional, grid):
        cex = (notional - x) * (market.half_spread_bp + sqrt_impact_bp(market, notional - x))
        pool = x * amm_cost_bp(x, reserve_in, reserve_out, fee_bps)
        total = (cex + pool) / notional
        if best is None or total < best["total"]:
            best = {"x": float(x), "total": float(total)}
    best["cex_only"] = market.half_spread_bp + sqrt_impact_bp(market, notional)
    best["saving"] = best["cex_only"] - best["total"]
    return best


def orders_allowed(governor, horizon_ms: int, n: int) -> bool:
    for i in range(n):
        ok, _ = governor.try_send(int(i * horizon_ms / n), 1, True)
        if not ok:
            return False
    return True
