"""Numbers gate: every numerical answer printed in Book 7, chapter 22 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "perf"))
from firm_perf import tear_sheet
from rs_perf import (
    dd_probability,
    histories,
    long_run,
    long_run_shape,
    momentum,
    monthly_scatter,
    smoothed_report,
    stream_results,
    updown_beta,
)


def r(x, d=2):
    return round(float(x), d)


def sheets():
    h, res = histories(), stream_results()
    mres, mkt = momentum()
    cols = [(res["trend"], h["index"], 252), (res["short vol"], h["index"], 252), (res["smoothed"], None, 12),
            (res["market maker"], h["index"], 252), (mres, mkt, 252)]
    return [tear_sheet(x, b, "", p)[0] for x, b, p in cols]


def test_tear_sheet_table():
    M = sheets()
    col = lambda k, d=2, s=1: [r(s * m[k], d) for m in M]  # noqa: E731
    assert col("annual return", 1, 100) == [14.4, 11.6, 7.2, 22.8, 1.1]
    assert col("annual volatility", 1, 100) == [14.6, 10.6, 7.4, 5.1, 9.1]
    assert col("Sharpe") == [1.00, 1.09, 0.99, 4.04, 0.17]
    assert col("se (iid)") == [0.45, 0.45, 0.46, 0.45, 0.32]
    assert col("se (HAC)") == [0.46, 0.45, 0.63, 0.52, 0.31]
    assert col("max drawdown", 1, 100) == [-33.6, -14.8, -11.0, -4.2, -34.0]
    assert [m["longest drawdown"] for m in M] == [791, 48, 22, 72, 2079]
    assert col("Calmar") == [0.43, 0.78, 0.66, 5.39, 0.03]
    assert col("Sortino") == [1.48, 1.87, 2.00, 6.31, 0.24]
    assert col("Omega(0)") == [1.17, 1.49, 2.07, 2.07, 1.03] and all(abs(m["Omega(0)"] - m["profit factor"]) < 1e-12 for m in M)
    assert col("skewness") == [-0.04, 5.38, 0.41, -0.66, -0.00]
    assert col("kurtosis", 1) == [3.0, 102.5, 2.8, 9.9, 3.4]
    assert col("hit rate", 0, 100) == [53, 76, 58, 65, 51]
    assert [r(M[k]["beta"]) for k in (0, 1, 3, 4)] == [-0.00, 0.45, 0.04, 0.00]
    assert [r(M[k]["beta_se"]) for k in (0, 1, 3, 4)] == [0.03, 0.09, 0.01, 0.01]
    assert (r(M[1]["alpha"] * 100, 1), r(M[1]["alpha_t"])) == (5.6, 1.38) and r(M[0]["alpha_t"]) == 2.15
    assert (r(M[3]["alpha_t"], 1), r(M[3]["alpha"] * 100, 1)) == (9.1, 20.2)
    assert (r(M[4]["holding period"], 0), r(100 * M[4]["turnover"], 2)) == (48, 1.86)


def test_named_result_and_long_run():
    pt, ps = dd_probability("trend"), dd_probability("short vol")
    assert (r(100 * pt[5], 0), r(100 * ps[5], 0), r(100 * pt[10], 0), r(100 * ps[10], 0)) == (14, 41, 31, 65)
    assert (r(100 * pt[1], 1), r(100 * ps[1], 0)) == (0.6, 11)
    assert r(100 * histories()["clean share"], 0) == 9
    (st, dt, vt), (ss, ds, vs) = long_run("trend"), long_run("short vol")
    assert (r(st), r(100 * dt, 0), r(ss), r(100 * ds, 0)) == (0.83, -37, 0.62, -72)
    assert (r(100 * vt, 0), r(100 * vs, 0)) == (15, 17)
    s = smoothed_report()
    assert (r(s["sr"]), r(s["se_iid"]), r(s["se_hac"]), r(s["lo"]), r(s["true"]), r(s["unsmoothed"])) == \
        (0.99, 0.46, 0.63, 0.61, 0.66, 0.59)
    assert [r(t) for t in s["theta"]] == [0.43, 0.36, 0.21] and [r(x) for x in s["rho"][:2]] == [0.64, 0.25]
    assert (r(100 * s["vol_rep"], 1), r(100 * s["vol_true"], 1), r(100 * s["vol_un"], 1)) == (7.4, 11.2, 12.7)


def test_betas_and_exercises():
    h = histories()
    assert tuple(r(b) for b in updown_beta(h["short vol"], h["index"])) == (0.59, 0.54)
    assert tuple(r(b) for b in monthly_scatter()[2]) == (0.98, 0.71)
    assert tuple(r(x, d) for x, d in zip(long_run_shape(), (2, 0), strict=True)) == (-1.23, 121)
    assert r(math.sqrt((1 + 0.5 * (1 / math.sqrt(252)) ** 2) / 1260) * math.sqrt(252), 2) == 0.45
    assert r(math.sqrt(0.5**2 + 0.3**2 + 0.2**2), 3) == 0.616 and r(0.6 / 0.616, 2) == 0.97
    assert r((0.5 * 0.3 + 0.3 * 0.2) / 0.38, 2) == 0.55 and r(0.5 * 0.2 / 0.38, 2) == 0.26
    assert r(12 / math.sqrt(12 + 2 * (11 * 0.55 + 10 * 0.26)), 2) == 2.22 and r(math.sqrt(12), 2) == 3.46
    assert r(2.22 / 3.46, 2) == 0.64
    assert r(0.144 / 0.336, 2) == 0.43
    assert (r(1 - 1.96 * 0.45), r(1 + 1.96 * 0.45)) == (0.12, 1.88) and r(math.sqrt(252 / 756)) == 0.58
    assert r(3.46 / 2.22) == 1.56 and r(0.38, 2) == 0.38 and r(100 * (1 / 0.616 - 1), 0) == 62
    assert (r(1.8718, 1), r(1.4756, 1)) == (1.9, 1.5) and r(1 / 0.58, 1) == 1.7
