"""Acceptance tests of the Book 2, Chapter 13 build (Bachelier, Black, quote conversion)."""
import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_normalvol import (
    atm_straddle,
    bachelier,
    black,
    black_to_normal,
    bp_per_day,
    implied,
    normal_to_black,
    normal_vega,
)

SQRT = math.sqrt(2 * math.pi)


def test_put_call_parity_both_models():
    for f, k in ((0.03, 0.035), (-0.002, 0.001)):
        assert math.isclose(bachelier(f, k, 2, 0.008) - bachelier(f, k, 2, 0.008, payer=False), f - k, abs_tol=1e-15)
    assert math.isclose(black(0.03, 0.035, 2, 0.3) - black(0.03, 0.035, 2, 0.3, payer=False), -0.005, abs_tol=1e-15)


def test_atm_closed_form_and_vega():
    assert math.isclose(bachelier(0.03, 0.03, 4, 0.01), 0.01 * 2 / SQRT, rel_tol=1e-12)
    assert math.isclose(atm_straddle(4, 0.01), 2 * 0.01 * 2 / SQRT, rel_tol=1e-12)
    h = 1e-7
    fd = (bachelier(0.03, 0.032, 3, 0.009 + h) - bachelier(0.03, 0.032, 3, 0.009 - h)) / (2 * h)
    assert math.isclose(normal_vega(0.03, 0.032, 3, 0.009), fd, rel_tol=1e-6)



def test_negative_rates():
    assert bachelier(-0.005, -0.004, 1, 0.005) > 0
    with pytest.raises(ValueError):
        black(-0.005, 0.001, 1, 0.3)
    with pytest.raises(ValueError):                  # 90 bp normal at a 0.25% forward: no Black vol
        normal_to_black(0.0025, 0.0025, 1, 0.009)


def test_round_trips():
    p = bachelier(0.025, 0.03, 5, 0.0095, 4.2)
    assert math.isclose(implied(p, 0.025, 0.03, 5, 4.2), 0.0095, rel_tol=1e-9)
    b = normal_to_black(0.04, 0.04, 1, 0.01)
    assert math.isclose(black_to_normal(0.04, 0.04, 1, b), 0.01, rel_tol=1e-8)
    # at the money the normal vol is close to Black vol times the forward
    assert abs(b * 0.04 - 0.01) < 1e-4


def test_quote_units():
    assert math.isclose(bp_per_day(0.01 * math.sqrt(252)), 100.0)
