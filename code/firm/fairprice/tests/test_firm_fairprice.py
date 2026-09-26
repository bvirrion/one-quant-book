"""Acceptance tests of firm.fairprice (the Python reference; cpp/ and rust/ replay the same fixture)."""
import csv
import math
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import fairprice_fixture as make_fixture  # noqa: E402
import firm_fairprice as fp  # noqa: E402


def test_weighted_mid_and_micro():
    assert math.isclose(float(fp.weighted_mid(99, 300, 100, 100)), 99.75)     # big bid queue: towards the ask
    g = np.array([-0.3, 0.0, 0.3])
    assert math.isclose(float(fp.micro(99, 900, 100, 100, g)), 99.8)
    gs = fp.fit_micro([0.1, 0.1, 0.9, 0.5], [1, 1, 1, 2], [-1.0, 0.0, 1.0, 5.0], 2)
    assert np.allclose(gs, [-0.5, 1.0])                                         # the two-tick spread row is ignored


def test_filter_is_the_kalman_update():
    f = fp.FairFilter(q=0.5, r=[1.0, 4.0])
    assert f.update(0.0, 0, 100.0) == 100.0 and f.p == 1.0
    x = f.update(2.0, 1, 102.0)                   # p = 1 + 0.5 * 2 = 2, k = 2 / 6
    assert math.isclose(x, 100.0 + 2.0 / 6.0 * 2.0) and math.isclose(f.p, 2.0 * (1 - 2.0 / 6.0))
    est, var = f.predict(4.0)
    assert est == x and math.isclose(var, f.p + 1.0)


def test_fixture_matches_the_reference():
    d = HERE / "data"
    ev = make_fixture.events()
    rows = list(csv.reader(open(d / "fixture_events.csv")))[1:]
    exp = list(csv.reader(open(d / "fixture_expected.csv")))[1:]
    assert len(rows) == len(ev) == len(exp) == 3000
    f = fp.FairFilter(make_fixture.Q, make_fixture.R)
    for (t, s, y), e in zip(ev, exp, strict=True):
        assert f.update(t, s, y) == float(e[0])
