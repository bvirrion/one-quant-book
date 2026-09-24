"""Acceptance tests of the Book 5, Chapter 19 build (structured-product term sheets)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_termsheet import (
    decrement_index,
    max_participation,
    protected_note,
    reverse_convertible_coupon,
    spread_for_participation,
    value,
    vol_target_index,
    zero_coupon,
)


def flat(v):
    return lambda k: v


def test_budget_identity_and_inverse():
    t, r, q, s, m = 2.0, 0.03, 0.015, 0.012, 1.5
    p = max_participation(t, r, s, q, flat(0.2), m)
    assert abs(value(protected_note(t, p), r, s, q, flat(0.2)) + m - 100.0) < 1e-10
    assert abs(spread_for_participation(p, t, r, q, flat(0.2), m) - s) < 1e-12
    assert max_participation(t, r, s + 0.005, q, flat(0.2), m) > p          # a weaker issuer can offer more
    capped = max_participation(t, r, s, q, flat(0.2), m, cap=1.2)
    assert capped > p


def test_zero_coupon_and_reverse_convertible():
    assert abs(zero_coupon(1.0, 0.03, 0.0) - 100 * math.exp(-0.03)) < 1e-12
    c1 = reverse_convertible_coupon(1.0, 0.03, 0.01, 0.015, flat(0.2), 0.9, 1.5)
    c2 = reverse_convertible_coupon(1.0, 0.03, 0.02, 0.015, flat(0.2), 0.9, 1.5)
    c3 = reverse_convertible_coupon(1.0, 0.03, 0.01, 0.015, flat(0.3), 0.9, 1.5)
    assert 0 < c1 < c2 and c1 < c3


def test_indices():
    rng = np.random.default_rng(1)
    rets = 0.3 * math.sqrt(1 / 252) * rng.standard_normal((2000, 504))
    vt = vol_target_index(rets, 0.10, lam=0.97)
    realised = np.std(np.log(vt[:, 253:] / vt[:, 252:-1]), axis=1).mean() * math.sqrt(252)
    assert abs(realised - 0.10) < 0.01
    tr = np.exp(0.03 * np.arange(0, 1261) / 252)[None, :]
    dec = decrement_index(tr, 0.05)[0]
    assert abs(dec[-1] / 100 - math.exp(-0.02 * 5)) < 1e-3
    pts = decrement_index(np.ones((1, 253)), 0.0, points=50.0, base=1000.0)[0]
    assert abs(pts[-1] - (1000 - 50 * 252 / 252)) < 1e-9
