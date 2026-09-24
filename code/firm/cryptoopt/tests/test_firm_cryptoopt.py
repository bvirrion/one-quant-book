"""Acceptance tests of the Book 3, Chapter 19 build (inverse options, conversions, basis)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_cryptoopt import (
    annualised_basis,
    coin_premium,
    etf_basis_carry,
    forward_delta,
    premium_adjusted_delta,
    return_on_margin,
    usd_premium,
)


def test_coin_premium_round_trip():
    f, t = 84_538.67, 91.866 / 365
    c = coin_premium(f, 90_000, t, 0.3746, "C")
    assert abs(c - 0.04921) < 2e-5                     # the venue's mark on 24 Sep 2026 was 0.04920697
    assert abs(usd_premium(c, f) - c * f) < 1e-9


def test_parity_in_coin():
    f, t, k, v = 60_000.0, 0.25, 65_000.0, 0.5
    call, put = coin_premium(f, k, t, v, "C"), coin_premium(f, k, t, v, "P")
    assert abs((call - put) - (f - k) / f) < 1e-12        # parity with zero rate, in coin


def test_premium_adjusted_delta():
    f, t, v = 60_000.0, 0.25, 0.5
    d = forward_delta(f, 60_000, t, v, "C")
    assert abs(d - 0.5 * (1 + math.erf(0.125 / math.sqrt(2)))) < 1e-12   # at the money: N(v sqrt(t) / 2)
    assert premium_adjusted_delta(f, 60_000, t, v, "C") < d
    assert premium_adjusted_delta(f, 60_000, t, v, "P") < forward_delta(f, 60_000, t, v, "P")


def test_basis_and_carry():
    assert round(annualised_basis(84_533.98, 83_499.12, 92), 5) == round((84_533.98 / 83_499.12 - 1) * 365 / 92, 5)
    assert round(annualised_basis(101, 100, 365, "continuous"), 6) == round(math.log(1.01), 6)
    c = etf_basis_carry(0.10, 0.045, 0.0025, 0.005)
    assert round(c, 4) == 0.0475 and round(return_on_margin(c, 0.25, 0.10), 4) == round(0.0475 / 0.35, 4)


def test_reference_rate_resists_one_print():
    from firm_cryptoopt import reference_rate, weighted_median
    assert weighted_median([(100, 1), (101, 1), (102, 5)]) == 102
    trades = [(t, 100.0 + 0.01 * (t % 7), 1.0) for t in range(3600)]
    base = reference_rate(trades, 0, 3600)
    spiked = reference_rate(trades + [(1800.0, 150.0, 20.0)], 0, 3600)
    assert abs(spiked - base) < 0.01                    # one large print moves one partition's median little
