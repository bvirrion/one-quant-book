"""Numbers gate: every numerical answer printed in Book 11, chapter 23 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import hf_wholesale as h  # noqa: E402


def r(x, d=3):
    return round(float(x), d)


def test_pi():
    b = h.by_pi()
    assert [r(b[p]["retail"]["net_ex_inventory"]) for p in (0.0, 0.3, 0.7)] == [0.85, 0.475, -0.025]
    assert [r(b[p]["inst"]["net_ex_inventory"], 2) for p in (0.0, 0.3, 0.7)] == [-0.57, -0.94, -1.44]
    assert r(b[0.3]["retail"]["net"], 2) == 0.44 and r(b[0.3]["retail"]["hedge"], 2) == 0.2
    assert r(1 - b[0.3]["retail"]["hedged_share"], 2) == 0.87
    assert r(h.break_even(), 2) == 0.68


def test_605_limits_herding():
    s = h.rule605()
    assert (r(s["quoted"], 2), r(s["effective"], 2), r(s["eq"], 2), r(s["improvement"])) == (2.5, 1.75, 0.7, 0.375)
    lim = h.limits()
    assert [(r(lim[k]["mean"], 2), r(lim[k]["sd"], 2)) for k in (1000.0, 10000.0)] == [(0.2, 0.06), (0.45, 0.38)]
    assert r(lim[50000.0]["sd"], 2) == 1.32 and r(lim[1000.0]["hedge"], 2) == 0.47
    assert h.best_limits() == {"mean": 10000.0, "mean_less_sd": 5000.0}
    hd = h.herding()
    assert (r(100 * hd[0.0], 1), r(100 * hd[0.995], 1)) == (0.9, 12.9) and round(hd[0.995] / hd[0.0]) == 14
