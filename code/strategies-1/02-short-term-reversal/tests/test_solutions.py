"""Numbers gate: every numerical answer printed in Book 8, chapter 2 (text and solutions)."""
import csv
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1] / "python"))
from s1_reversal import FLAT, SIZES, breakeven, ic, naive, traded  # noqa: E402

DATA = HERE.parents[4] / "data" / "strategies-1"


def r(x, d=2):
    return round(float(x), d)


def test_ics():
    got = {k: (r(ic(k), 3), r(ic(k, True), 3)) for k in ("raw", "industry", "residual", "truth")}
    assert got == {"raw": (0.037, 0.037), "industry": (0.038, 0.039), "residual": (0.041, 0.041),
                   "truth": (0.044, 0.044)}
    assert (r(ic("residual", skip_earnings=True), 3), r(ic("truth", skip_earnings=True), 3)) == (0.04, 0.042)


def test_naive_books():
    got = {k: (r(naive(k)["sr"]), r(100 * naive(k)["ret"], 1), r(100 * naive(k)["turnover"], 0),
               r(naive(k, FLAT)["sr"]), r(1e4 * breakeven(k), 1)) for k in ("raw", "industry", "residual")}
    assert got == {"raw": (6.69, 27.0, 75, -2.62, 7.2), "industry": (7.24, 28.2, 75, -2.46, 7.5),
                   "residual": (12.96, 30.3, 76, -3.43, 7.9)}


def test_traded_books():
    want = {1e8: (8.42, 1.72, 10.23, 8.18, 2.05, 18.6, 0.91, 2.0), 1e9: (3.97, 0.09, 2.44, 2.38, 0.05, 3.9, 0.48, 0.5),
            1e10: (1.72, 0.19, 0.45, 0.4, 0.05, 0.5, 0.18, 4.8)}
    for a in SIZES:
        t = traded(a, True, 1.0, True)
        assert (r(t["sr_gross"]), r(t["sr_net"]), r(100 * t["ret_gross"]), r(100 * t["cost"]), r(100 * t["ret_net"]),
                r(100 * t["turnover"], 1), r(t["gross"]), r(a * t["ret_net"] / 1e6, 1)) == want[a]
    blind = {a: traded(a, False, 1.0, True) for a in SIZES}
    assert (r(blind[1e8]["sr_gross"]), r(100 * blind[1e8]["turnover"], 0), r(blind[1e8]["gross"])) == (16.92, 186, 2.48)
    assert [r(blind[a]["sr_net"], 1) for a in SIZES] == [-27.8, -31.7, -32.2]
    assert [r(100 * blind[a]["cost"], 0) for a in SIZES] == [246, 738, 2293]
    u = traded(1e9, True, 1.0, False)
    assert (r(100 * u["ret_net"]), r(u["sr_net"])) == (-0.7, -1.04)
    assert (r(traded(3e8, True, 1.0, True)["sr_net"]), r(traded(3e9, True, 1.0, True)["sr_net"])) == (0.73, -0.08)


def test_french_factor():
    rows = {row["period"]: row for row in csv.DictReader(open(DATA / "strev_periods.csv"))}
    f = lambda k, c, d=1: r(100 * float(rows[k][c]), d)  # noqa: E731
    g = lambda k, c: r(float(rows[k][c]))  # noqa: E731
    assert (f("to 1989", "ann_mean"), g("to 1989", "sharpe"), g("to 1989", "t")) == (10.9, 0.93, 7.42)
    assert (f("from 1990", "ann_mean"), g("from 1990", "sharpe"), g("from 1990", "t")) == (1.6, 0.13, 0.79)
    assert tuple(f(k, "ann_mean") for k in ("2020s", "1930s", "2000s", "2010s")) == (-5.2, 26.2, 4.2, 3.7)
    assert (f("from 1990", "ann_vol"), f("to 1989", "ann_vol")) == (12.2, 11.8)


def test_exercises():
    assert r(0.303 / (2 * 0.76 * 252) * 1e4, 1) == 7.9 and r(2 * 0.75 * 0.001 * 252 * 100, 1) == 37.8
    assert r(0.001 * 1e4, 1) == 10.0
    assert r(1e4 * 0.7 * 0.02 * math.sqrt(10 / 25), 1) == 88.5
    assert r(1e4 * 0.04 * 0.02 * 2, 1) == 16.0
    assert r(1e4 * (0.0002 + 0.7 * 0.02 * math.sqrt(0.25 / 25)), 1) == 16.0
