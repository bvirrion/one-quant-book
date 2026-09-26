"""firm.auctionmm -- providing liquidity into the closing auction (One Quant Book 11, chapter 16).

Built on firm.auction (Book 1): the closing book is uncrossed by firm.auction.uncross. Prices are integer ticks
around a reference P0. The closing book holds paired market-on-close interest, limit-on-close orders that deepen away
from P0 (d0 * j shares at j ticks), and a market-on-close imbalance I. A provider offsets the imbalance with a
limit order of q shares k ticks through P0 on the other side. Tomorrow's value is P0 plus a share `perm` of the move
the imbalance alone would have caused (the information in it); the rest reverts.

API (stable):
    ClosingBook(p0, levels, d0, paired)             the book without the imbalance
    ClosingBook.orders(imbalance, q, k)             firm.auction orders: book, imbalance (buy if > 0), provider
    close_price(book, imbalance, q=0, k=0)          uncrossing price, and the provider's fill
    impact_curve(book, imbalances)                  closing move (ticks) against imbalance, without a provider
    provider(book, imbalance, q, k, perm, late_sd, n, seed)
                                                    expected fill, P&L per share and in total, with late orders
                                                    that change the final imbalance by N(0, late_sd)
    best_offer(book, imbalance, perm, qs, ks, ...)  the (q, k) maximising expected total P&L
    publications(final, times, seed, drift_sd)      a schedule of published imbalances converging to the final one
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "auction"))
import firm_auction as fa  # noqa: E402


class ClosingBook:
    def __init__(self, p0: int = 10000, levels: int = 60, d0: int = 2000, paired: int = 300000):
        self.p0, self.levels, self.d0, self.paired = p0, levels, d0, paired

    def orders(self, imbalance: int, q: int = 0, k: int = 0) -> list[fa.AuctionOrder]:
        o, seq = [], 0
        for side in (1, -1):
            o.append(fa.AuctionOrder(f"moc{side}", side, self.paired, None, seq))
            seq += 1
        for j in range(1, self.levels + 1):
            o.append(fa.AuctionOrder(f"s{j}", -1, self.d0 * j, self.p0 + j, seq))
            o.append(fa.AuctionOrder(f"b{j}", 1, self.d0 * j, self.p0 - j, seq + 1))
            seq += 2
        if imbalance:
            o.append(fa.AuctionOrder("imb", 1 if imbalance > 0 else -1, abs(int(imbalance)), None, seq))
            seq += 1
        if q:
            side = -1 if imbalance >= 0 else 1
            o.append(fa.AuctionOrder("prov", side, int(q), self.p0 - side * k, seq))
        return o


def close_price(book: ClosingBook, imbalance: int, q: int = 0, k: int = 0) -> tuple[int, int]:
    u = fa.uncross(book.orders(imbalance, q, k), book.p0)
    fill = dict(u.fills).get("prov", 0)
    return u.price, fill


def impact_curve(book: ClosingBook, imbalances) -> list[int]:
    return [close_price(book, int(i))[0] - book.p0 for i in imbalances]


def provider(book: ClosingBook, imbalance: int, q: int, k: int, perm: float = 0.15, late_sd: float = 0.0,
             n: int = 1, seed: int = 0) -> dict:
    """The provider sells (buys) q shares k ticks above (below) P0 against a buy (sell) imbalance. Late orders move
    the final imbalance by N(0, late_sd); tomorrow's value is P0 + perm * (the no-provider move at the final
    imbalance). P&L in ticks: sign * fill * (close - value)."""
    rng = np.random.default_rng(seed)
    sign = 1 if imbalance >= 0 else -1
    fills, pnl = [], []
    for _ in range(n):
        final = int(round(imbalance + (rng.normal(0.0, late_sd) if late_sd else 0.0)))
        p, f = close_price(book, final, q, k)
        move = close_price(book, final)[0] - book.p0
        value = book.p0 + perm * move
        fills.append(f)
        pnl.append(sign * f * (p - value))
    fills, pnl = np.array(fills, float), np.array(pnl, float)
    tot = float(pnl.mean())
    return {"fill": float(fills.mean()), "pnl": tot, "per_share": tot / float(fills.mean()) if fills.mean() else 0.0}


def best_offer(book: ClosingBook, imbalance: int, perm: float, qs, ks, late_sd: float = 0.0, n: int = 1,
               seed: int = 0) -> dict:
    best = None
    for q in qs:
        for k in ks:
            r = provider(book, imbalance, int(q), int(k), perm, late_sd, n, seed)
            if best is None or r["pnl"] > best["pnl"]:
                best = {"q": int(q), "k": int(k), **r}
    return best


def publications(final: int, times=(600, 300, 120, 60, 10), seed: int = 0, drift_sd: float = 0.3) -> list[int]:
    """Published imbalances at the given seconds before the close: the final imbalance less a late-order component
    that shrinks with the time left (standard deviation drift_sd * |final| * sqrt(t / 600))."""
    rng = np.random.default_rng(seed)
    return [int(round(final - rng.normal(0.0, drift_sd * abs(final) * np.sqrt(t / 600.0)))) for t in times]
