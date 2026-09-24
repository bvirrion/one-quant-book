"""Numbers gate: every numerical answer printed in Book 5, Chapter 19 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from dv_structured import (
    MARGIN,
    Q,
    R,
    T,
    bs,
    capped_note,
    decrement_example,
    named_result,
    participation_curve,
    reverse_convertible,
    smile,
    vol_target_options,
    zero_coupon,
)

N = named_result()
PC = {round(1e4 * s): p for s, p in participation_curve()}


def test_participation():
    assert round(100 * smile(T)(1.0), 1) == 20.5 and round(N["call"], 2) == 12.49
    assert round(N["zc_riskfree"], 2) == 94.18 and round(100 - N["zc_riskfree"] - MARGIN, 2) == 4.32
    assert [round(100 * PC[b], 1) for b in (0, 50, 100, 200, 300)] == [34.6, 42.1, 49.6, 64.2, 78.5]
    assert round(100 * (PC[50] - PC[0]), 1) == 7.5
    assert (round(1e4 * N["spread"]), round(100 * N["spread"], 2), round(N["zc_at_spread"], 2)) == (240, 2.40, 89.76)
    assert round(0.7 * N["call"], 2) == 8.74
    assert (round(100 * capped_note()["cap"], 1), round(100 * capped_note(0.0)["cap"], 1)) == (113.3, 108.7)


def test_reverse_convertible():
    rc = reverse_convertible()
    assert (round(rc["coupon"], 2), round(rc["put"], 2), round(rc["funding"], 2)) == (6.96, 4.26, 3.92)
    got = [(round(reverse_convertible(0.01, k)["coupon"], 2), round(reverse_convertible(0.01, k)["put"], 2)) for k in (0.8, 1.0)]
    assert got == [(5.17, 2.55), (9.71, 6.91)]


def test_indices():
    v = vol_target_options()
    assert (round(100 * v["realised"]["raw"], 1), round(100 * v["realised_sd"]["raw"], 1)) == (19.8, 8.2)
    assert (round(100 * v["realised"]["vt"], 1), round(100 * v["realised_sd"]["vt"], 1)) == (10.1, 0.6)
    assert (round(100 * v["raw"][1], 2), round(100 * v["vt"][1], 2)) == (7.54, 4.07)
    assert [round(100 * x, 1) for x in v["raw_iv"]] == [21.6, 19.0, 16.8]
    assert [round(100 * x, 1) for x in v["vt_iv"]] == [10.6, 10.2, 9.9]
    d = decrement_example()
    assert (round(100 * d["fwd_price"], 1), round(100 * d["fwd_dec"], 1)) == (100.0, 90.5)
    assert (round(100 * d["put_price"], 1), round(100 * d["put_dec"], 1), round(100 * (d["put_dec"] / d["put_price"] - 1))) == (15.2, 19.0, 24)
    assert abs(d["dec_path"][-1] - d["fwd_dec"]) < 1e-3


def test_exercises():
    assert (round(zero_coupon(2, R, 0.0), 2), round(zero_coupon(2, R, 0.024), 2)) == (94.18, 89.76)
    assert round(zero_coupon(2, R, 0.0) - zero_coupon(2, R, 0.024), 2) == 4.41
    assert round((100 - 0.95 * zero_coupon(2, R, 0.0) - 1.5), 2) == 9.03
    assert round(100 * (100 - 0.95 * zero_coupon(2, R, 0.0) - 1.5) / N["call"], 1) == 72.3
    u = 100 * bs(1.0, 1.0, 2.0, R, Q, 0.10, "C")
    assert round(u, 2) == 6.94 and round(100 * (100 - zero_coupon(2, R, 0) - 1.5) / u) == 62
    assert math.isclose(N["p_at_0"], PC[0])
