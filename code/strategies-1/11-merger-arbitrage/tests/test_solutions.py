"""Numbers gate: every numerical answer printed in Book 8, chapter 11 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s1_mergerarb import break_rates, run  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "mergerarb"))
from firm_mergerarb import annualised, collar_value, implied_probability, spread  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def test_base_case():
    b = run()
    assert (r(100 * b["ret"]), r(100 * b["excess"]), r(100 * b["vol"]), r(b["sr"]), r(b["beta"], 3)) == \
        (6.76, 2.76, 3.26, 0.85, 0.0)
    assert (r(b["beta_down"]), r(b["beta_up"]), b["down_months"], b["months"]) == (0.2, 0.09, 10, 96)
    assert (r(100 * b["worst_month"]), r(100 * b["mkt_worst"], 1), r(b["active"], 1), b["deals"]) == \
        (-3.06, 2.8, 22.3, 374)
    assert (r(100 * b["implied"], 0), r(100 * b["completed"], 1), r(100 * b["spread"], 2), r(100 * b["spread_ann"], 1)) == \
        (88, 92.5, 4.73, 11.8)
    br = break_rates()
    assert (r(100 * br["fell"], 1), r(100 * br["rose"], 1), br["n_fell"]) == (13.7, 4.7, 117)


def test_variants():
    f = lambda x: (r(100 * x["excess"], 2), r(x["sr"]))  # noqa: E731
    assert f(run(0.0, 0.12, 0.06)) == (4.3, 1.5)
    assert f(run(1.5, 0.06, 0.06)) == (-0.47, -0.17)
    assert f(run(0.0, 0.06, 0.06)) == (1.03, 0.46)
    assert (r(100 * run(0.0)["completed"], 1), r(100 * run(1.5, 0.06)["spread"], 2)) == (94.7, 3.27)
    assert r(100 * (run(0.0)["excess"] - run()["excess"]), 1) == 1.5


def test_exercises():
    assert (r(100 * spread(38.6, 40.0), 2), r(implied_probability(38.6, 40.0, 30.0), 2)) == (3.63, 0.86)
    assert r(100 * annualised(spread(38.6, 40.0), 84), 1) == 11.3
    assert r(collar_value(42.0, 0.5, 40.0, 50.0), 1) == 21.0 and r(collar_value(36.0, 0.5, 40.0, 50.0), 1) == 20.0
    assert r(0.86 * 1.4 - 0.14 * 8.6, 2) == 0.0
