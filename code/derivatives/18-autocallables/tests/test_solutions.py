"""Numbers gate: every numerical answer printed in Book 5, Chapter 18 (text and solutions)."""
import pathlib
import sys

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

S = sensitivities()


def test_phoenix():
    f = S["fair"]
    assert (round(f["coupon"], 2), round(f["annual"], 2), round(f["zero_coupon_value"], 2), round(f["per_coupon_point"], 2)) == (
        1.55, 6.18, 95.99, 2.60)
    assert round(100 * f["call_probs"][0], 1) == 57.6 and round(100 * sum(f["call_probs"][:4]), 1) == 80.5
    assert (round(100 * (f["maturity_prob"] - f["ki_prob"]), 1), round(100 * f["ki_prob"], 1)) == (5.7, 6.3)
    assert round(100 * S["flat_vol"], 1) == 20.0 and round(S["flat_atm3"], 2) == 102.78
    assert round(fair_coupon(flat(S["flat_vol"]))["annual"], 2) == 3.14


def test_sensitivities():
    assert round(S["vega_parallel"], 2) == -0.35
    assert [round(v, 2) for v in S["vega_buckets"]] == [-0.16, -0.05, -0.14]
    assert (round(S["skew"], 2), round(S["dividend"], 2)) == (-0.24, -0.20)
    pv = dict(price_vs_vol())
    assert (round(pv[-0.04], 2), round(pv[0.06], 2)) == (101.33, 97.90)
    wo = worst_of()
    assert (round(wo[0.5]["annual"], 1), round(wo[0.7]["annual"], 1)) == (11.5, 10.4)
    assert (round(100 * wo[0.5]["ki_prob"], 1), round(100 * wo[0.7]["ki_prob"], 1)) == (18.1, 14.6)


def test_snowball_and_cliff():
    sb = snowball_price()
    assert (round(sb["price"], 2), round(sb["se"], 2), round(100 * sb["ki_prob"], 1)) == (100.44, 0.06, 15.6)
    c = cliff()
    one = c[1]
    assert (round(one["delta_before"], 2), round(one["delta_after"], 2), round(one["sold"] / 1e6)) == (7.63, 1.00, 497)
    assert (round(c[3]["sold"] / 1e6), round(c[12]["sold"] / 1e6)) == (254, 97)
    assert round((7.63 - 1.00) * 0.75 * 100) == 497


def test_exercises():
    assert round((98 - S["fair"]["zero_coupon_value"]) / S["fair"]["per_coupon_point"], 2) == 0.78
    d = fair_coupon_daily_ki()
    assert (round(d["coupon"], 2), round(d["annual"], 2), round(100 * d["ki_prob"], 1)) == (1.91, 7.62, 10.4)
