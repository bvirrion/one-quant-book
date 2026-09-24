"""Acceptance tests of the Chapter 8 build."""
import datetime as dt
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_corpactions import Action, Adjuster, split_position

D = dt.date


def test_continuity_through_a_split():
    adj = Adjuster()
    adj.add(Action("NVX", D(2024, 6, 10), "split", {"ratio": 10}, D(2024, 5, 22)))
    before = 1208.88 * adj.factor("NVX", D(2024, 6, 7), as_of=D(2024, 6, 10))
    assert before == pytest.approx(120.888)


def test_as_of_rule_hides_the_future():
    adj = Adjuster()
    adj.add(Action("NVX", D(2024, 6, 10), "split", {"ratio": 10}, D(2024, 5, 22)))
    assert adj.factor("NVX", D(2024, 1, 2), as_of=D(2024, 5, 1)) == 1.0      # not yet announced
    assert adj.factor("NVX", D(2024, 1, 2), as_of=D(2024, 6, 7)) == 1.0      # announced, not yet effective
    assert adj.factor("NVX", D(2024, 1, 2), as_of=D(2024, 6, 10)) == pytest.approx(0.1)


def test_split_leaves_the_cost_basis_unchanged():
    q, c = split_position(500, 1200.0, 10)
    assert (q, c) == (5000, 120.0) and q * c == 500 * 1200.0


def test_rights_example_one_for_four_at_six():
    adj = Adjuster()
    adj.add(Action("R", D(2026, 3, 4), "rights",
                   {"cum_price": 10.0, "old": 4, "new": 1, "subscription": 6.0}, D(2026, 2, 20)))
    assert adj.factor("R", D(2026, 3, 3), as_of=D(2026, 3, 4)) == pytest.approx(0.92)


def test_rejects_nonsense():
    with pytest.raises(ValueError):
        Adjuster().add(Action("X", D(2026, 1, 5), "merger", {}, D(2026, 1, 1)))
    with pytest.raises(ValueError):
        Adjuster().add(Action("X", D(2026, 1, 5), "split", {"ratio": 2}, D(2026, 1, 6)))
