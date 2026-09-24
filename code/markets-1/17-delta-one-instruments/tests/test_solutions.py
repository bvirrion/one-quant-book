"""Numbers gate: every numerical answer printed in the Chapter 17 text and solutions."""
import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from wrappers import WRAPPERS, DrTerms, crossover_years, dr_band_bp, parity, total

W = {w.name: w for w in WRAPPERS}
ORDER = ("shares", "ETF", "future", "swap", "CFD")


def test_text():
    assert [total(W[n], 1.0, 200.0, 1.0) for n in ORDER] == pytest.approx([140, 93, 68, 56, 296])
    assert [total(W[n], 1.0, 200.0, 0.0) for n in ORDER] == pytest.approx([90, 43, 68, 56, 296])
    assert 296 / 56 > 5
    assert 6000 * (1 + 0.029 * 0.25) == pytest.approx(6043.5)
    assert (6048 / 6000 - 1) / 0.25 + 0.013 == pytest.approx(0.045)
    assert crossover_years(W["shares"], W["swap"], 200.0, 0.0) == pytest.approx(2.7)
    assert round(crossover_years(W["shares"], W["future"], 200.0, 0.0), 1) == 1.6
    assert round(crossover_years(W["ETF"], W["future"], 200.0, 0.0) * 52) == 7              # weeks
    assert crossover_years(W["ETF"], W["swap"], 200.0, 0.0) is None
    lo, hi = dr_band_bp(5 / 1.25 / 4, 1.25, DrTerms(4.0, 0.05, 0.05, 0.0, 6.0))
    assert (lo, hi) == pytest.approx((-106.0, 106.0))


def test_exercises():
    assert 50e6 * 0.06 == 3e6 and round(50e6 * 0.046 * 91 / 360) == 581_389 and round(3e6 - 50e6 * 0.046 * 91 / 360) == 2_418_611
    assert 6000 * (1 + (0.047 - 0.013) * 0.25) == pytest.approx(6051.0)
    par = 42.10 * 2 * 1.17
    assert round(par, 2) == 98.51 and round((98.90 / par - 1) * 1e4) == 39
    assert round((60 - 16) / 250 * 365) == 64
    assert 150 * 0.30 == pytest.approx(45.0) and 150 * 0.15 == pytest.approx(22.5)
    q = [total(W[n], 0.25, 200.0, 1.0) for n in ORDER]
    assert q == pytest.approx([80.0, 27.75, 18.5, 18.5, 86.0])
    assert [4 * x for x in q] == pytest.approx([320, 111, 74, 74, 344])
    assert total(W["CFD"], 3.0, 200.0, 0.0) == pytest.approx(856.0) and total(W["shares"], 3.0, 200.0, 0.0) == pytest.approx(150.0)


def test_problem():
    t = DrTerms(4.0, 0.05, 0.05, 150.0, 6.0)
    assert parity(5.0, 1.25, t) == pytest.approx(25.0)
    assert dr_band_bp(5.0, 1.25, t) == pytest.approx((-26.0, 176.0))
    assert [round((p / 25 - 1) * 1e4) for p in (25.30, 25.50, 24.90)] == [120, 200, -40]
    cost = 2.5e6 * 0.015 + 100_000 * 0.05 + 2.5e6 * 6e-4
    assert cost == pytest.approx(44_000) and 2.55e6 - 2.5e6 - cost == pytest.approx(6_000)
    assert 6_000 / 2.5e6 * 1e4 == pytest.approx(24.0)
    cost2 = 100_000 * 0.05 + 2.5e6 * 6e-4
    assert 2.5e6 - 2.49e6 - cost2 == pytest.approx(3_500) and 3_500 / 2.5e6 * 1e4 == pytest.approx(14.0)
    assert round(0.08 * math.sqrt(2 / 252) * 1e4) == 71
    est = 25 * (1 + 1.1 * 0.015)
    assert round(est, 2) == 25.41 and round((25.45 / 25 - 1) * 1e4) == 180 and round((25.45 / est - 1) * 1e4) == 15
