"""Acceptance tests of the Book 2, Chapter 1 build (overnight-rate compounding)."""
import datetime as dt
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_rfr import (
    Calendar,
    Convention,
    compound_in_arrears,
    observations,
    rate_from_index,
    simple_average,
    weights,
)

D = dt.date
CAL = Calendar(frozenset({D(2026, 9, 7)}))


def flat(rate):
    out, d = {}, D(2026, 7, 1)
    while d < D(2026, 12, 31):
        out[d] = rate
        d += dt.timedelta(days=1)
    return out


def test_friday_counts_three_days():
    days = CAL.business_days(D(2026, 9, 3), D(2026, 9, 10))   # Thu, Fri, (Mon holiday), Tue, Wed
    assert days == [D(2026, 9, 3), D(2026, 9, 4), D(2026, 9, 8), D(2026, 9, 9)]
    assert weights(CAL, days, D(2026, 9, 10)) == [1, 4, 1, 1]


def test_flat_rate_compounds_to_the_textbook_formula():
    r, start, end = 0.04, D(2026, 9, 1), D(2026, 10, 1)
    days = CAL.business_days(start, end)
    w = weights(CAL, days, end)
    growth = 1.0
    for n in w:
        growth *= 1 + r * n / 360
    assert compound_in_arrears(flat(r), CAL, start, end) == pytest.approx((growth - 1) * 360 / 30)
    assert compound_in_arrears(flat(r), CAL, start, end) > r > 0
    assert simple_average(flat(r), CAL, start, end) == pytest.approx(r)


def test_lookback_uses_earlier_fixings_with_current_weights():
    obs = observations(CAL, D(2026, 9, 1), D(2026, 10, 1), Convention(lookback=5))
    assert obs[0] == (D(2026, 8, 25), 1)
    assert obs[-1] == (D(2026, 9, 23), 1)
    assert sum(n for _, n in obs) == 30


def test_observation_shift_takes_weights_from_the_shifted_period():
    obs = observations(CAL, D(2026, 9, 1), D(2026, 10, 1), Convention(lookback=5, shift=True))
    assert obs[0][0] == D(2026, 8, 25) and obs[-1][0] == D(2026, 9, 23)
    assert sum(n for _, n in obs) == (D(2026, 9, 24) - D(2026, 8, 25)).days


def test_lockout_freezes_the_last_fixings():
    obs = observations(CAL, D(2026, 9, 1), D(2026, 10, 1), Convention(lockout=2))
    assert [d for d, _ in obs[-3:]] == [D(2026, 9, 28)] * 3


def test_rate_from_index_matches_compounding():
    r, start, end = 0.035, D(2026, 9, 1), D(2026, 10, 1)
    days = CAL.business_days(start, end)
    idx = 1.0
    for n in weights(CAL, days, end):
        idx *= 1 + r * n / 360
    assert rate_from_index(1.0, idx, start, end) == pytest.approx(compound_in_arrears(flat(r), CAL, start, end))


def test_negative_rates_are_allowed():
    assert compound_in_arrears(flat(-0.005), CAL, D(2026, 9, 1), D(2026, 10, 1)) < 0
