"""Numbers gate: every numerical answer printed in Book 7, chapter 20 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "overfit"))
from firm_overfit import cpcv_paths, purged_kfold
from rs_overfit import label_leak, minbtl, pbo_hundred, ranking, search, walk_forward_sr


def r(x, d=2):
    return round(float(x), d)


def test_search():
    n, t = search("noise"), search("trend")
    assert (r(n["is_best"]), r(n["oos_best"]), r(n["is_median"]), r(n["oos_mean"])) == (0.44, -0.32, 0.17, 0.20)
    assert (r(t["is_best"]), r(t["oos_best"]), r(t["is_median"]), r(t["oos_mean"])) == (0.77, 0.14, 0.50, 0.26)
    assert (r(n["years"], 1), r(n["expected_max_iid"]), r(n["sr_sd"], 3), r(n["expected_max_obs"])) == (17.9, 0.77, 0.076, 0.25)
    assert (r(n["pbo"]), r(n["slope"]), r(t["pbo"]), r(t["slope"])) == (0.82, -0.89, 0.74, -0.91)
    assert (r(walk_forward_sr("noise")), r(walk_forward_sr("trend"))) == (-0.04, 0.29)
    assert tuple(r(x) for x in ranking("noise")) == (-0.05, -0.02) and tuple(r(x) for x in ranking("trend")) == (0.33, 0.29)


def test_length_and_leak():
    m = minbtl()
    assert (r(m[0.5], 1), r(m[1.0], 1), r(m[1.8], 1)) == (42.4, 10.6, 3.3)
    leak = label_leak()
    assert [r(leak[k]) for k in ("shuffled", "contiguous", "purged", "embargoed")] == [0.90, -0.63, -0.57, -0.93]
    assert tuple(r(x) for x in pbo_hundred()) == (0.69, 0.52)


def test_exercises():
    assert r(math.log(380 / 1001 / (1 - 380 / 1001))) == -0.49
    assert (cpcv_paths(10, 2), cpcv_paths(6, 3)) == (9, 10)
    assert (r(2 * math.log(100), 1), r(2 * math.log(1000), 1)) == (9.2, 13.8)
    import numpy as np

    start = np.arange(400)
    folds = purged_kfold(start, start + 9, k=4, embargo=5)
    train, test = folds[2]
    assert (test[0], test[-1]) == (200, 299)
    dropped = sorted(set(range(400)) - set(train.tolist()) - set(test.tolist()))
    assert dropped == list(range(191, 200)) + list(range(300, 314))
