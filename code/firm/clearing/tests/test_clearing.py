"""Acceptance tests of the Chapter 5 build."""
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_clearing import ClearedTrade, NettingEngine


def example():
    e = NettingEngine()
    e.add(ClearedTrade("t1", "A", "B", "XYZ", 5000, 200_000))
    e.add(ClearedTrade("t2", "B", "C", "XYZ", 3000, 201_000))
    e.add(ClearedTrade("t3", "C", "A", "XYZ", 4000, 199_500))
    return e


def test_reproduces_the_chapter_example_exactly():
    s = example().close()
    assert s.shares[("A", "XYZ")] == 1000 and s.cash[("A", "USD")] == -202_000_000
    assert s.shares[("B", "XYZ")] == -2000 and s.cash[("B", "USD")] == 397_000_000
    assert s.shares[("C", "XYZ")] == 1000 and s.cash[("C", "USD")] == -195_000_000


def test_each_trade_id_appears_for_exactly_two_members():
    s = example().close()
    ids = [i for v in s.netted.values() for i in v]
    assert sorted(ids) == ["t1", "t1", "t2", "t2", "t3", "t3"]


def test_invariants_on_ten_thousand_random_trades():
    rng, e = np.random.default_rng(5), NettingEngine()
    for k in range(10_000):
        b, s = rng.choice(12, size=2, replace=False)
        e.add(ClearedTrade(f"t{k}", f"M{b}", f"M{s}", f"S{rng.integers(30)}",
                           int(rng.integers(1, 50)) * 100, int(rng.integers(100_000, 900_000))))
    out = e.close()
    assert sum(out.cash.values()) == 0 and sum(out.shares.values()) == 0


def test_rejections_and_closed_session():
    e = example()
    for bad in (ClearedTrade("x", "A", "A", "XYZ", 1, 1), ClearedTrade("y", "A", "B", "XYZ", 0, 1),
                ClearedTrade("t1", "A", "B", "XYZ", 1, 1)):
        with pytest.raises(ValueError):
            e.add(bad)
    e.close()
    with pytest.raises(RuntimeError):
        e.add(ClearedTrade("z", "A", "B", "XYZ", 1, 1))
