"""Acceptance tests of the Chapter 7 build (Python reference)."""
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_pnl import BUY, SELL, Book, Position


def test_round_trip_realises_the_difference():
    p = Position()
    p.on_fill(BUY, 100, 500_000)
    p.on_fill(SELL, 100, 501_200)
    assert p.quantity == 0 and p.realised == pytest.approx(120_000) and p.total(1) == 120_000


def test_average_cost_and_partial_close():
    p = Position()
    p.on_fill(BUY, 100, 500_000)
    p.on_fill(BUY, 300, 504_000)
    assert p.avg_cost == pytest.approx(503_000)
    p.on_fill(SELL, 200, 506_000)
    assert p.realised == pytest.approx(200 * 3_000) and p.quantity == 200 and p.avg_cost == pytest.approx(503_000)


def test_flip_opens_the_remainder_at_the_fill_price():
    p = Position()
    p.on_fill(BUY, 100, 500_000)
    p.on_fill(SELL, 250, 498_000)
    assert p.quantity == -150 and p.avg_cost == 498_000 and p.realised == pytest.approx(-200_000)
    assert p.unrealised(497_000) == pytest.approx(150_000)


def test_split_always_adds_up_to_the_exact_total():
    rng, p = np.random.default_rng(7), Position()
    for _ in range(5_000):
        p.on_fill(BUY if rng.random() < 0.5 else SELL, int(rng.integers(1, 9)) * 100,
                  int(rng.integers(499_000, 501_000)), fee=int(rng.integers(0, 50)))
    mark = 500_250
    assert p.realised + p.unrealised(mark) - p.fees == pytest.approx(p.total(mark), abs=1e-3)


def test_book_exposures():
    b = Book()
    b.on_fill("AAA", BUY, 1000, 200_000)
    b.on_fill("BBB", SELL, 500, 300_000)
    marks = {"AAA": 200_000, "BBB": 300_000}
    assert b.gross_exposure(marks) == 350_000_000 and b.net_exposure(marks) == 50_000_000


def test_rejects_bad_fills():
    with pytest.raises(ValueError):
        Position().on_fill(0, 100, 1)
    with pytest.raises(ValueError):
        Position().on_fill(BUY, 0, 1)
