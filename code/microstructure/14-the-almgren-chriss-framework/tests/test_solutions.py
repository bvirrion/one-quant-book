"""Numbers gate: every numerical answer printed in Book 10, chapter 14 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from mx_ac import ETA, SIGMA, X, block_study, sim_study  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def test_block():
    assert (r(ETA * 1e7, 3), SIGMA) == (2.53, 1.0)
    b = block_study()
    assert (r(b["kappa"]), r(b["cost"] / 1000, 0), r(b["sd"] / 1000, 0), r(b["utility"] / 1000, 0)) == (1.99, 300.0, 470.0, 521.0)
    assert r(b["t95_hours"], 1) == 5.9
    tw, pa, hu = b["twap"], b["patient"], b["hurried"]
    assert [r(x / 1000, 0) for x in tw] == [253.0, 576.0, 585.0]
    assert [r(x / 1000, 0) for x in pa] == [258.0, 542.0, 551.0]
    assert [r(x / 1000, 0) for x in hu] == [506.0, 352.0, 630.0]
    assert (r(100 * (pa[2] / b["utility"] - 1), 1), r(100 * (hu[2] / b["utility"] - 1), 1)) == (5.8, 20.9)
    assert (r(b["cost"] / X, 2), r(b["cost"] / X / 50 * 1e4, 0)) == (0.3, 60.0)
    # 2: TWAP by formula
    assert (r(ETA * X**2 / 1000, 0), r(math.sqrt(SIGMA**2 * X**2 / 3) / 1000, 0)) == (253.0, 577.0)


def test_simulation():
    s = sim_study()
    assert [r(s[k]["mean"], 1) for k in (0.0, 2.0, 6.0)] == [5.2, 5.3, 7.4]
    assert [r(s[k]["se"], 1) for k in (0.0, 2.0, 6.0)] == [2.8, 2.3, 1.3]
    assert [r(s[k]["sd"], 1) for k in (0.0, 2.0, 6.0)] == [8.0, 6.5, 3.8]
    assert [r(s[k]["model_mean"], 1) for k in (0.0, 2.0, 6.0)] == [1.2, 1.4, 3.6]
    assert [r(s[k]["model_sd"], 1) for k in (0.0, 2.0, 6.0)] == [16.4, 13.2, 7.6]
    assert (r(s["eta"], 3), r(s["sigma"], 2)) == (0.11, 0.69)
    # 7: the implied permanent impact
    g = [2 * (s[k]["mean"] - s[k]["model_mean"]) / 20_000 * 1e4 for k in (0.0, 6.0)]
    assert [r(x, 1) for x in g] == [4.0, 3.8]
