"""Acceptance tests of the Book 6, chapter 7 build (Hull-White, Jamshidian, tree, Vasicek, G2++)."""
import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_shortrate import (
    HullWhite,
    HWTree,
    calibrate_coterminal,
    g2_correlation,
    implied_normal,
    normal_price,
    vasicek_bond,
)


class Flat:
    def __init__(self, r):
        self.r = r

    def df_t(self, t):
        return math.exp(-self.r * t)


class Sloped:
    def df_t(self, t):
        return math.exp(-(0.02 + 0.001 * t) * t)


def test_bonds_reprice_the_curve_and_options_satisfy_parity():
    m = HullWhite(Sloped(), 0.05, [0.009, 0.011], [3.0])
    assert m.bond(0.0, 7.0, 0.0) == pytest.approx(Sloped().df_t(7.0))
    c, p = m.zbo(4.0, 9.0, 0.85), m.zbo(4.0, 9.0, 0.85, call=False)
    assert c - p == pytest.approx(m.P0(9.0) - 0.85 * m.P0(4.0), abs=1e-14)


def test_jamshidian_payer_minus_receiver_is_the_forward_swap():
    m = HullWhite(Sloped(), 0.03, [0.008])
    ann, f = m.annuity_forward(5, 5)
    k = f + 0.003
    assert m.swaption(5, 5, k) - m.swaption(5, 5, k, payer=False) == pytest.approx(ann * (f - k), abs=1e-12)


def test_tree_reprices_bonds_and_converges_to_jamshidian():
    m = HullWhite(Sloped(), 0.03, [0.008])
    ann, f = m.annuity_forward(5, 5)
    exact = m.swaption(5, 5, f)
    errs = []
    for dt in (1 / 12, 1 / 48):
        tree = HWTree(Sloped(), 0.03, 0.008, 10.0, dt)
        assert tree.zero_bonds_at(0, int(round(10 / dt)))[tree.jmax] == pytest.approx(Sloped().df_t(10.0), rel=1e-12)
        errs.append(abs(tree.european_swaption(5, 5, f) - exact))
    assert errs[1] < errs[0] / 2 and errs[1] / exact < 2e-3


def test_piecewise_calibration_reprices_its_targets():
    vols = {1: 0.006, 2: 0.007, 3: 0.0075}
    m = calibrate_coterminal(Flat(0.025), 0.03, [1, 2, 3], 5, lambda e: vols[e])
    for e in (1, 2, 3):
        ann, f = m.annuity_forward(e, 5 - e)
        assert implied_normal(m.swaption(e, 5 - e, f), f, f, e, ann) == pytest.approx(vols[e], abs=2e-7)
    assert normal_price(0.03, 0.03, 1.0, 0.01, 1.0) == pytest.approx(0.01 / math.sqrt(2 * math.pi))


def test_vasicek_and_g2():
    assert vasicek_bond(0.03, 1e-9, 0.1, 0.03, 0.01) == pytest.approx(1.0)
    assert vasicek_bond(0.02, 5, 0.1, 0.03, 0.01) > vasicek_bond(0.04, 5, 0.1, 0.03, 0.01)
    long = -math.log(vasicek_bond(0.03, 400, 0.1, 0.03, 0.01)) / 400
    assert long == pytest.approx(0.03 - 0.01**2 / (2 * 0.1**2), abs=2e-4)
    assert g2_correlation(2, 10, 0.02, 0.5, 0.0075, 0.0, -0.8) == pytest.approx(1.0)
    assert g2_correlation(2, 10, 0.02, 0.5, 0.0075, 0.009, -0.8) < 0.8
