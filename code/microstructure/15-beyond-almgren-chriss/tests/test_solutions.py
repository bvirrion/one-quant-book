"""Numbers gate: every numerical answer printed in Book 10, chapter 15 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from mx_beyond import aim_grid, liquidity_study, signal_study, transient_study  # noqa: E402


def r(x, d=1):
    return round(float(x), d)


def test_signal():
    s = signal_study()
    assert [r(s[(0.05, x)]["saved"], 2) for x in (0.5, 1.0, 2.0)] == [0.19, 0.75, 2.98]
    assert [r(s[(0.2, x)]["saved"]) for x in (0.5, 1.0, 2.0)] == [1.1, 4.5, 17.2]
    assert [r(s[(1.0, x)]["saved"]) for x in (0.5, 1.0, 2.0)] == [3.1, 11.5, 41.0]
    assert (r(s[(1.0, 2.0)]["saved_se"]), r(s[(1.0, 2.0)]["sd_ac"], 0), r(s[(1.0, 2.0)]["sd_signal"], 0)) == (1.9, 173.0, 212.0)
    assert (r(s[(0.05, 0.5)]["ac"]), r(s[(1.0, 2.0)]["ac"])) == (61.2, 66.4)


def test_transient_aim_liquidity():
    t = transient_study()
    assert (r(t["twap"], 4), r(t["ow"], 4), r(100 * (1 - t["ow"] / t["twap"]), 1)) == (0.0893, 0.0834, 6.6)
    assert (r(t["first"], 4), r(t["block_formula"], 4), r(t["middle"], 4)) == (0.0876, 0.0833, 0.0083)
    g = aim_grid()
    assert (r(g[0.25]["static"][0]), r(g[0.25]["static"][1]), r(g[0.25]["ce_static"])) == (60.9, 90.5, 101.9)
    assert [r(g[a]["ce_adaptive"]) for a in (0.25, 0.5, 1.0, 2.0)] == [100.5, 99.4, 98.6, 103.6]
    assert [r(g[a]["adaptive"][0]) for a in (0.25, 0.5, 1.0, 2.0)] == [61.2, 62.2, 66.2, 81.7]
    assert [r(g[a]["adaptive"][1]) for a in (0.25, 0.5, 1.0, 2.0)] == [88.7, 86.4, 80.4, 66.2]
    assert r(100 * (1 - g[1.0]["ce_adaptive"] / g[1.0]["ce_static"]), 1) == 3.2
    q = liquidity_study()
    assert (r(q["dp"]), r(q["static"]), r(q["saved"]), r(q["saved_se"])) == (73.2, 91.5, 18.3, 0.5)
    assert q["policy_mid"] == (60_000.0, 20_000.0)


def test_exercises():
    # 1: a half-life of 0.2 days in 5-minute steps
    assert r(math.exp(-math.log(2) * (1 / 78) / 0.2), 4) == 0.9565
    # 3: Obizhaeva-Wang blocks with rho = 10 per day: X / 12
    assert r(1 / 12, 4) == 0.0833


def test_exercise_7_noisy_signal():
    import numpy as np
    from firm_execcontrol import lqr_signal, simulate
    from mx_beyond import ETA, LAM, SIGMA, TAU, N, X
    h, s = 1.0, 2.0
    phi = math.exp(-math.log(2) * TAU / h)
    g, ac = lqr_signal(N, TAU, ETA, SIGMA, LAM, phi), lqr_signal(N, TAU, ETA, SIGMA, LAM, 0.0)
    c_ac = simulate(lambda k, x, a, dp: ac[k][0] * x, X, N, TAU, ETA, SIGMA, phi, s, seed=7, paths=1500)
    out = []
    for w in (1.0, 0.5):
        rng = np.random.default_rng(99)
        c = simulate(lambda k, x, a, dp, w=w, rng=rng: g[k][0] * x + g[k][1] * w * (a + s * rng.standard_normal()),
                     X, N, TAU, ETA, SIGMA, phi, s, seed=7, paths=1500)
        out.append(r((c_ac - c).mean() / 50 * 1e4))
    assert out == [8.3, 20.3]
