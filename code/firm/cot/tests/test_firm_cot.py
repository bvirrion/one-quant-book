"""Acceptance tests of the Book 3, Chapter 9 build (positioning and limits)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_cot import crush_margin, limit_path, net, net_share, variable_limit, zscore


def test_net_positions():
    r = {"open_interest": 1000, "mm_long": 300, "mm_short": 100}
    assert net(r, "mm") == 200 and net_share(r, "mm") == 0.2


def test_zscore_window():
    z = zscore([1.0, 2.0, 3.0, 10.0], 3)
    assert z[:3] == [None, None, None] and math.isclose(z[3], (10 - 2) / 1.0)


def test_variable_limit_rule():
    assert variable_limit(4.50) == (0.30, 0.45)          # 31.5 cents rounds to 30
    assert variable_limit(2.00) == (0.20, 0.30)          # the 20-cent floor
    assert variable_limit(6.00) == (0.40, 0.60)          # 42 cents rounds to 40


def test_limit_lock_sequence():
    path = limit_path(4.50, 3.70, 0.30, 0.45)
    assert [d.locked for d in path[:3]] == [True, True, False]
    assert [d.settle for d in path[:3]] == [4.20, 3.75, 3.70]


def test_crush():
    assert math.isclose(crush_margin(10.00, 300.0, 50.0), 6.6 + 5.5 - 10.0)
