import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from basis_demo import DEC, DIVS, TODAY, basis_path, mispricing, roll_yield, rolled_index


def test_basis_converges_to_zero_and_jumps_up_on_dividend_dates():
    days, basis = basis_path(6000.0, 0.042, TODAY, DEC, DIVS)
    assert basis[-1] == pytest.approx(0.0) and basis[0] == pytest.approx(42.62, abs=0.01)
    jumps = [b - a for a, b in zip(basis[:-1], basis[1:], strict=True)]
    assert sum(1 for j in jumps if j > 0) == 3 and max(jumps) == pytest.approx(9.5 - 0.7, abs=0.2)


def test_mispricing_stays_inside_the_band():
    x, hits = mispricing(5000, -10.27, 6.47, 1.6, 0.05, 1)
    assert x.max() <= 6.47 and x.min() >= -10.27 and hits["upper"] > hits["lower"]


def test_roll_yield_signs_and_the_rolled_index():
    assert roll_yield(70.0, 70.84, 1 / 12) < 0 < roll_yield(70.0, 69.3, 1 / 12)
    flat_spot = np.column_stack([np.full(13, 70.0), np.full(13, 70.84)])
    assert rolled_index(flat_spot)[-1] == pytest.approx((70 / 70.84) ** 12)
