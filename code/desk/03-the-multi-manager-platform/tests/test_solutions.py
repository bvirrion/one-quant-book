"""Numbers gate: every numerical answer printed in Book 16, chapter 3 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import fm_platform as m  # noqa: E402

ps = m.ps


def r(x, d=2):
    return round(float(x), d)


@pytest.mark.reference
def test_waterfall_and_classic():
    w = m.waterfall()
    assert [r(100 * w[k]) for k in ("gross", "payouts", "costs", "manager", "investor")] == [20.09, 4.27, 4.0, 2.38, 9.44]
    assert w["loss_years"] == 9 and w["years"] == 400
    c = m.classic()
    assert (r(100 * c["fees"]), r(100 * c["investor"])) == (5.62, 14.47)
    assert r(100 * (c["fees"] - w["payouts"] - w["costs"])) == -2.65
    assert r(100 * (w["payouts"] + w["costs"]) / w["gross"], 1) == 41.2 and r(100 * w["investor"] / w["gross"], 1) == 47.0
    n = m.waterfall(fire=None)
    assert (r(100 * n["payouts"]), r(100 * n["investor"])) == (4.04, 9.63)


def test_closed_forms():
    assert r(ps.expected_positive(1.0, 1.0), 4) == 1.0833
    shares = [m.netting_closed_form(s) / (s * m.VOL) for s in (1.0, 0.5, 0.25)]
    assert [r(100 * x, 1) for x in shares] == [1.7, 7.9, 22.9]
    assert r(0.2 * math.sqrt((1 + 49 * 0.1) / 50), 4) == 0.0687 and r(0.2 * math.sqrt(0.9 / 50), 4) == 0.0268


@pytest.mark.reference
def test_netting_simulated():
    v = {s: sim for s, sim, _ in m.netting_vs_sr()}
    assert (r(100 * v[1.0], 1), r(100 * v[0.5], 1)) == (1.3, 6.2)
    assert r(100 * m.netting_share(fire=None)[1], 1) == 0.1


@pytest.mark.reference
def test_ladder_and_overlay():
    e = m.ladder_effect()
    assert (r(100 * e["cut_share"], 1), r(100 * e["stop_share"], 1)) == (88.4, 26.6)
    assert [r(100 * e["base"][0], 1), r(100 * e["ladder"][0], 1), r(100 * e["base"][1], 1), r(100 * e["ladder"][1], 1)] == [
        20.1, 13.4, 6.9, 4.8]
    assert (r(e["base"][2]), r(e["ladder"][2])) == (2.92, 2.77)
    q = m.ladder_effect(0.20, 0.30, seeds=range(1, 6))
    assert r(100 * q["cut_share"], 0) == 26
    b, a = m.overlay_effect()
    assert (r(100 * b[1], 1), r(100 * a[1], 1), r(b[2], 1), r(a[2], 1), r(100 * a[0], 1)) == (6.9, 2.7, 2.9, 7.5, 20.1)


def test_hand_examples():
    assert r(0.2 * 0.12 * 500, 1) == 12.0
    p = ps.payouts(np.array([[-0.05], [0.12]]), 0.2)
    assert r(p[1, 0] * 500, 1) == 7.0
    two = ps.payouts(np.array([[0.10, -0.10]]), 0.2)
    assert r(two.sum() * 100, 1) == 2.0 and r(ps.netting_cost(np.array([[0.10, -0.10]]), 0.2)[0] * 100, 1) == 2.0


def test_small_runs():
    """Machine-independent properties at reduced size (CI)."""
    w = m.waterfall(seeds=range(1, 3), years=5)
    assert abs(w["gross"] - w["payouts"] - w["costs"] - w["manager"] - w["investor"]) < 1e-12
    s, cf = m.netting_share(seeds=range(1, 3), years=5, sr=0.5)[1], m.netting_closed_form(0.5) / 0.1
    assert 0 < s < 1 and cf > 0
    e = m.ladder_effect(seeds=range(1, 2))
    assert e["ladder"][1] < e["base"][1]


def test_diversification_table():
    t = m.diversification_table()
    want = {(10, 0.05): 2.63, (25, 0.05): 3.37, (50, 0.05): 3.81, (100, 0.05): 4.10, (10, 0.1): 2.29, (25, 0.1): 2.71,
            (50, 0.1): 2.91, (100, 0.1): 3.03, (10, 0.2): 1.89, (25, 0.2): 2.08, (50, 0.2): 2.15, (100, 0.2): 2.19}
    assert all(r(t[k]) == v for k, v in want.items())
    assert r(1 / math.sqrt(0.1)) == 3.16
