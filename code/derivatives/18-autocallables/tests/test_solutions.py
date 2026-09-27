"""Numbers gate: every numerical answer printed in Book 5, Chapter 18 (text and solutions)."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from dv_autocall import (
    cliff,
    fair_coupon,
    fair_coupon_daily_ki,
    flat,
    price_vs_vol,
    sensitivities,
    snowball_price,
    worst_of,
)


# Full-size Monte Carlo behind the book's printed numbers: make test-code / make reproduce, not CI
# (CI runs test_small_runs).
@pytest.mark.reference
def test_phoenix():
    f = sensitivities()["fair"]
    assert (round(f["coupon"], 2), round(f["annual"], 2), round(f["zero_coupon_value"], 2), round(f["per_coupon_point"], 2)) == (
        1.55, 6.18, 95.99, 2.60)
    assert round(100 * f["call_probs"][0], 1) == 57.6 and round(100 * sum(f["call_probs"][:4]), 1) == 80.5
    assert (round(100 * (f["maturity_prob"] - f["ki_prob"]), 1), round(100 * f["ki_prob"], 1)) == (5.7, 6.3)
    assert round(100 * sensitivities()["flat_vol"], 1) == 20.0 and round(sensitivities()["flat_atm3"], 2) == 102.78
    assert round(fair_coupon(flat(sensitivities()["flat_vol"]))["annual"], 2) == 3.14


# Full-size Monte Carlo behind the book's printed numbers: make test-code / make reproduce, not CI
# (CI runs test_small_runs).
@pytest.mark.reference
def test_sensitivities():
    assert round(sensitivities()["vega_parallel"], 2) == -0.35
    assert [round(v, 2) for v in sensitivities()["vega_buckets"]] == [-0.16, -0.05, -0.14]
    assert (round(sensitivities()["skew"], 2), round(sensitivities()["dividend"], 2)) == (-0.24, -0.20)
    pv = dict(price_vs_vol())
    assert (round(pv[-0.04], 2), round(pv[0.06], 2)) == (101.33, 97.90)
    wo = worst_of()
    assert (round(wo[0.5]["annual"], 1), round(wo[0.7]["annual"], 1)) == (11.5, 10.4)
    assert (round(100 * wo[0.5]["ki_prob"], 1), round(100 * wo[0.7]["ki_prob"], 1)) == (18.1, 14.6)


# Full-size Monte Carlo behind the book's printed numbers: make test-code / make reproduce, not CI
# (CI runs test_small_runs).
@pytest.mark.reference
def test_snowball_and_cliff():
    sb = snowball_price()
    assert (round(sb["price"], 2), round(sb["se"], 2), round(100 * sb["ki_prob"], 1)) == (100.44, 0.06, 15.6)
    c = cliff()
    one = c[1]
    assert (round(one["delta_before"], 2), round(one["delta_after"], 2), round(one["sold"] / 1e6)) == (7.63, 1.00, 497)
    assert (round(c[3]["sold"] / 1e6), round(c[12]["sold"] / 1e6)) == (254, 97)
    assert round((7.63 - 1.00) * 0.75 * 100) == 497


# Full-size Monte Carlo behind the book's printed numbers: make test-code / make reproduce, not CI
# (CI runs test_small_runs).
@pytest.mark.reference
def test_exercises():
    assert round((98 - sensitivities()["fair"]["zero_coupon_value"]) / sensitivities()["fair"]["per_coupon_point"], 2) == 0.78
    d = fair_coupon_daily_ki()
    assert (round(d["coupon"], 2), round(d["annual"], 2), round(100 * d["ki_prob"], 1)) == (1.91, 7.62, 10.4)


def test_small_runs():
    # The same pricers on 2,000 paths (common random numbers): what the printed numbers rest on, not their digits.
    n = 2_000
    s = sensitivities(n=n)
    f = s["fair"]
    assert f["coupon"] > 0 and f["per_coupon_point"] > 0 and 0 < f["zero_coupon_value"] < 100
    assert abs(sum(f["call_probs"]) + f["maturity_prob"] - 1) < 1e-9 and 0 <= f["ki_prob"] <= f["maturity_prob"]
    assert s["vega_parallel"] < 0 and len(s["vega_buckets"]) == 3
    pv = [p for _, p in price_vs_vol(n=n)]
    assert all(a > b for a, b in zip(pv, pv[1:], strict=False))  # the investor is short volatility
    wo = worst_of(n=n)
    assert wo[0.5]["annual"] > wo[0.7]["annual"] > f["annual"]  # worst-of pays more, and more when less correlated
    assert fair_coupon_daily_ki(n=n)["annual"] > f["annual"]  # daily monitoring of the barrier costs the investor
    sb = snowball_price(n=n)
    assert 0 < sb["ki_prob"] < 1 and sb["se"] > 0
