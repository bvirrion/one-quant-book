"""Acceptance tests of the Book 6, chapter 4 build (caps, floors, swaptions)."""
import datetime as dt
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "curvebuild"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "multicurve"))
from firm_capfloor import (
    Cap,
    cap_price,
    caplets,
    cash_annuity,
    forward_swap,
    piecewise,
    strip_caplet_vols,
    swaption_physical,
)
from firm_curvebuild import Swap, calibrate
from firm_multicurve import Fixing, IborSwap, add_months, calibrate_projection

SPOT = dt.date(2026, 9, 29)
YEARS = [1, 2, 3, 5, 7, 10, 15]
DISC = calibrate(SPOT, [Swap(SPOT, n, 0.02 + 0.0006 * n) for n in YEARS], "monotone_convex").curve
PROJ = calibrate_projection(SPOT, DISC, [Fixing(SPOT, add_months(SPOT, 6), 0.022)] +
                            [IborSwap(SPOT, n, 0.0215 + 0.0006 * n) for n in YEARS])


def test_zero_vol_is_intrinsic_and_cap_minus_floor_is_a_swap():
    cap, flo = Cap(SPOT, 5, 0.025), Cap(SPOT, 5, 0.025, floor=True)
    intrinsic = sum(max(c["fwd"] - 0.025, 0) * c["delta"] * c["df"] for c in caplets(cap, PROJ, DISC))
    assert cap_price(cap, PROJ, DISC, 1e-9) == pytest.approx(intrinsic, abs=1e-12)
    swap = sum((c["fwd"] - 0.025) * c["delta"] * c["df"] for c in caplets(cap, PROJ, DISC))
    assert cap_price(cap, PROJ, DISC, 0.008) - cap_price(flo, PROJ, DISC, 0.008) == pytest.approx(swap, abs=1e-12)


def test_stripped_vols_reprice_every_cap():
    mats, flats = [1, 2, 3, 5, 7], [0.006, 0.0068, 0.0074, 0.0077, 0.0075]
    f = piecewise(strip_caplet_vols(SPOT, mats, flats, 0.03, PROJ, DISC))
    for m, v in zip(mats, flats, strict=True):
        cap = Cap(SPOT, m, 0.03)
        assert cap_price(cap, PROJ, DISC, f) == pytest.approx(cap_price(cap, PROJ, DISC, v), rel=1e-8)


def test_payer_minus_receiver_is_the_forward_swap():
    ex = dt.date(2029, 9, 29)
    s, a = forward_swap(PROJ, DISC, ex, 5)
    k = s + 0.004
    d = swaption_physical(ex, 5, k, PROJ, DISC, 0.008) - swaption_physical(ex, 5, k, PROJ, DISC, 0.008, payer=False)
    assert d == pytest.approx(a * (s - k), abs=1e-12)
    assert swaption_physical(ex, 5, s, PROJ, DISC, 0.008, model="lognormal") > 0


def test_cash_annuity():
    assert cash_annuity(0.0, 10) == pytest.approx(10.0)
    assert cash_annuity(0.03, 10) == pytest.approx((1 - 1.03**-10) / 0.03)
    assert cash_annuity(0.05, 10) < cash_annuity(0.03, 10)
