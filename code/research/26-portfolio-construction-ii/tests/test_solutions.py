"""Numbers gate: every numerical answer printed in Book 7, chapter 26 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from rs_allocation import METHODS, PHI, RULES, backtest, multiperiod, redraw_turnover, stability


def r(x, d=2):
    return round(float(x), d)


def test_stability_and_backtests():
    per_bp = [tuple(r(100 * v, k) for v, k in zip(stability(m), (3, 2), strict=True)) for m in METHODS[:4]]
    assert per_bp == [(0.029, 0.33), (0.028, 0.24), (0.028, 0.12), (0.031, 0.11)]
    assert [r(100 * redraw_turnover(m), 1) for m in METHODS] == [23.9, 23.4, 22.4, 24.4, 0.0, 0.0, 0.0, 0.0]
    got = [(r(backtest(m)["sr"]), r(backtest(m)["sr_net"]), r(100 * backtest(m)["vol"], 1), r(100 * backtest(m)["turnover"], 0))
           for m in METHODS]
    assert got == [(0.62, 0.57, 15.8, 33), (0.82, 0.77, 15.9, 31), (0.66, 0.61, 15.8, 31), (0.75, 0.72, 19.6, 27),
                   (0.66, 0.65, 18.4, 7), (0.69, 0.67, 17.8, 14), (0.67, 0.66, 19.3, 5), (0.66, 0.65, 19.5, 6)]


def test_multiperiod():
    for lam, exp in ((100.0, [(5.14, -0.51, 0.566), (4.74, 4.06, 0.040), (5.07, 3.36, 0.126), (3.01, 2.96, 0.002)]),
                     (1000.0, [(5.14, -22.62, 5.663), (3.5, 3.15, 0.017), (4.28, 1.08, 0.187), (3.01, 2.55, 0.022)])):
        got = [(r(multiperiod(k, lam)["sr"]), r(multiperiod(k, lam)["sr_net"]), r(multiperiod(k, lam)["cost"], 3)) for k in RULES]
        assert got == exp, (lam, got)
    assert (r(multiperiod(RULES[1], 100.0)["rate"]), r(multiperiod(RULES[1], 1000.0)["rate"])) == (0.56, 0.23)
    assert (r(multiperiod(RULES[0], 100.0)["turnover"]), r(multiperiod(RULES[1], 100.0)["turnover"])) == (2.11, 0.56)
    assert (r(PHI["momentum"], 5), r(PHI["pead"], 4)) == (0.00137, 0.0167)
    assert r(multiperiod(RULES[1], 10000.0)["sr_net"]) == 1.61 and r(multiperiod(RULES[3], 10000.0)["sr_net"]) == -0.68


def test_exercises():
    a = 0.5617 * 100
    assert r(1 / (1 + 1.0 * a / 72), 2) == 0.56 and r(1 / (1 + 0.00137 * a / 72), 3) == 0.999
    assert r(1 / (1 + (1 / 60) * a / 72), 3) == 0.987
    assert r(math.sqrt(0.5**2 * 0.04 + 0.5**2 * 0.01), 3) == 0.112 and r(0.5617 * 100 / 72, 2) == 0.78
    assert r(math.sqrt((1 + 0.7**2 / 2) / 7.9), 1) == 0.4 and r(0.67 - 0.57, 2) == 0.10
    assert r(100 * backtest(METHODS[5])["max_weight"], 1) == 5.8
