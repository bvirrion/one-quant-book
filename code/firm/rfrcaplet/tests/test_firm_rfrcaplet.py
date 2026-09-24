"""Acceptance tests of the Book 6, chapter 10 build (backward-looking caplets)."""
import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_rfrcaplet import (
    gfmm_effective_variance,
    hw_backward_caplet,
    hw_backward_caplet_mc,
    hw_forward_caplet,
    hw_period_variances,
    meeting_variance,
)


class Flat:
    def df_t(self, t):
        return math.exp(-0.03 * t)


def test_backward_exceeds_forward_by_the_in_period_variance():
    b, d = hw_period_variances(0.03, 0.009, 1.0, 1.25)
    assert d > 0 and b > 0
    assert hw_backward_caplet(Flat(), 0.03, 0.009, 1.0, 1.25, 0.031) > hw_forward_caplet(Flat(), 0.03, 0.009, 1.0,
                                                                                          1.25, 0.031)
    b0, d0 = hw_period_variances(0.03, 0.009, 1e-9, 0.25)
    assert b0 < 1e-12 and d0 == pytest.approx(0.009**2 * 0.25**3 / 3, rel=0.01)


def test_closed_form_matches_monte_carlo_on_an_aligned_grid():
    cf = hw_backward_caplet(Flat(), 0.03, 0.009, 0.5, 0.75, 0.032)
    mc, se = hw_backward_caplet_mc(Flat(), 0.03, 0.009, 0.5, 0.75, 0.032, paths=40000, steps_per_year=260)
    assert abs(mc - cf) < 3 * se
    with pytest.raises(ValueError):
        hw_backward_caplet_mc(Flat(), 0.03, 0.009, 1.0, 1.25, 0.032, paths=10, steps_per_year=250)


def test_gfmm_and_meeting_variances():
    assert gfmm_effective_variance(0.2, 1.0, 1.25) == pytest.approx(0.04 * (1.0 + 0.25 / 3))
    assert gfmm_effective_variance(0.2, 1.0, 1.25, t=1.25) == 0.0
    assert meeting_variance([0.5, 1.1], 0.01, 1.0, 1.25) == pytest.approx(0.01**2 + (0.01 * 0.15 / 0.25) ** 2)
    assert meeting_variance([0.5, 1.1], 0.01, 1.0, 1.25, t=1.2) == 0.0
