"""Acceptance tests of the Book 3, Chapter 14 build (fees and confirmations)."""
import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_gasfee import GWEI, confirmation_seconds, next_base_fee, project, tx_cost_usd

LIMIT = 30_000_000


def test_eip1559_bounds():
    b = 10 * GWEI
    assert next_base_fee(b, LIMIT, LIMIT) == b * 9 // 8                 # full block: +12.5%
    assert next_base_fee(b, 0, LIMIT) == b * 7 // 8                     # empty block: -12.5%
    assert next_base_fee(b, LIMIT // 2, LIMIT) == b                     # at target: unchanged
    assert next_base_fee(7, LIMIT // 2 + 1, LIMIT) == 8                 # increase is at least 1 wei


def test_projection_and_costs():
    path = project(10 * GWEI, [1.0] * 20, LIMIT)
    assert math.isclose(path[-1] / (10 * GWEI), 1.125**20, rel_tol=1e-6)
    assert math.isclose(tx_cost_usd(150_000, 100.0, 2.0, 3000.0), 150_000 * 102e-9 * 3000)
    assert confirmation_seconds("bitcoin") == 3600 and confirmation_seconds("ethereum") == 768
    with pytest.raises(ValueError):
        confirmation_seconds("dogecoin")
