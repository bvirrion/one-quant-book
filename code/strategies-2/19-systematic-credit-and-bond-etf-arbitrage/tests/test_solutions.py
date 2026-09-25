"""Numbers gate: every numerical answer printed in Book 9, chapter 19 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s2_syscredit import etf, factors, stale_gap  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def test_factors():
    f = factors()
    assert {k: r(f[k]["sr"]) for k in ("value", "momentum", "lowrisk", "combined")} == {
        "value": 0.46, "momentum": 0.14, "lowrisk": 0.95, "combined": 0.94}
    assert {k: r(v) for k, v in f["corr"].items()} == {"value-momentum": -0.09, "value-lowrisk": -0.03,
                                                        "momentum-lowrisk": -0.02}
    assert (r(100 * f["value"]["vol"], 1), r(100 * f["lowrisk"]["vol"], 1)) == (1.4, 0.3)


def test_etf():
    e = etf()
    assert (r(e["discount_normal"], 1), r(e["discount_sd_normal"], 1), r(e["discount_min"], 0), e["min_day"],
            r(e["stale_at_min"], 0), r(e["price_vs_true_at_min"], 0)) == (2.7, 21.6, -504.0, 14, 215.0, -300.0)
    assert (e["profit_days"], r(e["profit_max"], 0), e["profit_outside"], r(100 * e["market_move"], 1)) == (28, 163.0, 0,
                                                                                                           -9.8)
    assert r(-300 + 150) == -150
    assert r((1 / 0.97 - 1 - 0.015) * 1e4, 0) == 159.0                     # exercise 2
    assert r(150 * 6.5 / 100, 2) == 9.75                                   # exercise 3


def test_exercise_7():
    lo = stale_gap(0.05)
    assert (r(lo["discount_min"], 0), r(lo["stale"], 0), lo["day"]) == (-1050.0, 838.0, 14)
