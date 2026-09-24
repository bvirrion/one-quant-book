"""Acceptance tests of the Book 6, chapter 6 build (timing, CMS replication, quanto, spread options)."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_cms import (
    cms_caplet,
    cms_rate,
    cms_rate_hagan,
    cms_spread_option,
    linear_tsr,
    otm_integral,
    quanto_adjustment_normal,
    timing_adjustment_black,
    timing_adjustment_normal,
)

ACC = [1.0139] * 10
A0, DFP, F, T = 7.9, 0.93, 0.031, 5.0


def test_replication_with_a_flat_smile_is_the_closed_form():
    flat = lambda k: 0.0080  # noqa: E731
    assert otm_integral(F, T, flat) == pytest.approx(0.0080**2 * T / 2, rel=1e-4)
    assert cms_rate(F, T, A0, DFP, ACC, flat) == pytest.approx(cms_rate_hagan(F, T, 0.008, A0, DFP, ACC), abs=5e-7)


def test_no_slope_in_the_annuity_mapping_means_no_adjustment():
    a0, _ = linear_tsr(A0, DFP, F, ACC)
    flat_dfp = a0 * A0                                   # P/A equals a0: a1 = 0
    assert cms_rate(F, T, A0, flat_dfp, ACC, lambda k: 0.009) == pytest.approx(F, abs=1e-12)


def test_deep_in_the_money_cms_caplet_is_the_discounted_cms_forward():
    sm = lambda k: 0.0075  # noqa: E731
    k = F - 0.08
    assert cms_caplet(k, F, T, A0, DFP, ACC, sm) == pytest.approx(DFP * (cms_rate(F, T, A0, DFP, ACC, sm) - k),
                                                                  rel=1e-4)


def test_timing_quanto_and_spread():
    assert timing_adjustment_black(0.03, 0.5, 5, 0.25) == pytest.approx(timing_adjustment_normal(0.03, 0.5, 5, 0.0075))
    assert timing_adjustment_normal(0.03, 0.5, 5, 0.0075) > 0
    assert quanto_adjustment_normal(0.0075, 0.08, 0.3, 5.0) == pytest.approx(-0.0009)
    assert cms_spread_option(0.035, 0.030, 0.0, 2.0, 0.008, 0.008, 1.0, 0.95) == pytest.approx(0.95 * 0.005)
    lo = cms_spread_option(0.035, 0.030, 0.0, 2.0, 0.008, 0.008, 0.9, 0.95)
    hi = cms_spread_option(0.035, 0.030, 0.0, 2.0, 0.008, 0.008, 0.5, 0.95)
    assert lo < hi
