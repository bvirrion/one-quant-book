"""Tests of the Chapter 22 teaching module (Book 3)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import m3_mev as m


def test_tolerance_table():
    rows = {t: r for t, *r in m.by_tolerance()}
    assert round(rows[50][0]) == 38_912 and round(rows[50][1]) == 5_067 and round(rows[50][3], 2) == 1.56
    assert round(rows[100][1]) == 10_130 and round(rows[100][3], 2) == 3.12
    assert rows[0][1] == 0


def test_gain_rises_to_the_bound():
    c = m.profit_curve(50)
    feasible = [g for _, g, ok in c if ok]
    assert feasible == sorted(feasible) and not c[-1][2]


def test_cex_dex():
    dx, p = m.cex_dex_arbitrage(3030)
    assert round(dx, -3) == 52_000 and round(p) == 182
    assert m.cex_dex_arbitrage(3005) == (0.0, 0.0) or m.cex_dex_arbitrage(3005)[1] < 1
