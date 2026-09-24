"""Acceptance tests of the Chapter 15 build."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_recon import Security, predict, tracker_trades, weights

U = [
    Security("A", 100, 50.0, 1.0, 10, True),      # cap 5000
    Security("B", 100, 40.0, 0.5, 10, True),      # 4000, half floated
    Security("C", 100, 30.0, 1.0, 10, False),     # 3000, outsider ranked 3
    Security("D", 100, 25.0, 1.0, 5, True),       # 2500, member ranked 4
    Security("E", 100, 10.0, 1.0, 10, False),
]


def test_plain_top_three_swaps_d_for_c():
    p = predict(U, 3, 0)
    assert p.members == ("A", "B", "C") and p.adds == ("C",) and p.deletes == ("D",)


def test_buffer_of_one_keeps_d():
    p = predict(U, 3, 1)
    assert p.members == ("A", "B", "D") and p.adds == () and p.deletes == ()


def test_float_adjusted_weights_and_tracker_trades():
    p = predict(U, 3, 0)
    w = weights(U, p.members)
    assert w["B"] == pytest.approx(2000 / 10_000) and sum(w.values()) == pytest.approx(1.0)
    trades = {t.symbol: t for t in tracker_trades(U, p, 1_000.0)}
    assert trades["C"].dollars == pytest.approx(300.0) and trades["C"].shares == 10
    assert trades["C"].adv_multiple == pytest.approx(1.0)
    assert trades["D"].dollars == pytest.approx(-1000 * 2500 / 9500) and trades["D"].shares == -11
    assert trades["D"].adv_multiple == pytest.approx(2.2)
