"""Numbers gate: every numerical answer printed in Book 7, chapter 14 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from rs_combine import geometry, orthogonalised, results, small_universe


def r(x, d=3):
    return round(float(x), d)


def pair(t):
    return (r(t[0]), r(t[1]))


def test_full_panel():
    from rs_combine import data

    assert data("stable")[0].shape == (119, 704, 40)
    s, d = results("stable"), results("drifting")
    assert (r(s["signal_ic"].mean()), r(d["signal_ic"].mean())) == (0.015, 0.013)
    assert pair(s["equal"]) == (0.065, 0.064) and pair(d["equal"]) == (0.055, 0.060)
    assert pair(s["ic_weighted"]) == (0.091, 0.099) and pair(d["ic_weighted"]) == (0.073, 0.075)
    assert pair(s["max_icir"][0.0]) == (0.050, 0.064) and pair(d["max_icir"][0.0]) == (0.052, 0.041)
    assert pair(s["max_icir"][1.0]) == (0.090, 0.098) and pair(d["max_icir"][1.0]) == (0.074, 0.074)
    assert pair(s["ridge"][0.0]) == (0.093, 0.100) and pair(d["ridge"][0.0]) == (0.076, 0.071)
    assert pair(s["lasso"]) == (0.093, 0.102) and pair(d["lasso"]) == (0.075, 0.071)
    assert (r(s["oracle"]), r(d["oracle"])) == (0.102, 0.087)
    assert r(max(abs(v[1] - s["ridge"][0.0][1]) for v in s["ridge"].values()), 4) <= 0.001
    assert r(d["ridge"][1.0][1] - d["ridge"][0.0][1]) == 0.003
    assert list(s["stack"][0]) == [0.0, 1.0, 0.0] and list(d["stack"][0]) == [0.0, 1.0, 0.0]
    assert (r(s["stack"][2]), r(d["stack"][2])) == (0.099, 0.075)


def test_geometry():
    m, t, ic, c = geometry()
    assert (r(ic), r(c)) == (0.015, 0.027)
    assert (r(m[2]), r(m[10]), r(m[40]), r(t[40]), r(ic / math.sqrt(c))) == (0.021, 0.042, 0.064, 0.065, 0.090)


def test_small_universe():
    s12, d12 = small_universe("stable", 12), small_universe("drifting", 12)
    assert (r(s12["equal"]), r(d12["equal"])) == (0.069, 0.069)
    assert (r(s12["shrunk"][0.0]), r(d12["shrunk"][0.0])) == (0.073, 0.005)
    best = max(s12["shrunk"], key=s12["shrunk"].get)
    assert (best, r(s12["shrunk"][best])) == (0.4, 0.081) and max(d12["shrunk"], key=d12["shrunk"].get) == 1.0
    assert r(s12["ic_weighted"]) == 0.086
    icw = {w: [r(small_universe(w, k)["ic_weighted"]) for k in (6, 12, 24, 48)] for w in ("stable", "drifting")}
    assert icw == {"stable": [0.085, 0.086, 0.082, 0.092], "drifting": [0.043, 0.049, 0.067, 0.074]}
    opt = {}
    for k in (6, 24, 48):
        u = small_universe("stable", k)["shrunk"]
        b = max(u, key=u.get)
        opt[k] = (b, r(u[b]))
    assert opt == {6: (0.5, 0.074), 24: (0.6, 0.074), 48: (0.4, 0.083)}


def test_orthogonalised():
    o = orthogonalised("stable")
    assert (r(o["raw"]), r(o["symmetric"]), r(o["sequential"]), r(o["sym_corr"], 2)) == (0.064, 0.064, 0.050, 0.95)


def test_exercises():
    assert r(10 * 0.02 / math.sqrt(10 + 90 * 0.25)) == 0.035 and r(0.02 / math.sqrt(0.25), 2) == 0.04
    w = np.array([0.75, 0.25, 0.0])
    assert [r(x) for x in 0.5 * w + 0.5 / 3] == [0.542, 0.292, 0.167]
    C = np.array([[1.0, 0.5], [0.5, 1.0]])
    rho = np.array([0.03, 0.02])
    v = np.linalg.solve(C, rho)
    assert [r(x, 4) for x in v] == [0.0267, 0.0067] and [r(x, 1) for x in v / v.sum()] == [0.8, 0.2]
    assert (r(math.sqrt(rho @ v), 4), r(0.05 / math.sqrt(3), 4)) == (0.0306, 0.0289)
