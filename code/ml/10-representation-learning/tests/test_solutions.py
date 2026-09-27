"""Numbers gate: every numerical answer printed in Book 12, chapter 10 (text and solutions)."""
import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import ml_represent as m  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


# Printed digits that move with the CPU's floating-point kernels: skipped by CI (make test-fast).
@pytest.mark.reference
def test_learning_curve():
    a, b, c = m.compare(300), m.compare(1000), m.compare(0)
    assert (r(a["predictive probe"]), r(a["raw ridge"]), r(a["from scratch"])) == (0.22, 0.12, 0.18)
    assert (r(a["autoencoder probe"]), r(a["contrastive probe"]), r(a["features ridge"])) == (0.15, 0.05, 0.05)
    assert a["features ridge"] < a["contrastive probe"]
    assert (r(b["predictive probe"]), r(b["raw ridge"]), r(b["from scratch"]), r(b["features ridge"])) == (
        0.29, 0.24, 0.20, 0.50)
    assert b["autoencoder probe"] < b["raw ridge"] and b["contrastive probe"] < b["raw ridge"]
    assert (r(c["raw ridge"]), r(c["predictive probe"]), r(c["predictive fine-tuned"]), r(c["from scratch"])) == (
        0.45, 0.40, 0.46, 0.38)
    assert (r(c["autoencoder probe"]), r(c["contrastive probe"]), r(c["features ridge"])) == (0.31, 0.31, 0.55)
    assert r(c["predictive fine-tuned"] - c["from scratch"]) == 0.08


def test_exercises():
    assert (2 * 256 - 1, r(math.log(511))) == (511, 6.24)
    assert (300 * 0.5 / 60, r(4444 * 0.5 / 60, 1)) == (2.5, 37.0)
    assert (400 * 64 + 64 + 64 * 16 + 16, 17) == (26704, 17)
    assert r(m.compare(1000, ahead=16)["predictive probe"], 3) == 0.204
