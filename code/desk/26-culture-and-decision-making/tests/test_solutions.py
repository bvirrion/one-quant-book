"""Numbers gate: every numerical answer printed in Book 16, chapter 26 (text and solutions)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import fm_culture as m  # noqa: E402

dl = m.dl


def r(x, d=3):
    return round(float(x), d)


def test_hand_numbers():
    assert dl.brier([0.5] * 4, [1, 0, 1, 0]) == 0.25 and r(dl.brier([0.9], [1]), 4) == 0.01
    assert r(dl.brier([0.7, 0.7, 0.7], [1, 1, 0]), 4) == 0.2233
    assert r(float(dl.expit(np.mean(dl.logit([0.6, 0.8])))), 3) == 0.71


def test_year_scores():
    s = m.scores()
    assert [r(s[f"forecaster {k}"]) for k in range(1, 6)] == [0.24, 0.225, 0.252, 0.245, 0.262]
    assert (r(s["truth"]), r(s["mean"]), r(s["log-odds"]), r(s["extremised"])) == (0.214, 0.22, 0.223, 0.237)
    q, y, P = m.year()
    a, e = dl.murphy(P[0], y), dl.murphy(P[4], y)
    g = dl.murphy(dl.aggregate(P, "logodds"), y)
    assert (r(a["reliability"]), r(a["resolution"]), r(e["reliability"]), r(e["resolution"])) == (0.017, 0.027, 0.04, 0.026)
    assert (r(g["reliability"]), r(g["resolution"]), r(g["uncertainty"])) == (0.01, 0.039, 0.25)


def test_five_or_one():
    indep, byrho = m.five_or_one()
    assert r(indep) == 0.207 and [r(byrho[x]) for x in (0.25, 0.5, 0.75, 1.0)] == [0.217, 0.224, 0.231, 0.237]
    assert r(byrho[0.5] - indep) == 0.017 and r(byrho[1.0] - indep) == 0.03


def test_journal():
    j = m.journal()
    ob = dl.outcome_bias(j)
    assert (len(j), ob["lost"], r(100 * ob["share_misjudged_by_outcome"], 1)) == (362, 123, 34.0)
    assert (r(100 * np.mean([e.outcome for e in j]), 1), r(100 * np.mean([e.prob for e in j]), 1)) == (66.0, 77.7)


def test_small_runs():
    q, y, P = m.year(1, 0.0, 50)
    assert P.shape == (5, 50) and ((P > 0) & (P < 1)).all()


def test_exercises():
    assert r(0.5 + 0.5 / 5, 2) == 0.6 and r(1 / 0.6, 2) == 1.67
    s = m.scores()
    avg = np.mean([s[f"forecaster {k}"] for k in range(1, 6)])
    assert r(avg) == 0.245 and r((avg - s["truth"]) / 2, 4) == 0.0154
