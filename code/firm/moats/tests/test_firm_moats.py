import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_moats as fm  # noqa: E402


def test_hhi_and_ratios():
    assert fm.hhi([1.0]) == pytest.approx(10_000) and fm.hhi([0.2] * 5) == pytest.approx(2_000)
    assert fm.cr([3, 1, 1, 1], 1) == pytest.approx(0.5)


def test_bounds_bracket_every_feasible_vector():
    lo, hi = fm.hhi_bounds(6, 0.66, 2)
    rng = __import__("numpy").random.default_rng(3)
    for _ in range(2000):
        top = rng.uniform(0.33, 0.66)
        rest = rng.dirichlet([1] * 4) * 0.34
        v = [top, 0.66 - top] + list(rest)
        if max(rest) <= min(top, 0.66 - top):
            assert lo - 1e-6 <= fm.hhi(v) <= hi + 1e-6
    with pytest.raises(ValueError):
        fm.hhi_bounds(3, 0.2, 2)


def test_free_entry_and_planner():
    S = 3000.0
    for F in (5.0, 20.0, 50.0, 300.0):
        n = fm.free_entry(S, F)
        assert S / (n + 1) ** 2 >= F > S / (n + 2) ** 2
        assert fm.planner(S, F) <= n                                    # excess entry in this model


def test_cournot_merger_and_synergy():
    a, b, c = 10.0, 0.012, [4.0] * 6
    x = fm.cournot(a, b, c)
    assert x["price"] == pytest.approx((a + 24) / 7) and x["shares"].sum() == pytest.approx(1)
    assert fm.merge(a, b, c, 0, 1)["price"] > x["price"]
    d = fm.synergy_for_price(a, c, 0, 1)
    assert fm.merge(a, b, c, 0, 1, d)["price"] == pytest.approx(x["price"])
    with pytest.raises(ValueError):
        fm.cournot(a, b, [4.0, 9.9, 9.9])
    assert [s[1] for s in fm.scenarios(3000.0, [25.0, 50.0, 100.0])] == [9, 6, 4]
