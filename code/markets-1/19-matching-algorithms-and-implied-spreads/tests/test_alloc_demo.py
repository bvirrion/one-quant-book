import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from alloc_demo import EXAMPLE, compare, expected_fill_by_position, fill_vs_size


def test_three_rules_three_outcomes():
    r = compare(EXAMPLE, 100)
    assert r["fifo"] == {"A": 10, "B": 90}
    assert r["pro_rata"] == {"A": 2, "B": 40, "C": 8, "D": 50}
    assert sum(r["split"].values()) == 100 and r["split"]["A"] == 10 and r["split"]["C"] >= 10


def test_showing_more_gets_more_under_pro_rata():
    fills = dict(fill_vs_size(range(0, 401, 50), 1000, 100))
    assert fills[0] == 0 and fills[50] == 4 and fills[400] == 28
    assert all(fills[a] <= fills[b] for a, b in zip(list(fills)[:-1], list(fills)[1:], strict=True))


def test_position_matters_only_under_fifo():
    f, p = expected_fill_by_position(np.array([0, 100, 400]), 10, 500, 120.0, 20_000, 1)
    assert f[0] > f[1] > f[2] and np.ptp(p) == 0.0 and f[0] > p[0] > f[2]
