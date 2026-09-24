"""Acceptance tests of the Book 6, chapter 13 build (hazard curves and default swaps)."""
import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "cds"))
from firm_cds import Cds, hazard_from_spread
from firm_cdscurve import (
    HazardCurve,
    bootstrap,
    bucketed_cs01,
    cds_value,
    jump_to_default,
    par_spread,
    risky_bond,
    standard_upfront,
)


class Flat:
    def __init__(self, r):
        self.r = r

    def df_t(self, t):
        return math.exp(-self.r * t)


D = Flat(0.03)
T, S = [1.0, 3.0, 5.0, 10.0], [0.006, 0.009, 0.012, 0.015]


def test_bootstrap_reprices_every_quote():
    c = bootstrap(D, T, S)
    for t, s in zip(T, S, strict=True):
        assert par_spread(c, D, t) == pytest.approx(s, abs=1e-12)


def test_one_tenor_is_book2_flat_hazard():
    c = bootstrap(D, [5.0], [0.012])
    assert c.hazards[0] == pytest.approx(hazard_from_spread(Cds(5.0, 0.01), 0.012, 0.03), rel=1e-9)


def test_standard_upfront_bond_and_jump_to_default():
    assert standard_upfront(5.0, 0.01, 0.01, 0.03) == pytest.approx(0.0, abs=1e-12)
    assert standard_upfront(5.0, 0.02, 0.01, 0.03) > 0
    riskless = risky_bond(HazardCurve([10.0], [0.0]), D, 5.0, 0.05)
    assert riskless == pytest.approx(sum(0.025 * D.df_t(k / 2) for k in range(1, 11)) + D.df_t(5.0))
    assert jump_to_default(0.01, 1.0, 0.4, True) == pytest.approx(0.59)
    c = bootstrap(D, T, S)
    cs = bucketed_cs01(D, T, S, 0.4, lambda cv: cds_value(cv, D, 5.0, 0.01))
    assert cs[2] > 0 and abs(cs[3]) < 1e-12 and sum(cs) > 0
    assert cds_value(c, D, 5.0, 0.012) == pytest.approx(0.0, abs=1e-12)
