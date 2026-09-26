"""Numbers gate: every numerical answer printed in Book 11, chapter 2 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import hf_fairvalue as f  # noqa: E402

fp = f.fp


def r(x, d=3):
    return round(float(x), d)


def test_estimates_by_hand():
    assert r(fp.weighted_mid(99, 300, 100, 100), 2) == 99.75
    gs, q, rr = f.fitted()
    assert [r(x) for x in gs[0]] == [-0.087, -0.007, 0.022, 0.091, 0.22]
    assert r(fp.micro(99, 300, 100, 100, gs[0]), 2) == 99.59 and r(fp.micro(99, 900, 100, 100, gs[0]), 2) == 99.72
    assert r(q) == 0.047 and [r(x) for x in rr] == [0.104, 0.123, 0.134]


def test_weights():
    w5, w2 = f.weights(0.5), f.weights(2.0)
    assert [r(x, 2) for x in w5["consolidated"]] == [0.73, 0.32]
    assert [r(x, 2) for x in w5["cross"]] == [0.74, 0.22, 0.18]
    assert [r(x, 2) for x in w2["cross"]] == [0.89, -0.09, 0.27]


def test_table():
    t5, t2 = f.table(0.5), f.table(2.0)
    assert [(r(t5[k]["truth"]), r(t5[k]["future"])) for k in f.NAMES] == [
        (0.962, 0.549), (0.963, 0.542), (0.957, 0.536), (0.947, 0.542), (0.961, 0.559), (0.93, 0.529), (0.941, 0.544)]
    assert [r(t5[k]["rel_future"], 1) for k in f.NAMES] == [0.0, -1.3, -2.4, -1.2, 1.8, -3.5, -0.8]
    assert [r(t2[k]["rel_future"], 1) for k in f.NAMES] == [0.0, 0.1, -1.7, -3.0, -0.3, -12.8, -8.7]
    share = (t5["consolidated"]["future"] - t5["cross"]["future"]) / (t5["mid"]["future"] - t5["cross"]["future"])
    assert r(100 * share, 0) == 65


def test_lead_one_second():
    t1 = f.table(1.0)
    assert (r(t1["cross"]["rel_future"], 2), r(t1["cross_filter"]["rel_future"], 2)) == (-7.54, -3.23)


def test_filter_exercises():
    p = 0.02 + 0.05 * 0.4
    k = p / (p + 0.1)
    assert (r(k), r(100 + k, 2)) == (0.286, 100.29)
    for d, pp, kk in ((0.1, 0.02, 0.2), (1.0, 0.05, 0.5)):
        ps = 0.5 * (-0.05 * d + math.sqrt((0.05 * d) ** 2 + 4 * 0.05 * d * 0.1))
        assert (r(ps), r((ps + 0.05 * d) / (ps + 0.05 * d + 0.1))) == (pp, kk)
    flt = fp.FairFilter(0.05, [0.1])
    flt.update(0.0, 0, 100.0)
    for i in range(1, 400):
        flt.update(0.1 * i, 0, 100.0)
    assert np.isclose(flt.p, 0.02)
