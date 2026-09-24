"""Acceptance tests of the Book 2, Chapter 6 build: the exchange's published conversion factors."""
import datetime as dt
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_ctd import Deliverable, cheapest_to_deliver, conversion_factor, implied_repo, net_basis, whole_months

D = dt.date


@pytest.mark.parametrize("coupon, first, maturity, quarter, expected", [
    (0.015, D(2008, 12, 1), D(2010, 10, 31), False, 0.9229),     # 2-year example
    (0.01125, D(2009, 3, 1), D(2012, 1, 15), False, 0.8747),     # 3-year example
    (0.0275, D(2008, 12, 1), D(2013, 10, 31), False, 0.8653),    # 5-year example
    (0.0375, D(2008, 12, 1), D(2018, 11, 15), True, 0.8357),     # 10-year example
    (0.045, D(2008, 12, 1), D(2038, 5, 15), True, 0.7943),       # bond example
])
def test_published_conversion_factors(coupon, first, maturity, quarter, expected):
    assert conversion_factor(coupon, first, maturity, quarter) == expected


def test_whole_months():
    assert whole_months(D(2008, 12, 1), D(2010, 10, 31)) == 22
    assert whole_months(D(2008, 12, 1), D(2018, 11, 15)) == 119


def test_six_percent_bond_has_factor_one():
    assert conversion_factor(0.06, D(2026, 12, 1), D(2033, 12, 1)) == 1.0


def test_implied_repo_and_net_basis_agree_on_the_ctd():
    a = Deliverable("A", 95.0, 1.0, 2.0, 0.90)
    b = Deliverable("B", 99.0, 1.0, 2.0, 0.94)
    f, days = 105.0, 90
    ctd = cheapest_to_deliver([a, b], f, days)
    r = implied_repo(ctd, f, days)
    assert net_basis(ctd, f, r, days) == pytest.approx(0.0, abs=1e-12)
    other = b if ctd is a else a
    assert net_basis(other, f, r, days) > 0
