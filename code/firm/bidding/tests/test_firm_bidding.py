"""Acceptance tests of firm.bidding."""
import math
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_bidding import (  # noqa: E402
    common_value,
    expected_revenue_uniform,
    fp_bid,
    fp_bid_general,
    myerson_reserve,
    pab_bid,
    simulate,
    simulate_multiunit,
)


def test_bid_functions():
    v = np.array([0.2, 0.5, 0.9])
    assert np.allclose(fp_bid(v, 4), 0.75 * v)
    assert np.allclose(fp_bid_general(v, 4, lambda x: np.asarray(x)), 0.75 * v, atol=1e-6)
    # with a reserve, a bidder at the reserve bids the reserve; below it does not bid
    assert abs(fp_bid(0.5, 3, reserve=0.5) - 0.5) < 1e-15 and np.isnan(fp_bid(0.4, 3, reserve=0.5))
    # pay-as-bid, n = 5, k = 2: b(v) = v (3 - 2.4 v) / (4 - 3 v)
    assert np.allclose(pab_bid(v, 5, 2), v * (3 - 2.4 * v) / (4 - 3 * v), atol=1e-6)
    # k = 1 is the first-price auction
    assert np.allclose(pab_bid(v, 5, 1), fp_bid(v, 5), atol=1e-6)


def test_revenue_equivalence_and_reserve():
    rev = [simulate(f, 3, 400_000, 5)["revenue"] for f in ("first", "second", "english", "dutch")]
    assert all(abs(x - 0.5) < 0.002 for x in rev)
    assert abs(expected_revenue_uniform(3) - 0.5) < 1e-15
    assert abs(myerson_reserve(lambda x: x, lambda x: 1.0) - 0.5) < 1e-12
    assert abs(myerson_reserve(lambda x: x * x, lambda x: 2 * x) - 1 / math.sqrt(3)) < 1e-12
    assert abs(myerson_reserve(lambda x: x, lambda x: 1.0, seller_value=0.2) - 0.6) < 1e-12
    r = simulate("second", 2, 400_000, 6, reserve=0.5)
    assert abs(r["revenue"] - 5 / 12) < 0.002 and abs(r["sold"] - 0.75) < 0.003
    with pytest.raises(ValueError):
        simulate("candle", 2, 10, 1)


def test_multiunit_and_common_value():
    u = simulate_multiunit("uniform", 5, 2, 200_000, 3)
    p = simulate_multiunit("payasbid", 5, 2, 200_000, 3)
    assert abs(u["revenue"] - 1.0) < 0.004 and abs(p["revenue"] - 1.0) < 0.004
    assert u["revenue_sd"] > 2 * p["revenue_sd"]
    with pytest.raises(ValueError):
        simulate_multiunit("dutch", 5, 2, 10, 1)
    c = common_value(5, 200_000, 2, noise=0.1)
    assert abs(c["profit"] + 0.1 * 4 / 6) < 0.001 and c["p_loss"] > 0.9
