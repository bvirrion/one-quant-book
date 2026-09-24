"""Call auctions: the example book, an indicative-price path, and the price of an imbalance
(Chapter 13). Parameters illustrative."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/auction"))
from firm_auction import AuctionOrder, demand, supply, uncross

EXAMPLE = [
    AuctionOrder("b1", +1, 300, None, 1), AuctionOrder("b2", +1, 500, 1003, 2),
    AuctionOrder("b3", +1, 400, 1001, 3), AuctionOrder("b4", +1, 600, 1000, 4),
    AuctionOrder("s1", -1, 200, None, 5), AuctionOrder("s2", -1, 400, 999, 6),
    AuctionOrder("s3", -1, 500, 1001, 7), AuctionOrder("s4", -1, 700, 1002, 8),
]


def curves(orders, lo: int, hi: int):
    return [(p, demand(orders, p), supply(orders, p)) for p in range(lo, hi + 1)]


def random_book(n: int, seed: int, fair: int = 1000, width: float = 6.0) -> list[AuctionOrder]:
    """Limit orders scattered around a fair price: buyers a little below, sellers a little above."""
    rng = np.random.default_rng(seed)
    out = []
    for k in range(n):
        side = 1 if rng.random() < 0.5 else -1
        price = int(round(fair - side * 1.0 + rng.normal(0.0, width)))
        out.append(AuctionOrder(f"o{k}", side, int(rng.integers(1, 20)) * 100, price, k))
    return out


def indicative_path(orders: list[AuctionOrder], reference: int, steps: int = 40):
    """Indicative price, paired volume and surplus as the orders arrive during the call phase."""
    out = []
    for k in range(1, steps + 1):
        seen = orders[: len(orders) * k // steps]
        u = uncross(seen, reference)
        out.append((k, u.price, u.volume, u.surplus))
    return out


def imbalance_impact(n_books: int, imbalance_fraction: float, seed: int = 0) -> float:
    """Mean move of the uncrossing price, in ticks, when a market buy order worth
    `imbalance_fraction` of the balanced auction's volume is added."""
    moves = []
    for s in range(seed, seed + n_books):
        book = random_book(400, s)
        base = uncross(book, 1000)
        extra = AuctionOrder("moc", +1, max(100, int(base.volume * imbalance_fraction) // 100 * 100), None, 10**6)
        moves.append(uncross(book + [extra], 1000).price - base.price)
    return float(np.mean(moves))
