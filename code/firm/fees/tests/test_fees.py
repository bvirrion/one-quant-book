"""Acceptance tests of the Chapter 3 build."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_fees import FeeTerms, InvestorState, accrue

PATH = [0.20, -0.15, 0.10, 0.25, -0.05, 0.08, 0.30, -0.20, 0.15, 0.12]


def run(terms, path):
    s, m, p = InvestorState(), 0.0, 0.0
    for g in path:
        s, a, b = accrue(terms, s, g)
        m, p = m + a, p + b
    return s, m, p


def test_reproduces_the_tutorial_path():
    s, m, p = run(FeeTerms(), PATH)
    assert s.nav == pytest.approx(1.451555, abs=1e-6)
    assert m == pytest.approx(0.234259, abs=1e-6) and p == pytest.approx(0.124289, abs=1e-6)


def test_no_performance_fee_under_the_mark():
    s, _, p1 = accrue(FeeTerms(mgmt=0.0), InvestorState(), 0.30)
    s, _, p2 = accrue(FeeTerms(mgmt=0.0), s, -0.20)
    s, _, p3 = accrue(FeeTerms(mgmt=0.0), s, 0.10)
    assert (p1, p2, p3) == (pytest.approx(0.06), 0.0, 0.0)


def test_two_investors_two_marks():
    late = accrue(FeeTerms(), InvestorState(), 0.15)[2]
    early_state = InvestorState(nav=1.1678, high_water=1.4972)
    assert late == pytest.approx(0.026) and accrue(FeeTerms(), early_state, 0.15)[2] == 0.0


def test_quarterly_flat_fund_pays_the_annual_management_fee():
    s, m, p = run(FeeTerms(periods_per_year=4), [0.0] * 4)
    assert p == 0.0 and m == pytest.approx(0.02, rel=0.02)


def test_hurdle_raises_the_mark():
    _, _, with_h = accrue(FeeTerms(mgmt=0.0, hurdle=0.04), InvestorState(), 0.10)
    assert with_h == pytest.approx(0.20 * 0.06)
