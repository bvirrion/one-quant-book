"""Numbers gate: every numerical answer printed in Book 8, chapter 1 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s1_statbook import bets, margin_example, summary


def r(x, d=2):
    return round(float(x), d)


def test_two_books():
    a, b = summary(neutral_styles=False), summary(neutral_styles=True)
    pct = lambda x, d=1: r(100 * x, d)  # noqa: E731
    assert (pct(a["ret"]), pct(a["vol"]), r(a["sr"]), pct(a["factor_var_share"]), pct(a["best"]), pct(a["worst"])) == \
        (23.6, 23.6, 1.0, 99.7, 5.8, -4.8)
    assert (pct(a["by_factor_vol"]["momentum"]), pct(a["by_factor"]["momentum"]), pct(a["by_factor"]["value"])) == (23.1, 9.0, -2.9)
    assert (pct(b["ret"]), pct(b["vol"]), r(b["sr"]), pct(b["factor_var_share"]), pct(b["best"]), pct(b["worst"], 2)) == \
        (22.5, 4.5, 5.03, 7.6, 1.5, -1.25)
    assert (pct(b["gross_alpha"]), pct(b["cost"]), pct(b["financing"]), pct(b["rebate"]), pct(b["long_cost"]), pct(b["borrow"])) == \
        (42.0, -22.9, 3.4, 5.6, -2.2, -0.4)
    assert (pct(b["turnover"], 0), r(b["n_long"], 0), r(b["n_short"], 0)) == (91, 452, 495) and b["check"] < 1e-15
    assert pct((-b["long_cost"] - b["borrow"]) / b["gross_alpha"]) == 6.2
    assert pct(b["financing"], 2) == 3.42
    assert (pct(a["turnover"], 0), pct(a["cost"])) == (42, -10.6)


def test_bets_and_margin():
    n, top, med = bets(True)
    assert (r(n / 1e6, 1), r(100 * top, 1), r(100 * med)) == (1.9, 1.0, 0.25)
    assert tuple(r(x) for x in margin_example()) == (1.5, 0.45)


def test_exercises():
    assert r(math.sqrt(946 * 252) * 0.02, 1) == 9.8 and r(0.04 - 0.0342, 4) == 0.0058
    assert r(1.5 * (0.04 - 0.0025) - 0.5 * 0.045, 4) == 0.0337
    assert r(0.5 * 1.5 + 0.5 * 1.5, 2) == 1.5 and r(1 / 0.5, 1) == 2.0 and r(1 / 0.15, 2) == 6.67


def test_half_lives():
    f, s = summary(half_life=1.0, neutral_styles=True), summary(half_life=5.0, neutral_styles=True)
    assert (r(f["sr"]), r(100 * f["cost"], 1), r(100 * f["ret"], 1), r(100 * f["turnover"], 0)) == (6.16, -32.5, 27.5, 129)
    assert (r(s["sr"]), r(100 * s["cost"], 1), r(100 * s["ret"], 1), r(100 * s["turnover"], 0)) == (2.47, -14.0, 11.7, 56)
