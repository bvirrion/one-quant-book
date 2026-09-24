"""Numbers gate: every numerical answer printed in the Chapter 21 text and solutions."""
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from basis_demo import DEC, DIVS, MAR, TODAY, example_band, roll_yield, rolled_index

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/fairvalue"))
from firm_fairvalue import dividends_to_expiry, fair_value, implied_rate, roll_richness_bp

FV = fair_value(6000.0, 0.042, TODAY, DEC, DIVS)


def test_text():
    assert round(300_000 * 0.042 * 91 / 360) == 3185 and round(21.0854 * 50) == 1054
    assert round(6000 * 0.042 * 91 / 360, 2) == 63.70
    assert round(dividends_to_expiry(DIVS, TODAY, DEC, 0.042), 2) == 21.09 and round(FV, 2) == 6042.61
    assert round(implied_rate(6047.20, 6000.0, TODAY, DEC, DIVS) * 100, 2) == 4.50
    lo, hi = example_band()
    assert (round(FV - lo, 2), round(hi - FV, 2), round(lo, 2), round(hi, 2)) == (10.27, 6.47, 6032.35, 6049.09)
    assert round(6050.50 - FV, 2) == 7.89 and round(6050.50 - hi, 2) == 1.41 and round(1.41 * 50) == 70
    assert round(6000 * 0.042 / 360, 1) == 0.7
    spot = np.full(25, 70.0)
    a = rolled_index(np.column_stack([spot, spot * 1.012]))[-1]
    b = rolled_index(np.column_stack([spot, spot * 0.990]))[-1]
    assert (round(a, 3), round(b, 3)) == (0.751, 1.273)


def test_exercises():
    assert round(fair_value(6000.0, 0.042, TODAY, DEC, []), 2) == 6063.70
    assert round(roll_yield(70.0, 70.84, 1 / 12) * 100, 1) == -14.2 and round(roll_yield(70.0, 69.30, 1 / 12) * 100, 1) == 12.1
    assert round(fair_value(6000.0, 0.0445, TODAY, DEC, DIVS) - FV, 2) == 3.79
    spot = np.full(25, 70.0)
    prem = np.linspace(0.012, 0.0, 25)
    assert round(rolled_index(np.column_stack([spot, spot * (1 + prem)]))[-1], 3) == 0.861


def test_problem():
    n = round(1e9 / 300_000)
    assert n == 3333
    fv_mar = fair_value(6000.0, 0.042, TODAY, MAR, DIVS)
    assert round(fv_mar, 2) == 6085.01 and round(fv_mar - FV, 2) == 42.39
    interest = 6000 * 0.042 * 91 / 360
    assert round(interest, 2) == 63.70 and round(interest - (fv_mar - FV), 2) == 21.31
    assert roll_richness_bp(fv_mar - FV + 4.55, 6000.0, 0.042, TODAY, DEC, MAR, DIVS) == pytest.approx(30.0, abs=0.01)
    rich, trade = 4.55 * 50 * n, 0.025 * 50 * n
    assert rich == pytest.approx(758_257.5) and trade == pytest.approx(4_166.25)
    assert round(4 * (rich + trade)) == 3_049_695 and round(4 * (rich + trade) / 1e9 * 1e4, 1) == 30.5
