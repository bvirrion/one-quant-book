"""Auctions and the close (One Quant Book 11, chapter 16).

A closing book around 100.00 dollars (ticks of a cent): 300,000 shares of paired market-on-close interest and
limit-on-close orders of 2,000 x j shares at j cents on each side. A buy imbalance of 25,000 to 400,000 shares; a
provider offsets it with a limit sell of q shares k cents above the reference; tomorrow's value keeps a share `perm`
of the closing move the imbalance alone would cause. Uncrossed with firm.auction.
"""
from __future__ import annotations

import functools
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "firm" / "auctionmm"))
import firm_auctionmm as am  # noqa: E402

BOOK = am.ClosingBook()
IMBALANCES = (25000, 50000, 100000, 200000, 300000, 400000)
PERMS = (0.0, 0.15, 0.5)
QS = range(20000, 400001, 20000)
KS = range(0, 11)


def impact() -> dict:
    return dict(zip(IMBALANCES, am.impact_curve(BOOK, IMBALANCES), strict=True))


@functools.cache
def offers() -> dict:
    return {(i, p): am.best_offer(BOOK, i, p, QS, KS) for i in IMBALANCES for p in PERMS}


def with_provider(imbalance: int = 200000, perm: float = 0.15) -> dict:
    o = offers()[(imbalance, perm)]
    p, _ = am.close_price(BOOK, imbalance, o["q"], o["k"])
    return {"close_move": p - BOOK.p0, "alone_move": am.close_price(BOOK, imbalance)[0] - BOOK.p0, **o}


@functools.cache
def late(imbalance: int = 200000, perm: float = 0.15, late_sd: float = 60000.0) -> dict:
    """The provider sizes on the published imbalance but late orders move the final one."""
    naive = offers()[(imbalance, perm)]
    known = am.provider(BOOK, imbalance, naive["q"], naive["k"], perm)
    same = am.provider(BOOK, imbalance, naive["q"], naive["k"], perm, late_sd, n=100, seed=5)
    best = am.best_offer(BOOK, imbalance, perm, range(60000, 180001, 20000), range(0, 5), late_sd, n=100, seed=5)
    return {"known": known, "same_offer": same, "best": best}


def schedule() -> list[int]:
    return am.publications(200000, seed=3)


def deeper(d0: int = 4000, imbalance: int = 200000, perm: float = 0.15) -> dict:
    """Exercise 7: a closing book twice as deep."""
    book = am.ClosingBook(d0=d0)
    o = am.best_offer(book, imbalance, perm, QS, KS)
    return {"move": am.close_price(book, imbalance)[0] - book.p0, **o}
