"""Acceptance tests of the Book 2, Chapter 10 build (margin funding and the CCP basis)."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_ccpbasis import MarginModel, annuity_remaining, basis_bp, dv01_path, im_path, mva


def test_annuity_closed_form():
    r, n = 0.04, 10
    assert annuity_remaining(0.0, n, r) == pytest.approx((1 - (1 + r) ** -n) / r)
    assert annuity_remaining(9.5, n, r) == pytest.approx(1 / (1 + r) ** 0.5)


def test_margin_scales_with_dv01_and_decays():
    m = MarginModel()
    ims = [im for _, im in im_path(1e8, 10, 0.04, m)]
    assert all(a > b for a, b in zip(ims, ims[1:], strict=False) if a - b > 1e-6) and ims[0] > ims[-1] > 0
    assert ims[0] == pytest.approx(dv01_path(1e8, 10, 0.04, 0.25)[0][1] * m.im_per_dv01())


def test_mva_linear_in_funding_and_notional():
    m = MarginModel()
    a = mva(1e8, 10, 0.04, m, 0.005)
    assert mva(2e8, 10, 0.04, m, 0.005) == pytest.approx(2 * a)
    assert mva(1e8, 10, 0.04, m, 0.010) == pytest.approx(2 * a)
    assert mva(1e8, 10, 0.04, m, 0.0) == 0.0


def test_basis_grows_with_maturity_and_ccps():
    m = MarginModel()
    b5, b10, b30 = (basis_bp(1e8, n, 0.04, m, 0.005) for n in (5, 10, 30))
    assert b5 < b10 < b30
    assert basis_bp(1e8, 10, 0.04, m, 0.005, ccps=2) == pytest.approx(2 * b10)
