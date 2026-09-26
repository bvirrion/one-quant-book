import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_wholesale as fw  # noqa: E402


def test_flows():
    r = fw.Flow("retail", n=5000, seed=3)
    i = fw.Flow("institutional", n=500, seed=4)
    assert np.median(r.size) < np.median(i.size) and r.info.mean() < i.info.mean()
    assert np.all(np.diff(r.t) > 0) and set(np.unique(r.side)) <= {-1.0, 1.0}


def test_decomposition_by_hand():
    f = fw.Flow("retail", n=3000, seed=5)
    a = fw.wholesale(f, 0.3, pfof=0.1, limit=1e12, sigma_day=0.0)
    assert math.isclose(a["capture"], float((f.size * f.half).sum() * 0.7 / f.size.sum()))
    assert math.isclose(a["pfof"], 0.1) and a["hedge"] == 0.0 and a["inventory"] == 0.0
    assert math.isclose(a["net"], a["capture"] - a["markout"] - a["pfof"])
    more = fw.wholesale(f, 0.5, pfof=0.1, limit=1e12, sigma_day=0.0)
    assert more["net"] < a["net"]


def test_limits_and_605():
    f = fw.Flow("retail", n=5000, seed=6)
    tight, loose = fw.wholesale(f, 0.3, limit=500.0), fw.wholesale(f, 0.3, limit=50000.0)
    assert tight["hedge"] > loose["hedge"] and tight["hedged_share"] > loose["hedged_share"]
    s = fw.rule605(f, 0.3)
    assert math.isclose(s["eq"], 0.7) and s["improvement"] > 0
