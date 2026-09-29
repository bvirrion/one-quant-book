import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_techtier as tt  # noqa: E402

TIERS = [tt.Tier("slow", 0.0, 1.0), tt.Tier("mid", 0.0, 2.0), tt.Tier("fast", 0.0, 5.0)]


def test_revenue_splits_the_pool():
    s = tt.Strategy("x", 50.0, 0.8)
    prof = [2, 2, 1, 0]
    total = sum(tt.revenue(s, prof[i], prof[:i] + prof[i + 1:]) for i in range(4))
    assert abs(total - 50.0) < 1e-12
    assert tt.revenue(s, 2, [2, 1, 0]) == pytest.approx(50.0 * (0.8 / 2 + 0.2 / 4))
    assert tt.revenue(s, 1, [2, 2, 0]) == pytest.approx(50.0 * 0.2 / 4)


def test_arms_race_and_waste():
    s = tt.Strategy("x", 20.0, 0.9)
    prof, _ = tt.arms_race(s, TIERS, 3)
    w = tt.waste(s, TIERS, 3)
    assert w["profile"] == sorted(prof, reverse=True) and w["baseline"] == 3.0
    for i in range(3):                                    # no firm gains by deviating
        others = prof[:i] + prof[i + 1:]
        assert tt.best_tier(s, TIERS, others)[0] == prof[i]
    assert w["wasted_share"] == pytest.approx((w["spend"] - 3.0) / w["spend"])


def test_colobill_fees_and_budget():
    fees = tt.colobill_venue_fees({"t": [("miax-pearl", [("conn_1g", 2)])]})
    assert fees["t"] == 36_000.0
    assert tt.run_change([("a", 3.0, "run"), ("b", 1.0, "change")]) == (3.0, 1.0, 0.75)
