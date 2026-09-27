"""Numbers gate: every numerical answer printed in Book 12, chapter 7 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import ml_nets as m  # noqa: E402


def r(x, d=3):
    return round(float(x), d)


# Printed digits that move with the CPU's floating-point kernels: skipped by CI (make test-fast).
@pytest.mark.reference
def test_seeds():
    s = m.seed_study()
    a, b = s["small"], s["large"]
    assert (r(a.min()), r(a.max()), r(a.mean(), 4), r(a.std(ddof=1), 4), r(b.mean(), 4)) == (
        0.057, 0.065, 0.0601, 0.0023, 0.0619)
    assert (r(s["gap"], 4), r(s["sd"], 4), round(s["seeds_needed"])) == (0.0019, 0.0024, 14)
    assert round(s["sd"] * math.sqrt(2), 4) == 0.0035 and round((a.max() - a.min()) / s["gap"]) == 4
    r2 = [100 * m.net(m.SMALL, k)["r2"] for k in range(1, 11)]
    sr = [m.net(m.SMALL, k)["ls_sr_net"] for k in range(1, 11)]
    assert (r(min(r2), 2), r(max(r2), 2), r(min(sr), 2), r(max(sr), 2)) == (0.08, 0.30, 1.37, 1.78)
    epochs = [m.net(m.SMALL, k)["best_epoch"] for k in range(1, 11)] + [m.net(m.LARGE, k)["best_epoch"]
                                                                       for k in range(1, 11)]
    assert min(epochs) >= 1 and max(epochs) <= 4 and [m.net(m.SMALL, k)["best_epoch"] for k in (1, 2, 3)] == [2, 2, 4]


# Printed digits that move with the CPU's floating-point kernels: skipped by CI (make test-fast).
@pytest.mark.reference
def test_ensembles_and_ablation():
    e = m.ensemble()
    assert (r(e["ic"]), r(100 * e["r2"], 2), r(e["ls_sr_net"], 2), r(m.ensemble(hidden=m.LARGE)["ic"])) == (
        0.066, 0.32, 1.73, 0.066)
    assert [r(m.ensemble(n)["ic"], 4) for n in (1, 2, 5, 10)] == [0.0602, 0.0625, 0.0659, 0.0662]
    a = {k: r(v.mean()) for k, v in m.ablation().items()}
    assert a == {"plain": 0.059, "dropout 0.2": 0.062, "weight decay 0.01": 0.059, "batch norm": 0.052,
                 "layer norm": 0.056}
    b = m.baselines()
    assert (r(b["ridge"]["ic"]), r(b["ridge"]["ls_sr_net"], 2), r(b["boosting"]["ic"]), r(b["boosting"]["ls_sr_net"], 2)
            ) == (0.060, 1.59, 0.075, 2.02)


def test_exercises():
    def count(sizes):
        return sum(a * b + b for a, b in zip(sizes[:-1], sizes[1:], strict=True))

    assert (count([40, 32, 16, 1]), count([40, 64, 32, 16, 1])) == (1857, 5249)
    assert round(8 * 0.003**2 / 0.001**2) == 72
    assert (math.ceil(160000 / 512), math.ceil(100000 / 512)) == (313, 196)
    assert round(100 * (0.0625 - 0.0602) / (0.0662 - 0.0602)) == 38 and round(100 * (0.0659 - 0.0602) / 0.006) == 95
    assert np.isclose(0.059, 0.059)
