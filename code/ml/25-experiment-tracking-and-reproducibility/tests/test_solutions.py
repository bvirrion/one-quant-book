"""Numbers gate: every numerical answer printed in Book 12, chapter 25 (text and solutions)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import ml_track as m  # noqa: E402


def test_study():
    s = m.summary()
    assert (s["runs"], s["trials logged"]) == (200, 200)
    assert (round(s["best valid"], 2), round(s["median valid"], 2), round(s["test"], 2)) == (2.22, -0.83, 0.91)
    assert (round(s["dsr 200"], 2), round(s["psr 1"], 2), round(m.null_max(), 2)) == (0.15, 0.96, 3.58)
    v = [r["metrics"]["valid sharpe"] for r in m.study()["tracker"].runs()]
    assert round(min(v), 2) == -3.16


def test_reproduction():
    r = m.reproduction()
    assert r["registry"] and r["audit intact"]
    got = {k: (r[k][0], round(r[k][1], 2)) for k in ("params", "seed", "data", "code")}
    assert got == {"params": (False, -1.28), "seed": (False, 0.85), "data": (False, -1.25), "code": (False, -0.44)}
    reg = m.study()["registry"]
    assert reg.as_of("xs-gbdt", "2026-03-10T08:00")["version"] == 1 and reg.as_of("xs-gbdt", "2026-03-01T08:00") is None


def test_seed_spread():
    s = np.array(m.seed_spread())
    assert (round(s.min(), 2), round(s.max(), 2), round(s.mean(), 2), round(s.std(ddof=1), 2)) == (-0.2, 2.88, 1.03, 0.94)
