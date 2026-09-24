"""Numbers in the solutions of Book 3, Chapter 17."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import m3_perp as m
from firm_perp import funding_rate, pnl_inverse, pnl_quanto


def test_exercises():
    assert round(2 * 60_000 * 0.0003, 2) == 36.0
    assert [round(1e4 * funding_rate(p), 6) for p in (0.0002, 0.001, -0.0008)] == [1.0, 5.0, -3.0]
    assert round(pnl_inverse(60_000, 60_000, 50_000), 6) == -0.2 and round(pnl_inverse(60_000, 60_000, 75_000), 6) == 0.2
    assert round(-0.2 * 50_000) == -10_000 and round(0.2 * 75_000) == 15_000
    assert round(pnl_quanto(10_000, 1e-6, 3_000, 3_300), 6) == 3.0 and round(3.0 * 60_000) == 180_000
    assert round(0.0001 * 3 * 365 * 10e6) == 1_095_000
    r = {y: round(100 * m.funding_trade(v), 2) for y, v in m.yearly_funding().items()}
    assert r == {2020: 12.93, 2021: 23.2, 2022: 2.95, 2023: 5.79, 2024: 8.89, 2025: 3.7, 2026: 2.02}


def test_problem():
    assert round(0.1192 * 100, 2) == 11.92 and round(2 * (0.001 + 0.0005) * 100, 2) == 0.3
    assert round(100 * 0.0001 * 3 * 365, 2) == 10.95
    assert round(100 * m.margin_to_survive(), 2) == 30.65
    assert round(11.92 - 0.3, 2) == 11.62 and round(100 * m.funding_trade(0.1192), 2) == 8.89
    assert round(100 * (30.65 - 0.5) / 100.5, 1) == 30.0
