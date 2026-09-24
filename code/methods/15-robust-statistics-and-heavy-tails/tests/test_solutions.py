"""Numbers gate: every numerical answer printed in Book 4, Chapter 15 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from qm_robust import (
    dependence,
    gaussian_tail_dependence,
    gpd_fit,
    gpd_quantile,
    hill_curve,
    load,
    scale_table,
    sensitivity,
    tail_quantiles,
)

C, B = scale_table(False), scale_table(True)
TQ, TB = tail_quantiles(False), tail_quantiles(True)
D = dependence()


def r(x, d=2):
    return round(float(x), d)


def test_data():
    d = load(False)
    assert d["dates"][0] == "1999-01-04" and d["dates"][-1] == "2026-09-23" and d["r_usd"].size == 7098
    assert r(d["usd"][d["dates"] == "2026-03-24"][0], 4) == 1.1572


def test_hook_and_scales():
    assert (r(C["sd"]), r(B["sd"]), round(B["sd"] / C["sd"])) == (0.34, 2.43, 7)
    assert (r(C["mad"], 3), r(B["mad"], 3), r(C["qn"], 3), r(B["qn"], 3)) == (0.275, 0.279, 0.300, 0.305)
    assert (r(100 * (B["mad"] / C["mad"] - 1), 1), r(100 * (B["qn"] / C["qn"] - 1), 1)) == (1.3, 1.5)
    assert r(C["sd"], 3) == 0.339 and r(B["sd"], 3) == 2.434
    assert (r(C["mean"], 3), r(B["mean"], 3), r(C["median"], 3)) == (-0.011, -0.011, -0.030)
    assert (r(C["huber"], 5), r(B["huber"], 5)) == (-0.01953, -0.01948)
    assert r(100 * math.log(1.5172 / 1.1572), 1) == 27.1
    s = dict((round(e, 4), v) for e, *v in sensitivity(errors=[0.0, 0.2709]))
    assert r(s[0.2709][0], 2) == 2.43
    rr = load(False)["r_usd"]
    z = (rr - rr.mean()) / rr.std()
    assert (int(np.sum(np.abs(z) > 4)), int(np.sum(z < -4)), int(np.sum(z > 4))) == (17, 6, 11)
    assert r(len(z) * math.erfc(4 / math.sqrt(2)), 2) == 0.45 and r(np.mean(z**4), 1) == 6.3
    assert (r(z.min(), 1), r(z.max(), 1)) == (-8.2, 7.2)
    assert 0.5 * math.erfc(7 / math.sqrt(2)) < 1e-11


def test_huber_efficiency():
    c = 1.345

    def phi(z):
        return math.exp(-z * z / 2) / math.sqrt(2 * math.pi)

    def cdf(z):
        return 0.5 * math.erfc(-z / math.sqrt(2))
    e1 = 2 * cdf(c) - 1
    e2 = e1 - 2 * c * phi(c) + 2 * c * c * (1 - cdf(c))
    assert (r(e1, 4), r(e2, 4), r(e1**2 / e2, 3)) == (0.8214, 0.7102, 0.950)


def test_dependence():
    assert (r(D["pearson"]), r(D["spearman"], 3), r(D["spearman_gauss"], 3), r(D["kendall"], 3), r(D["kendall_gauss"], 3)) == (
        0.42, 0.406, 0.406, 0.286, 0.277)
    assert (r(D["tail_05"]), r(D["tail_01"])) == (0.32, 0.21)
    assert (r(gaussian_tail_dependence(D["pearson"], 0.05)), r(gaussian_tail_dependence(D["pearson"], 0.01))) == (0.20, 0.10)
    assert (r(6 / math.pi * math.asin(0.21), 3), r(2 / math.pi * math.asin(0.42), 3)) == (0.404, 0.276)


def test_tail():
    assert (r(TQ["u"]), TQ["n_exc"], r(TQ["xi"], 3), r(TQ["beta"])) == (0.93, 355, 0.069, 0.34)
    assert (r(TQ["normal"]), r(TQ["t"]), r(TQ["gpd"]), r(TQ["empirical"])) == (1.80, 2.74, 2.47, 2.27)
    assert (r(TQ["df"], 1), r(TQ["t_scale"]), r(TQ["sd"])) == (4.7, 0.44, 0.58)
    assert (TQ["n_beyond_normal"], TQ["n_beyond_gpd"], r(TQ["n"] * 0.001, 0)) == (35, 6, 7)
    assert (r(TB["normal"]), r(TB["t"]), r(TB["gpd"]), r(TB["xi"])) == (2.27, 2.91, 2.85, 0.22)
    assert (round(100 * (TB["normal"] / TQ["normal"] - 1)), round(100 * (TB["t"] / TQ["t"] - 1)),
            round(100 * (TB["gpd"] / TQ["gpd"] - 1))) == (27, 6, 15)
    assert r(TB["sd"]) == 0.74
    h = {k: a for k, a, _ in hill_curve(ks=[50, 100, 150, 200, 700])}
    assert (r(h[50], 1), r(h[700], 1)) == (4.9, 2.6) and all(3.8 <= h[k] <= 4.0 for k in (100, 150, 200))
    assert r(hill_curve(ks=[50])[0][2], 1) == 0.7


def test_thresholds_and_extrapolation():
    """WRITING section 9 analogue for a fit: the named quantile is stable across thresholds (the fit's 'step'),
    and the mechanism credited (the bad print) is ablated by the clean run above."""
    loss = -load(False)["r_usd"]
    rows = []
    for us in (0.10, 0.05, 0.025, 0.01):
        u = float(np.quantile(loss, 1 - us))
        y = loss[loss > u] - u
        xi, b = gpd_fit(y)
        rows.append((y.size, r(xi, 3), r(gpd_quantile(u, xi, b, y.size / loss.size, 0.999))))
    assert rows == [(710, 0.033, 2.45), (355, 0.069, 2.47), (178, 0.098, 2.49), (71, 0.212, 2.43)]
    q4 = gpd_quantile(TQ["u"], TQ["xi"], TQ["beta"], TQ["n_exc"] / TQ["n"], 0.9999)
    assert r(q4) == 3.59 and int(np.sum(loss > q4)) == 2 and r(TQ["n"] * 1e-4, 1) == 0.7
    s = np.sort(loss)[::-1]
    assert (r(s[0], 1), r(s[1], 1)) == (4.7, 3.7)
    from firm_robust import winsorize
    assert (r(winsorize(load(False)["r_usd"][-250:], 0.01).std(ddof=1), 3), r(winsorize(load(True)["r_usd"][-250:], 0.01).std(ddof=1), 3)) == (0.328, 0.341)
