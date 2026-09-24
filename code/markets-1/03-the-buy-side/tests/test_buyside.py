import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from buyside import information_ratio, run_fees, tracking_error, years_to_significance


def test_tracking_error_of_a_shifted_copy_is_zero():
    b = np.random.default_rng(0).normal(0, 0.04, 60)
    assert tracking_error(b - 0.001, b) == pytest.approx(0.0, abs=1e-12)


def test_te_and_ir_recover_inputs():
    rng = np.random.default_rng(1)
    b = rng.normal(0, 0.04, 12_000)
    f = b + 0.02 / 12 + rng.normal(0, 0.04 / np.sqrt(12), 12_000)
    assert tracking_error(f, b) == pytest.approx(0.04, rel=0.03)
    assert information_ratio(f, b) == pytest.approx(0.5, abs=0.1)


def test_years_to_significance():
    assert years_to_significance(0.5) == pytest.approx(16.0)
    assert years_to_significance(2.0) == pytest.approx(1.0)


def test_no_performance_fee_below_the_high_water_mark():
    r = run_fees([0.30, -0.20, 0.10], mgmt=0.0, perf=0.20)
    assert r.perf_fees[0] == pytest.approx(0.06)
    assert r.perf_fees[1] == 0.0
    # 1.24 -> 0.992 -> 1.0912 : still under the mark of 1.24
    assert r.perf_fees[2] == 0.0 and r.high_water[-1] == pytest.approx(1.24)
