"""Numbers gate: every numerical answer printed in Book 4, Chapter 26 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import qm_mc  # noqa: E402
from firm_mcengine import control_variate, geometric_asian_price  # noqa: E402
from qm_mc import bs_call, digital_is, error_vs_cost, mlmc_study, orders, slope, table  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def test_variance_table():
    tb = table(14, 32)
    f = tb["factor"]
    assert (r(tb["plain_est"], 3), r(tb["plain_se"], 3), r(tb["price"], 4), r(tb["geo"], 4)) == (6.495, 0.077, 6.4788, 6.1793)
    assert tb["price_se"] < 1e-4 and abs(tb["plain_est"] - tb["price"]) < 2 * tb["plain_se"]
    assert (r(f["antithetic"], 1), round(f["control variate"]), r(tb["rho_cv"], 5), r(tb["beta"])) == (1.8, 853, 0.99941, 1.04)
    assert r(tb["rho_anti"]) == -0.43 and r(1 - tb["rho_cv"] ** 2, 4) == 0.0012
    assert 30 < f["rqmc increments"] < 38 and 2200 < f["rqmc bridge"] < 2800 and 33000 < f["rqmc bridge + cv"] < 41000
    assert round(math.sqrt(f["rqmc bridge + cv"]) / 10) * 10 == 190


def test_error_vs_cost_slopes():
    rows = error_vs_cost()
    n = [row[0] for row in rows]
    s = [slope(n, [row[i] for row in rows]) for i in range(1, 6)]
    assert (r(s[0], 2), r(s[1], 2)) == (-0.5, -0.5)
    assert all(-0.82 < v < -0.68 for v in s[2:]) and (n[0], n[-1]) == (64, 32768)


def test_orders_mlmc_is():
    o = orders()
    x = [row[0] for row in o]
    assert (r(-slope(x, [row[1] for row in o])), r(-slope(x, [row[2] for row in o])),
            r(-slope(x, [row[3] for row in o]))) == (0.49, 0.89, 1.0)
    ml = {row["eps"]: row for row in mlmc_study()}
    m = ml[0.005]
    assert (m["L"], r(m["cost"] / 1e7, 1), r(m["std_cost"] / 1e9, 1), round(m["ratio"])) == (7, 3.2, 3.0, 94)
    assert [round(ml[e]["ratio"]) for e in (0.04, 0.02, 0.01)] == [8, 20, 45]
    assert [f"{v:.2g}" for v in m["V"][1:]] == ["0.23", "0.062", "0.016", "0.0045", "0.0012", "0.0003", "7.9e-05"]
    assert abs(m["est"] - bs_call(100, 100, 0.03, 0.25, 1.0)) < 2 * 0.005 and r(bs_call(100, 100, 0.03, 0.25, 1.0), 4) == 11.3485
    d = digital_is()
    rows = {r(th, 1): (est, rel) for th, est, rel in d["rows"]}
    assert (r(d["zstar"]), r(d["exact"] * 1e4)) == (3.67, 1.21)
    assert (r(rows[0.0][0] * 1e5, 1), r(rows[0.0][1])) == (6.0, 0.2) and r(rows[3.8][1] * 100) == 0.64
    assert min(rows, key=lambda t: rows[t][1]) == 3.8 and round((rows[0.0][1] / rows[3.8][1]) ** 2, -2) == 1000


def test_exercises():
    assert (r(1 / (1 - 0.81), 1), r(1 / (1 - 0.99**2), 1)) == (5.3, 50.3)
    z = digital_is()["zstar"]
    th = np.linspace(0, 6, 60001)
    m2 = np.exp(th**2) * 0.5 * np.array([math.erfc((z + t) / math.sqrt(2)) for t in th])
    assert r(th[m2.argmin()]) == 3.8
    out = {}
    for strike in (80.0, 130.0):
        qm_mc.K = strike
        try:
            p = qm_mc.plain(2**14)
            geo = geometric_asian_price(100.0, strike, 0.03, 0.25, 1.0, 64)
            cv = control_variate(p["a"], p["g"], geo)
            out[strike] = (r(cv["rho"], 5), round(1 / (1 - cv["rho"] ** 2)))
        finally:
            qm_mc.K = 100.0
    assert out == {80.0: (0.99953, 1071), 130.0: (0.99425, 87)}


def test_multilevel_scheme_ablation():
    """WRITING section 9: halving the step halves Euler's weak error of the mean and Milstein's strong error, and
    dropping the Milstein term (the ablation, i.e. Euler) leaves strong order one half."""
    o = orders()
    for a, b in zip(o[3:], o[4:], strict=False):
        assert 1.9 < a[3] / b[3] < 2.1 and 1.7 < a[2] / b[2] < 2.1 and 1.3 < a[1] / b[1] < 1.5
