"""Acceptance tests of the Chapter 30 build."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_futfees import (
    Access,
    IncentiveTier,
    ProductFees,
    breakeven_sides,
    cost_in_ticks,
    monthly_cost,
    per_side,
    with_incentive,
)

ES = ProductFees("ES", {"non_member": 1.18, "lessee": 0.47, "owner": 0.35}, {"non_member": 0.02, "lessee": 0.0, "owner": 0.0})
OUT, LEASE = Access("non_member", 0.25), Access("lessee", 0.10, 1_500.0)


def test_per_side_and_month():
    assert per_side(ES, OUT) == pytest.approx(1.45) and per_side(ES, LEASE) == pytest.approx(0.57)
    assert monthly_cost(ES, LEASE, 10_000) == pytest.approx(7_200) and monthly_cost(ES, OUT, 10_000) == pytest.approx(14_500)


def test_breakeven():
    assert breakeven_sides(ES, LEASE, OUT) == pytest.approx(1_500 / 0.88)
    assert breakeven_sides(ES, OUT, LEASE) is None                  # the dearer route never wins on variable cost
    assert breakeven_sides(ES, Access("lessee", 0.10, 0.0), OUT) == 0.0


def test_incentive_applies_to_the_whole_month():
    tiers = (IncentiveTier(50_000, 0.05), IncentiveTier(200_000, 0.10))
    assert with_incentive(ES, LEASE, 49_999, tiers) == pytest.approx(monthly_cost(ES, LEASE, 49_999))
    assert with_incentive(ES, LEASE, 50_000, tiers) == pytest.approx(monthly_cost(ES, LEASE, 50_000) - 2_500)


def test_fees_against_the_tick():
    assert cost_in_ticks(ES, OUT, 12.5) == pytest.approx(0.232) and cost_in_ticks(ES, LEASE, 12.5) == pytest.approx(0.0912)
