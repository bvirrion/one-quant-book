"""Numbers gate: every numerical answer printed in Book 7, chapter 27 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import numpy as np
from rs_tcost import AUMS, estimate, liquidity, netting, run, smoothing_curve


def r(x, d=2):
    return round(float(x), d)


def test_estimation():
    for n, exp in ((500, (1.09, 0.24, 0.59, 0.07)), (5000, (0.71, 0.08, 0.48, 0.03)), (50000, (0.67, 0.03, 0.49, 0.01))):
        e = estimate(n)
        assert (r(e["eta_fixed"]), r(e["se_eta"]), r(e["exponent"]), r(e["se_exponent"])) == exp, (n, e)
    assert r(1e4 * 0.7 * 0.02 * math.sqrt(0.01), 0) == 14 and r(1e4 * 0.02 * math.sqrt(0.01 / 0.1), 0) == 63


def test_books():
    n = run("naive", 1e9)
    assert (r(n["sr"]), r(n["sr_net"]), r(100 * n["cost"], 0), r(n["turnover"]), r(100 * n["vol"], 1)) == (2.56, -29.47, 1223, 5.33, 19.2)
    assert [r(run("naive", a)["sr_net"]) for a in AUMS] == [-4.96, -15.91, -29.47, -34.0]
    got = [(r(run("cost-aware", a)["sr"]), r(run("cost-aware", a)["sr_net"]), r(100 * run("cost-aware", a)["cost"], 1),
            r(run("cost-aware", a)["turnover"], 3)) for a in AUMS]
    assert got == [(3.12, -0.31, 46.1, 2.269), (3.14, 0.06, 28.8, 0.814), (3.06, 1.8, 7.6, 0.148), (2.11, 1.76, 1.2, 0.018)]
    assert [r(run("cost-aware", a, 1.0)["sr_net"]) for a in AUMS] == [1.68, 2.03, 2.43, 1.66]
    assert [r(run("naive", a, 50.0)["sr_net"]) for a in AUMS] == [1.78, 1.63, 1.15, -0.23]


def test_smoothing_and_netting():
    assert [r(v) for v in smoothing_curve("naive").values()] == [-29.47, -19.18, -10.62, -2.57, 0.1, 1.02, 1.15, 0.93, 0.69]
    assert [r(v) for v in smoothing_curve("cost-aware").values()] == [1.8, 2.43, 2.37, 2.17, 1.94, 1.71, 1.4, 1.15, 0.94]
    nt = netting()
    assert (r(100 * nt["a"]), r(100 * nt["b"]), r(100 * nt["netted"]), r(100 * nt["saving"]), r(100 * nt["saving_share"], 1),
            r(100 * nt["same_side_extra"])) == (8.27, 8.73, 16.04, 0.96, 5.7, 2.94)
    assert r(0.96 + 2.94, 2) == 3.9


def n_ret():
    return run("naive", 1e9)["ret"]


def test_exercises():
    assert r(1e4 * (2e-4 + 0.7 * 0.02 * math.sqrt(0.05)), 1) == 33.3
    assert r(1e4 * 0.491 / (5.33 * 252), 2) == 3.66 and r(100 * n_ret(), 1) == 49.1
    assert r((2**1.5 - 2) / 2, 2) == 0.41 and (r(math.sqrt(2)), r(2**1.5)) == (1.41, 2.83)
    assert r(np.median([x for d in liquidity().values() for x in d.values()]) / 1e6, 0) == 474
