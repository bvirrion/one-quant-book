"""Numbers gate: every numerical answer printed in Book 8, chapter 20 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s1_carry import books, carry_quality, market, sr, summary, trend_correlation, wti  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def table(prem):
    return {k: (r(v["sr"]), r(v["skew"]), [r(100 * x, 1) for x in v["crash"]]) for k, v in summary("mixed", prem).items()}


def test_half_carry_earned():
    assert table(0.5) == {"equity": (0.17, 0.13, [-7.8, -12.8, 9.0]), "bond": (0.22, -0.1, [8.6, -5.5, -9.4]),
                          "currency": (0.03, -0.36, [-30.4, -27.2, -29.1]),
                          "commodity": (0.27, -0.17, [-1.0, -12.5, -0.4]),
                          "diversified": (0.34, -0.21, [-15.3, -29.0, -14.9])}


def test_full_carry_earned():
    assert table(1.0) == {"equity": (0.28, 0.13, [-7.1, -12.4, 9.5]), "bond": (0.53, -0.09, [9.6, -4.1, -8.5]),
                          "currency": (0.49, -0.36, [-29.0, -24.9, -28.0]),
                          "commodity": (0.59, -0.16, [0.8, -11.3, 0.9]),
                          "diversified": (0.95, -0.2, [-12.9, -26.3, -13.1])}


def test_seasonal_carry():
    q = carry_quality()
    assert (r(q["near_all"]), r(q["near_seasonal"]), r(q["year_seasonal"])) == (1.0, 0.05, 1.0)
    assert (r(sr(books("near", 0.5)[0]["commodity"])), r(sr(books("near", 1.0)[0]["commodity"]))) == (0.17, 0.34)
    assert (r(sr(books("near", 0.5)[1])), r(sr(books("near", 1.0)[1]))) == (0.29, 0.82)


def test_trend_and_crashes():
    assert r(trend_correlation()) == -0.0
    assert [(s / 252, e - s) for s, e in market()["crashes"]] == [(7.5, 100), (18.0, 100), (27.0, 100)]


def test_wti():
    w = wti()
    assert (r(100 * w["mean_carry"], 1), r(100 * w["backwardation"], 1), r(w["sr"]), r(100 * w["ret"], 1), w["years"]) \
        == (1.2, 51.7, 0.61, 24.8, (1986, 2024))
    assert (r(100 * w["carry"].min(), 0), r(100 * w["carry"].max(), 0)) == (-575, 126)


def test_exercises():
    assert r(math.log(100 / 98) * 12, 3) == 0.242 and r(0.05 - 0.01, 2) == 0.04
    assert r(0.02 - 0.045, 3) == -0.025
    sd = 10 * math.sqrt(100 / 252)
    assert (r(sd, 1), r(26.3 / sd, 1), r(0.95 * 10 * 100 / 252, 1)) == (6.3, 4.2, 3.8)


def test_diversification_ratio():
    assert r((0.28 + 0.53 + 0.49 + 0.59) / 4) == 0.47 and r(0.95 / 0.47, 1) == 2.0
