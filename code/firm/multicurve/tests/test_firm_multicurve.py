"""Acceptance tests of the Book 6, chapter 2 build (discount and projection curves)."""
import datetime as dt
import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "curvebuild"))
from firm_curvebuild import Swap, calibrate
from firm_multicurve import (
    CollateralChoiceCurve,
    Fixing,
    IborSwap,
    ShiftedCurve,
    add_months,
    calibrate_projection,
    ibor_swap_pv,
    tenor_basis,
)

SPOT = dt.date(2026, 9, 29)
YEARS = [1, 2, 3, 5, 7, 10]
OIS = [0.0195, 0.0202, 0.0210, 0.0225, 0.0240, 0.0255]
IRS = [0.0215, 0.0221, 0.0228, 0.0242, 0.0256, 0.0270]


def disc():
    return calibrate(SPOT, [Swap(SPOT, n, r) for n, r in zip(YEARS, OIS, strict=True)], "monotone_convex").curve


def proj(d=None, irs=IRS):
    ins = [Fixing(SPOT, add_months(SPOT, 6), 0.0213)] + [IborSwap(SPOT, n, r) for n, r in zip(YEARS, irs, strict=True)]
    return calibrate_projection(SPOT, d or disc(), ins)


def test_projection_reprices_on_its_discount_curve():
    d = disc()
    p = proj(d)
    for n, r in zip(YEARS, IRS, strict=True):
        assert IborSwap(SPOT, n, 0.0).model(p, d) == pytest.approx(r, abs=1e-12)
        assert ibor_swap_pv(p, d, SPOT, n, r, 1e8) == pytest.approx(0.0, abs=1e-3)


def test_tenor_basis_is_the_par_rate_difference_with_identical_fixed_legs():
    d = disc()
    p = proj(d)
    for n, a, b in zip(YEARS, IRS, OIS, strict=True):
        assert tenor_basis(p, d, SPOT, n) == pytest.approx(a - b, abs=1e-10)


def test_no_basis_means_projection_equals_discount_forwards():
    d = disc()
    p = proj(d, irs=OIS)
    s, e = add_months(SPOT, 30), add_months(SPOT, 36)
    assert (p.df(s) / p.df(e)) == pytest.approx(d.df(s) / d.df(e), abs=2e-6)


def test_shifted_curve_and_payer_receiver_signs():
    d = disc()
    up = ShiftedCurve(d, 1e-4)
    t = 7.0
    assert up.df(SPOT + dt.timedelta(days=int(365 * t))) == pytest.approx(
        d.df(SPOT + dt.timedelta(days=int(365 * t))) * math.exp(-1e-4 * int(365 * t) / 365))
    p = proj(d)
    rec = ibor_swap_pv(p, d, SPOT, 10, 0.035, 1e8, payer=False)
    assert rec > 0 and ibor_swap_pv(p, d, SPOT, 10, 0.035, 1e8, payer=True) == pytest.approx(-rec)


def test_collateral_choice_never_raises_a_receivable_and_equals_max_rule():
    d = disc()
    c = CollateralChoiceCurve(d, [lambda t: 0.0, lambda t: 0.001 if t < 2 else -0.001])
    for t in (0.5, 1.0, 2.0, 5.0):
        assert c.df_t(t) <= d.df_t(t) + 1e-15
    assert c.df_t(5.0) == pytest.approx(d.df_t(5.0) * math.exp(-0.002), rel=1e-6)
    assert c.fwd_t(1.0) == pytest.approx(d.fwd_t(1.0) + 0.001)
    same = CollateralChoiceCurve(d, [lambda t: 0.0])
    assert same.df_t(3.3) == pytest.approx(d.df_t(3.3), rel=1e-12)


def test_add_months_end_of_month():
    assert add_months(dt.date(2027, 1, 31), 1) == dt.date(2027, 2, 28)
    assert add_months(dt.date(2026, 9, 29), 6) == dt.date(2027, 3, 29)
