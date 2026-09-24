"""Numbers gate: every numerical answer printed in the Chapter 13 text and solutions."""
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from auction_sim import EXAMPLE, curves, random_book

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/auction"))
from firm_auction import AuctionOrder as O
from firm_auction import demand, supply, uncross


def test_text():
    table = {p: (d, s) for p, d, s in curves(EXAMPLE, 999, 1003)}
    assert table == {999: (1800, 600), 1000: (1800, 600), 1001: (1200, 1100), 1002: (800, 1800), 1003: (800, 1800)}
    u = uncross(EXAMPLE, 1000)
    assert (u.price, u.volume, u.surplus) == (1001, 1100, 100) and dict(u.fills)["b3"] == 300


def test_exercises():
    bk = [O("b1", 1, 400, 2010, 1), O("b2", 1, 300, 2005, 2), O("b3", 1, 500, 2000, 3),
          O("s1", -1, 200, 1995, 4), O("s2", -1, 600, 2005, 5), O("s3", -1, 300, 2010, 6)]
    assert [(demand(bk, p), supply(bk, p)) for p in (1995, 2000, 2005, 2010)] == [(1200, 200), (1200, 200), (700, 800), (400, 1100)]
    u = uncross(bk, 2000)
    assert (u.price, u.volume, u.surplus) == (2005, 700, -100) and dict(u.fills)["s2"] == 500
    two = [O("b", 1, 1000, 5020, 1), O("s", -1, 1000, 5000, 2)]
    assert uncross(two, 5012).price == 5012 and uncross(two, 5040).price == 5020
    assert round(300_000 / 65_000, 1) == 4.6 and round(300_000 / 65_000 * 0.01 / 80 * 1e4, 1) == 5.8
    assert 50e6 * 0.0012 == pytest.approx(60_000) and 50e6 * 0.0008 == pytest.approx(40_000)

    def slope(n):
        mv, qs = [], []
        for s in range(60):
            book = random_book(n, s)
            base = uncross(book, 1000)
            q = max(100, int(base.volume * 0.5) // 100 * 100)
            mv.append(uncross(book + [O("moc", 1, q, None, 10**6)], 1000).price - base.price)
            qs.append(q)
        return np.mean(mv) / np.mean(qs) * 1e5
    assert round(slope(400), 1) == 4.1 and round(slope(1600), 1) == 1.0


def test_problem():
    buy = [O("bm", 1, 50_000, None, 1), O("b1", 1, 80_000, 4010, 2), O("b2", 1, 120_000, 4000, 3), O("b3", 1, 150_000, 3990, 4)]
    sell = [O("sm", -1, 60_000, None, 5), O("s1", -1, 100_000, 3995, 6), O("s2", -1, 140_000, 4005, 7),
            O("s3", -1, 200_000, 4015, 8), O("s4", -1, 250_000, 4030, 9), O("s5", -1, 300_000, 4050, 10)]
    bk = buy + sell
    u = uncross(bk, 4000)
    assert (u.price, u.volume, u.surplus) == (4000, 160_000, 90_000) and dict(u.fills)["b2"] == 30_000
    bk2 = bk + [O("idx", 1, 500_000, None, 11)]
    u2 = uncross(bk2, 4000)
    assert (u2.price, u2.volume, u2.surplus) == (4030, 550_000, -200_000)
    assert demand(bk2, 4000) - supply(bk2, 4000) == 590_000
    assert round(0.30 / 40.00 * 1e4) == 75 and 0.30 * 500_000 == 150_000
    bk3 = bk2 + [O("l1", -1, 150_000, 4010, 12), O("l2", -1, 200_000, 4020, 13)]
    u3 = uncross(bk3, 4000)
    assert (u3.price, u3.volume, u3.surplus) == (4015, 550_000, -100_000) and dict(u3.fills)["s3"] == 100_000
    assert round(0.15 * 500_000) == 75_000 and round(0.10 * 150_000) == 15_000
    depth = ((supply(bk3, 4015) - supply(bk3, 4000)) + (demand(bk3, 4000) - demand(bk3, 4015))) / 15
    assert round(depth, -3) == 46_000 and round(500_000 / depth, 1) == 10.9
