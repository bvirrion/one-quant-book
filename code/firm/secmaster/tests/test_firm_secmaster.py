"""Acceptance tests of firm.secmaster."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_secmaster import SecurityMaster, buffered_universe, churn


def _master():
    m = SecurityMaster()
    m.list(1, "FB", "2012-05-18")
    m.rename(1, "META", "2022-06-09")
    m.list(2, "GM", "1990-01-02")
    m.delist(2, "2009-06-01", "performance", ret=-0.9)
    m.list(3, "GM", "2010-11-18")
    return m


def test_ticker_change_is_as_of():
    m = _master()
    assert m.resolve("FB", "2022-06-08") == 1 and m.resolve("FB", "2022-06-09") is None
    assert m.ticker(1, "2022-06-08") == "FB" and m.ticker(1, "2022-06-09") == "META"
    assert m.spans(1) == [("2012-05-18", "2022-06-09", "FB"), ("2022-06-09", None, "META")]


def test_reuse_and_delisting():
    m = _master()
    assert m.resolve("GM", "2009-06-01") == 2 and m.resolve("GM", "2009-06-02") is None
    assert m.resolve("GM", "2011-01-03") == 3 and m.reused() == {"GM": [2, 3]}
    assert m.delisting(2) == ("2009-06-01", "performance", -0.9) and m.ticker(2, "2010-01-04") is None
    assert m.listed("2011-01-03") == {3} and m.listed("2013-01-02") == {1, 3}


def test_a_held_ticker_cannot_be_given_twice():
    m = _master()
    with pytest.raises(ValueError):
        m.list(4, "META", "2023-01-03")
    with pytest.raises(ValueError):
        m.list(1, "XYZ", "2023-01-03")


def test_buffer_lowers_churn():
    import numpy as np

    rng = np.random.default_rng(0)
    level = rng.normal(0, 1, 400)
    paths = level + np.cumsum(rng.normal(0, 0.15, (60, 400)), axis=0)

    def scores(t):
        return {i: float(paths[t, i]) for i in range(400)}

    plain = buffered_universe(range(60), scores, 100)
    buf = buffered_universe(range(60), scores, 100, exit_rank=130)
    assert all(len(u) == 100 for u in plain.values()) and all(len(u) == 100 for u in buf.values())
    assert churn(buf) < 0.6 * churn(plain)
