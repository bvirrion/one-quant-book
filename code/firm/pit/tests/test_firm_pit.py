"""Acceptance tests of firm.pit."""
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_pit import Guard, LookAheadError, Store, asof_join


def _store():
    s = Store()
    s.put("US", "payrolls", "2008-09", "2008-10", -159)      # first release
    s.put("US", "payrolls", "2008-09", "2008-11", -284)      # second
    s.put("US", "payrolls", "2008-09", "2008-12", -403)      # third
    s.put("US", "payrolls", "2008-10", "2008-11", -240)
    return s


def test_asof_follows_knowledge_time():
    s = _store()
    assert s.asof("US", "payrolls", "2008-09", "2008-09") is None
    assert s.asof("US", "payrolls", "2008-09", "2008-10") == -159
    assert s.asof("US", "payrolls", "2008-09", "2008-11-15") == -284
    assert s.first("US", "payrolls", "2008-09") == ("2008-10", -159)
    assert [v for _, v in s.vintages("US", "payrolls", "2008-09")] == [-159, -284, -403]


def test_snapshot_is_a_vintage_and_latest_is_today():
    s = _store()
    assert s.snapshot("US", "payrolls", "2008-11") == {"2008-09": -284, "2008-10": -240}
    assert s.latest("US", "payrolls") == {"2008-09": -403, "2008-10": -240}


def test_same_knowledge_time_replaces():
    s = _store()
    s.put("US", "payrolls", "2008-09", "2008-10", -160)
    assert s.first("US", "payrolls", "2008-09") == ("2008-10", -160) and len(s.vintages("US", "payrolls", "2008-09")) == 3


def test_guard_refuses_the_future():
    g = Guard(_store(), "2008-11")
    assert g.asof("US", "payrolls", "2008-09") == -284
    with pytest.raises(LookAheadError):
        g.asof("US", "payrolls", "2008-09", known="2008-12")


def test_asof_join():
    right_t, right_v = [1.0, 2.0, 5.0], [10.0, 20.0, 50.0]
    out = asof_join([0.5, 1.0, 4.0, 9.0], right_t, right_v)
    assert np.isnan(out[0]) and list(out[1:]) == [10.0, 20.0, 50.0]
    strict = asof_join([1.0, 2.0], right_t, right_v, strict=True)
    assert np.isnan(strict[0]) and strict[1] == 10.0
    tol = asof_join([4.0, 9.0], right_t, right_v, tolerance=2.5)
    assert tol[0] == 20.0 and np.isnan(tol[1])
