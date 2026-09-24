"""Acceptance tests of the Book 6, chapter 1 build (multi-instrument curve builder)."""
import datetime as dt
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "curve"))
from firm_curve import bootstrap, schedule
from firm_curvebuild import KINDS, Deposit, Future, Swap, calibrate, imm_date, swap_pv, with_quote

SPOT = dt.date(2026, 9, 29)
YEARS = [1, 2, 3, 5, 7, 10, 15, 20, 30]
RATES = [0.0360, 0.0340, 0.0335, 0.0345, 0.0360, 0.0380, 0.0398, 0.0405, 0.0400]


def swaps(rates=RATES):
    return [Swap(SPOT, n, r, f"{n}Y") for n, r in zip(YEARS, rates, strict=True)]


def mixed():
    s = [imm_date(2026, 12), imm_date(2027, 3), imm_date(2027, 6)]
    return [Deposit(SPOT, dt.date(2026, 12, 29), 0.0358, "3M"), Future(s[0], s[1], 96.50, 2e-5, "F1"),
            Future(s[1], s[2], 96.62, 4e-5, "F2")] + swaps()[1:]


@pytest.mark.parametrize("kind", KINDS)
def test_every_instrument_reprices(kind):
    cal = calibrate(SPOT, mixed(), kind)
    assert cal.max_error < 1e-12 and cal.iterations <= 6
    for inst in mixed():
        assert inst.model(cal.curve) == pytest.approx(inst.quote(), abs=1e-12)


def test_flat_forward_on_swaps_is_book2_bootstrap():
    # Book 2's bisection bounds ln P in [-1, 0]: compare only up to 20 years, where P > 1/e.
    mine = calibrate(SPOT, swaps()[:-1], "flat_forward").curve
    theirs = bootstrap(SPOT, YEARS[:-1], RATES[:-1])
    for k in range(1, 27):
        d = SPOT + dt.timedelta(days=int(k * 365.25 * 0.75))
        assert mine.df(d) == pytest.approx(theirs.df(d), abs=1e-11)


@pytest.mark.parametrize("kind", KINDS)
def test_flat_par_quotes_give_a_flat_forward_curve(kind):
    c = calibrate(SPOT, swaps([0.04] * len(YEARS)), kind).curve
    f = [c.fwd_t(t) for t in np.arange(0.3, 29.7, 0.37)]
    assert max(f) - min(f) < 0.5e-4


def test_monotone_convex_forward_is_continuous_at_pillars():
    c = calibrate(SPOT, mixed(), "monotone_convex").curve
    for t in c.times[:-1]:
        assert c.fwd_t(t - 1e-7) == pytest.approx(c.fwd_t(t + 1e-7), abs=1e-6)


def test_local_schemes_have_a_lower_triangular_jacobian():
    for kind in ("linear_zero", "flat_forward"):
        jac = calibrate(SPOT, mixed(), kind).jacobian
        assert np.max(np.abs(np.triu(jac, 1))) < 1e-9
    assert np.max(np.abs(np.triu(calibrate(SPOT, mixed(), "cubic_zero").jacobian, 1))) > 1e-3


def test_a_bump_spreads_further_under_a_cubic_spline():
    ins = swaps()
    up = list(ins)
    up[4] = with_quote(ins[4], ins[4].quote() + 1e-4)            # 7Y

    def far(kind):
        a, b = calibrate(SPOT, ins, kind).curve, calibrate(SPOT, up, kind).curve
        return max(abs(b.fwd_t(t) - a.fwd_t(t)) for t in np.arange(15.5, 29.5, 0.5))
    assert far("flat_forward") < 0.02e-4 < far("cubic_zero")


def test_bumped_curve_protocol_and_payer_sign():
    c = calibrate(SPOT, mixed(), "monotone_convex").curve
    k = Swap(SPOT, 10, 0.0).model(c)
    up = c.bumped(None, 1e-4)
    assert all(b - a == pytest.approx(1e-4) for a, b in zip(c.zeros, up.zeros, strict=True))
    one = c.bumped("10Y", 1e-4)
    assert sum(abs(b - a) > 0 for a, b in zip(c.zeros, one.zeros, strict=True)) == 1
    assert swap_pv(up, SPOT, 10, k, 1e8) > 0 > swap_pv(up, SPOT, 10, k, 1e8, payer=False)
    assert swap_pv(c, SPOT, 10, k, 1e8) == pytest.approx(0.0, abs=1e-4)
    assert len(schedule(SPOT, 10)) == 11


def test_imm_dates_and_bad_order():
    assert imm_date(2026, 12) == dt.date(2026, 12, 16) and imm_date(2027, 3) == dt.date(2027, 3, 17)
    with pytest.raises(ValueError):
        calibrate(SPOT, [Swap(SPOT, 2, 0.03), Swap(SPOT, 1, 0.03)])
