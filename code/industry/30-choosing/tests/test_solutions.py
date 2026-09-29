"""Numbers gate: every numerical answer printed in Book 17, chapter 30 (text and solutions)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import in_choose as a  # noqa: E402

fd = a.fd


def r(x, d=3):
    return round(float(x), d)


def test_table():
    m = a.matrix()
    assert [round(x / 1000) for x in m[:, 0]] == [1618, 1949, 1703, 1191]
    assert [r(x, 2) for x in m[:, 1]] == [1.01, 1.16, 1.67, 1.22]
    assert [r(100 * x, 1) for x in m[:, 2]] == [53.1, 40.8, 50.0, 55.3]
    assert [r(x, 1) for x in m[:, 3]] == [0.0, 3.8, 0.0, 5.1] and [r(x, 2) for x in m[:, 5]] == [1.0, 1.0, 0.65, 1.0]
    assert {k: round(v) for k, v in a.ce3().items()} == {"bank quant": 1_186_354, "market maker": 1_365_186,
                                                        "platform analyst": 903_603, "technology engineer": 845_964}
    assert round(m[1, 0]) == 1_949_485


def test_results():
    res = a.results()
    assert [r(v) for v in res["values"]] == [0.584, 0.852, 0.589, 0.202] and res["dominated"] == [3]
    assert [r(100 * x, 1) for x in res["ra"][:, 0]] == [15.9, 79.5, 4.6, 0.0]
    shift, best = res["flip"]
    assert (r(shift), best, r(0.15 + shift)) == (0.452, 0, 0.602)


def test_exercises():
    s = a.scaled()
    v = fd.value(s, fd.swing_weights((30, 15, 10, 15, 60, 10)))
    assert (r(v[1]), r(v[2]), int(np.argmax(v))) == (0.894, 0.706, 1)
    s3 = fd.scale(a.matrix()[:3], a.HIGHER)
    ra = fd.rank_acceptability(s3, 20_000, np.random.default_rng(30))
    assert [r(100 * x, 1) for x in ra[:, 0]] == [13.5, 81.4, 5.1]
    assert [r(x, 2) for x in fd.swing_weights(a.SWING)] == [0.3, 0.15, 0.1, 0.15, 0.2, 0.1]


def test_small_runs():
    assert fd.dominated(a.matrix(), a.HIGHER) == [3]
