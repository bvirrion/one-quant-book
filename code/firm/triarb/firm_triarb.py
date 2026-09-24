"""Arbitrage scanner across venues and pairs (build of Book 3, Chapter 16).

Books are top-of-book quotes {venue: {pair: Quote}} with pairs written "BASE/QUOTE". A triangular
cycle converts a quote asset into a base asset, into a second one and back on one venue; a
cross-venue trade buys a pair on one venue and sells it on another, either from prepositioned
inventory (both legs at once, rebalancing later at a known cost) or by transferring the asset
(price risk during the transfer, charged as z standard deviations of the move).
"""
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Quote:
    bid: float
    ask: float
    bid_size: float      # in base units
    ask_size: float


@dataclass(frozen=True)
class Opportunity:
    kind: str            # "triangular" or "cross"
    route: str
    edge_bp: float       # net of fees and costs, per unit of notional
    size_quote: float    # executable notional in the starting (quote) asset
    profit: float        # edge times size


def triangular(book: dict[str, Quote], a: str, b: str, q: str, fee: float) -> list[Opportunity]:
    """Both directions of the cycle q -> a -> b -> q with pairs a/q, b/q and b/a, taker fee `fee`."""
    aq, bq, ba = book[f"{a}/{q}"], book[f"{b}/{q}"], book[f"{b}/{a}"]
    k = (1 - fee) ** 3
    out = []
    # q -> a (buy a/q at ask), a -> b (buy b/a at ask), b -> q (sell b/q at bid)
    m1 = k * bq.bid / (aq.ask * ba.ask)
    s1 = min(aq.ask_size * aq.ask, ba.ask_size * ba.ask * aq.ask, bq.bid_size * ba.ask * aq.ask)
    out.append(Opportunity("triangular", f"{q}>{a}>{b}>{q}", 1e4 * (m1 - 1), s1, s1 * (m1 - 1)))
    # q -> b (buy b/q at ask), b -> a (sell b/a at bid), a -> q (sell a/q at bid)
    m2 = k * ba.bid * aq.bid / bq.ask
    s2 = min(bq.ask_size * bq.ask, ba.bid_size * bq.ask, aq.bid_size * bq.ask / ba.bid)
    out.append(Opportunity("triangular", f"{q}>{b}>{a}>{q}", 1e4 * (m2 - 1), s2, s2 * (m2 - 1)))
    return out


def cross(buy: Quote, sell: Quote, fee_buy: float, fee_sell: float, route: str,
          rebalance_bp: float = 0.0, transfer_minutes: float = 0.0, vol_annual: float = 0.0,
          z: float = 0.0) -> Opportunity:
    """Buy at `buy.ask`, sell at `sell.bid`. With prepositioned inventory pass rebalance_bp (the later
    cost of moving the asset back); with a transfer pass its duration, the volatility and z."""
    mid = 0.5 * (buy.ask + sell.bid)
    risk_bp = 1e4 * z * vol_annual * math.sqrt(transfer_minutes / (365 * 24 * 60))
    edge = 1e4 * (sell.bid * (1 - fee_sell) - buy.ask * (1 + fee_buy)) / mid - rebalance_bp - risk_bp
    size = min(buy.ask_size, sell.bid_size) * buy.ask
    return Opportunity("cross", route, edge, size, size * edge / 1e4)


def scan(books: dict[str, dict[str, Quote]], fees: dict[str, float], cycles: list[tuple[str, str, str]],
         rebalance_bp: float, min_edge_bp: float = 0.0) -> list[Opportunity]:
    """All triangular cycles on every venue and all cross-venue trades (prepositioned inventory) on
    every pair quoted on two venues, keeping those above `min_edge_bp`, largest profit first."""
    found = []
    for v, book in books.items():
        for a, b, q in cycles:
            if {f"{a}/{q}", f"{b}/{q}", f"{b}/{a}"} <= book.keys():
                found += triangular(book, a, b, q, fees[v])
    venues = sorted(books)
    for i, v in enumerate(venues):
        for w in venues[i + 1:]:
            for pair in sorted(books[v].keys() & books[w].keys()):
                for x, y in ((v, w), (w, v)):
                    found.append(cross(books[x][pair], books[y][pair], fees[x], fees[y],
                                       f"{pair} {x}>{y}", rebalance_bp))
    return sorted((o for o in found if o.edge_bp > min_edge_bp), key=lambda o: -o.profit)
