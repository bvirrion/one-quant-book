"""Numbers gate: every numerical answer printed in Book 12, chapter 11 (text and solutions)."""
import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import ml_uncert as m  # noqa: E402


def row(r):
    return (round(1e4 * r["crps"], 1), round(100 * r["cov90"], 1))


def test_scores():
    s = m.scores()
    assert (row(s["boosted quantiles"]["before"]), row(s["boosted quantiles"]["after"])) == ((78.9, 89.4), (136.3, 85.0))
    assert (row(s["Gaussian network"]["before"]), row(s["Gaussian network"]["after"])) == ((79.0, 90.6), (135.3, 87.0))
    assert (row(s["ensemble of 5"]["before"]), row(s["ensemble of 5"]["after"])) == ((79.1, 91.1), (135.4, 87.6))
    assert (row(s["mixture density"]["before"]), row(s["mixture density"]["after"])) == ((78.8, 89.7), (136.1, 86.1))
    assert (row(s["truth (Gaussian)"]["before"]), row(s["truth (Gaussian)"]["after"])) == ((78.9, 91.2), (135.5, 91.3))
    assert round(100 * s["epistemic_share"], 2) == 0.09
    before = [s[k]["before"]["crps"] for k in ("boosted quantiles", "Gaussian network", "ensemble of 5",
                                               "mixture density", "truth (Gaussian)")]
    assert 1e4 * (max(before) - min(before)) < 0.3                      # within a quarter of a basis point


# Printed digits that move with the CPU's floating-point kernels: skipped by CI (make test-fast).
@pytest.mark.reference
def test_conformal():
    c = m.conformal()
    got = {t: {k: round(100 * v, 1) for k, v in c[t].items()} for t in ("before", "after")}
    assert got == {"before": {"raw": 90.7, "normalised": 90.3, "adaptive": 89.9},
                   "after": {"raw": 74.0, "normalised": 86.9, "adaptive": 90.1}}
    assert round(100 * m.conformal(gamma=0.02)["after"]["adaptive"], 1) == 90.0


def test_sizing():
    r = {k: round(float(v.mean()), 2) for k, v in m.sizing().items()}
    assert r == {"reading": 1.72, "reading / EWMA variance": 1.90, "reading / network variance": 1.91,
                 "reading / true variance": 1.93, "true mean": 2.94, "true mean / true variance": 3.31}


def test_exercises():
    assert (round(0.95 * 1.0, 2), round(-0.05 * -1.0, 2)) == (0.95, 0.05)
    assert (math.ceil(251 * 0.9), math.ceil(5041 * 0.9)) == (226, 4537)
    assert round(250**2 / 80**2, 1) == 9.8
    assert round(math.sqrt(1 / 3), 2) == 0.58
