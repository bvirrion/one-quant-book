"""Acceptance tests of the Book 2, Chapter 9 build (OIS curve and swaps)."""
import datetime as dt
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_curve import add_years, bootstrap, bucket_dv01, par_rate, schedule, swap_pv

SPOT = dt.date(2026, 9, 29)
TENORS = [1, 2, 3, 5, 7, 10]
RATES = [0.0390, 0.0385, 0.0383, 0.0385, 0.0392, 0.0405]


def test_inputs_reprice_at_par():
    c = bootstrap(SPOT, TENORS, RATES)
    for n, r in zip(TENORS, RATES, strict=True):
        assert par_rate(c, schedule(SPOT, n)) == pytest.approx(r, abs=1e-12)
        assert swap_pv(c, schedule(SPOT, n), r, 1e8) == pytest.approx(0.0, abs=1e-3)


def test_flat_curve_gives_flat_par_rates():
    c = bootstrap(SPOT, TENORS, [0.04] * 6)
    assert par_rate(c, schedule(SPOT, 4)) == pytest.approx(0.04, abs=2e-6)
    assert par_rate(c, schedule(SPOT, 8)) == pytest.approx(0.04, abs=2e-6)


def test_payer_gains_when_rates_rise_and_buckets_sum_to_parallel():
    dates = schedule(SPOT, 10)
    b = bucket_dv01(SPOT, TENORS, RATES, dates, RATES[-1], 1e8)
    assert b[-1] > 0 and all(abs(x) < 1e-3 for x in b[:-1])          # a par swap loads only its own pillar
    fwd = schedule(add_years(SPOT, 5), 5)
    k = par_rate(bootstrap(SPOT, TENORS, RATES), fwd)
    bf = bucket_dv01(SPOT, TENORS, RATES, fwd, k, 1e8)
    assert bf[3] < 0 < bf[5]                                          # 5y5y: short the 5y, long the 10y


def test_leap_day():
    assert add_years(dt.date(2028, 2, 29), 1) == dt.date(2029, 2, 28)
