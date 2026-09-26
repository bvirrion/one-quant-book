"""Numbers gate: every numerical answer printed in Book 10, chapter 5 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from mx_decomp import by_horizon, day, estimators, low_frequency, truth, var_by_lags  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "code" / "firm" / "spreaddecomp"))
from firm_spreaddecomp import corwin_schultz, decompose, quoted_spread  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def test_truth_and_horizons():
    d = day()
    assert (len(d.trades), r(d.trades["qty"].mean(), 0)) == (21993, 118.0)
    n = d.n_open
    assert r(quoted_spread(d.top["t"][n:], d.top["bid"][n:], d.top["ask"][n:], d.cfg.seconds)) == 1.04
    tr = truth(d)
    assert (r(tr["effective"], 3), r(tr["adverse"], 3), r(tr["share"])) == (0.535, 0.449, 0.84)
    assert (r(tr["informed_volume"], 3), r(tr["gap_informed"]), r(tr["gap_noise"], 3)) == (0.21, 2.05, 0.025)
    h = by_horizon(d)
    assert [r(h[x]["impact"]) for x in (0.05, 1.0, 5.0, 15.0, 30.0, 60.0, 120.0, 300.0)] == \
        [0.03, 0.08, 0.21, 0.35, 0.40, 0.48, 0.40, 0.20]
    assert [r(h[x]["se"]) for x in (60.0, 300.0)] == [0.07, 0.15]
    assert [r(h[x]["clean"]) for x in (15.0, 30.0, 60.0, 120.0, 300.0)] == [0.38, 0.43, 0.46, 0.48, 0.46]
    assert r(h[300.0]["clean_se"]) == 0.04 and r(h[60.0]["clean_se"]) == 0.04
    assert (r(h[0.05]["realised"]), r(h[60.0]["realised"], 3)) == (0.50, 0.056)
    assert r(h[60.0]["clean"] / tr["effective"]) == 0.85
    assert r(h[300.0]["se"] / h[60.0]["se"]) == 2.28 and r(math.sqrt(5)) == 2.24


def test_estimators():
    d = day()
    e = estimators(d)
    assert (r(e["realised_60s"]), r(e["huang_stoll"]), r(e["hs_spread"]), r(e["mrr"]), r(e["mrr_rho"])) == \
        (0.89, 0.09, 1.07, 0.13, 0.33)
    assert (r(e["gh_100"], 3), r(e["gh_500"], 3)) == (0.095, -0.067)
    tr = d.trades
    assert (r(tr["qty"][tr["informed"]].mean(), 0), r(tr["qty"][~tr["informed"]].mean(), 0)) == (109.0, 120.0)
    v = var_by_lags(d)
    assert [r(x) for x in v.values()] == [0.14, 0.28, 0.38, 0.49, 0.56, 0.48]
    t, m = d.top["t"], 0.5 * (d.top["bid"] + d.top["ask"])
    inf = d.trades["informed"]
    a, b = decompose(d.trades[inf], t, m, 60.0), decompose(d.trades[~inf], t, m, 60.0)
    assert (r(a["effective"]), r(a["realised"]), r(a["impact"])) == (0.54, -1.57, 2.11)
    assert (r(b["effective"]), r(b["realised"]), r(b["impact"], 3)) == (0.53, 0.49, 0.045)


def test_low_frequency():
    d = day()
    got = {b: low_frequency(d, b) for b in (30.0, 60.0, 300.0, 900.0)}
    assert r(got[60.0]["effective_rel"] * 1e4, 2) == 1.07
    assert [r(got[b]["cs"] * 1e4, 1) for b in got] == [0.5, 0.6, 2.0, 2.6]
    assert [r(got[b]["ar"] * 1e4, 1) for b in got] == [0.1, 0.0, 3.3, 0.0]
    assert [got[b]["bars"] for b in got] == [761, 390, 78, 26]


def test_exercises():
    # 1: bid 100.00, ask 100.04, buy at 100.03, mid a minute later 100.025
    m0, p, m1 = 100.02, 100.03, 100.025
    assert (r(p - m0, 3), r(p - m1, 3), r(m1 - m0, 3), r(100.04 - p, 3)) == (0.01, 0.005, 0.005, 0.01)
    assert r(2 * (p - m0) / m0 * 1e4, 1) == 2.0
    # 2: sale at 49.98, mid 50.00, mid five minutes later 49.97
    assert (r(-(49.98 - 50.00)), r(-(49.98 - 49.97)), r(-(49.97 - 50.00))) == (0.02, -0.01, 0.03)
    # 3: Huang-Stoll with S = 0.04, lambda = 0.6
    assert (r(0.6 * 0.02, 3), r(0.4 * 0.02, 3)) == (0.012, 0.008)
    # 4: MRR theta = 0.012, phi = 0.008, rho = 0.3
    th, ph, rho = 0.012, 0.008, 0.3
    assert (r(2 * (th + ph)), r(th / (th + ph)), r(th * (1 - rho), 4), r(2 * ph + th * (1 + rho), 4)) == \
        (0.04, 0.6, 0.0084, 0.0316)
    # 6: Corwin-Schultz on two days
    h, lo = np.log([100.10, 100.12]), np.log([99.94, 99.96])
    beta = (h[0] - lo[0]) ** 2 + (h[1] - lo[1]) ** 2
    gamma = (h.max() - lo.min()) ** 2
    assert (r(beta * 1e6, 2), r(gamma * 1e6, 2)) == (5.12, 3.24)
    assert r(corwin_schultz([100.10, 100.12], [99.94, 99.96]) * 1e4, 1) == 11.2
