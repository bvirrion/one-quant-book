import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_drarb as fd  # noqa: E402


def test_fair_values():
    assert fd.dr_fair(10.0, 2.0, 1.25) == 25.0
    assert math.isclose(fd.closed_fair(10.0, 2.0, 1.25, 0.01, 1.2), 25.0 * 1.012)


def test_conversion():
    assert math.isclose(fd.threshold_bp(25.0, 0.05, 6.0, 2, 0.05), 20.0 + 6.0 + 1e4 * 0.05 * 2 / 360)
    act, edge = fd.conversion_edge(25.2, 10.0, 2.0, 1.25, 0.05, 6.0)
    assert act == "issue" and math.isclose(edge, 0.2 - 0.05 - 25.0 * (6e-4 + 0.05 * 2 / 360))
    assert fd.conversion_edge(24.8, 10.0, 2.0, 1.25, 0.05, 6.0)[0] == "cancel"
    assert fd.conversion_edge(25.05, 10.0, 2.0, 1.25, 0.05, 6.0) == ("none", 0.0)


def test_pair():
    p = fd.Pair(days=10, seed=2)
    assert p.open.sum() == 10 * p.overlap and np.all(p.t_home <= np.arange(p.m))
    assert np.all(p.t_home[p.open] == np.arange(p.m)[p.open])
    eh, ep = p.error_bp("home"), p.error_bp("proxy")
    assert np.allclose(eh[p.open], ep[p.open])
    rms = lambda x: float(np.sqrt(np.mean(x * x)))  # noqa: E731
    assert rms(ep[p.open]) < 3.0 and rms(ep[~p.open]) < rms(eh[~p.open]) and rms(ep[~p.open]) > 10 * rms(ep[p.open])
