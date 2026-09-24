import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from asia_rules import autocorr, locked_days, round_to_lot, round_trip_tax_bp, truncate


def test_locked_days():
    assert locked_days(0.05, 0.10) == 0           # fits in one day
    assert locked_days(0.10, 0.10) == 0
    assert locked_days(0.21, 0.10) == 1           # 1.1^2 = 1.21: one full limit day, arrives on the second
    assert locked_days(0.50, 0.10) == 4           # 1.1^4 = 1.46 < 1.5 <= 1.1^5
    assert locked_days(-0.50, 0.10) == 6          # 0.9^6 = 0.53 > 0.5 >= 0.9^7


def test_truncation_conserves_the_total_move():
    r = np.array([0.35, 0.0, 0.0, 0.0, 0.0])
    o = truncate(r, 0.10)
    assert np.allclose(o[:3], 0.10) and np.prod(1 + o) == pytest.approx(1.35)


def test_truncation_creates_autocorrelation_and_hides_volatility():
    rng = np.random.default_rng(1)
    true = rng.standard_t(3, 40_000) * 0.035 / np.sqrt(3)
    obs = truncate(true, 0.10)
    assert abs(autocorr(true)) < 0.02 and autocorr(obs) > 0.03
    assert obs.std() < true.std()


def test_lots_and_taxes():
    assert round_to_lot(1_234, 500) == 1_000 and round_to_lot(499, 500) == 0
    assert round_trip_tax_bp(0.0010, 0.0010) == pytest.approx(20)
