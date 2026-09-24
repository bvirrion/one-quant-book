"""Acceptance tests of the Chapter 2 build."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_blockbid import quote


def test_reproduces_the_chapter_example():
    q = quote(2e6, 50.0, 1e7, 0.02)
    assert q.unwind_days == pytest.approx(2.0)
    assert round(q.discount * 100, 2) == 3.31
    assert q.bid == 48.34


def test_fully_hedged_block_is_priced_at_impact():
    q = quote(2e6, 50.0, 1e7, 0.02, hedge_ratio=1.0)
    assert q.discount == pytest.approx(q.impact)


def test_limits():
    with pytest.raises(ValueError):
        quote(2e6, 50.0, 1e7, 0.02, participation=0.5)
    with pytest.raises(ValueError):
        quote(6e7, 50.0, 1e7, 0.02)
