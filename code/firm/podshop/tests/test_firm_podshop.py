import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_podshop as ps  # noqa: E402


def test_payout_carry_forward_no_clawback():
    ann = np.array([[0.10, -0.05], [-0.04, 0.03], [0.06, 0.04]])
    p = ps.payouts(ann, 0.2)
    assert np.allclose(p[:, 0], [0.02, 0.0, 0.004])       # year 3 pays only above the carried 0.04
    assert np.allclose(p[:, 1], [0.0, 0.0, 0.004])        # 0.03 does not cover the 0.05 loss; 0.04 exceeds the rest
    nc = ps.netting_cost(ann, 0.2)
    assert math.isclose(nc[0], 0.02 - 0.2 * 0.05) and nc[1] == 0.0


def test_expected_positive_matches_monte_carlo():
    rng = np.random.default_rng(3)
    x = rng.normal(0.5, 1.0, 400_000)
    assert abs(ps.expected_positive(0.5, 1.0) - np.maximum(x, 0).mean()) < 0.005
    assert math.isclose(ps.expected_positive(0.0, 2.0), 2.0 / math.sqrt(2 * math.pi))


def test_pods_moments_and_waterfall_identity():
    rng = np.random.default_rng(7)
    s = ps.pods(20, 40, 0.8, 0.10, 0.2, rng)
    ann = ps.annual(s["daily"])
    assert ann.shape == (40, 20)
    assert abs(ann.mean() - 0.08) < 0.01 and abs(ann.std() - 0.10) < 0.01
    c = np.corrcoef(ann.T)[np.triu_indices(20, 1)].mean()
    assert abs(c - 0.2) < 0.08
    w = ps.waterfall(ann, ps.Terms())
    assert math.isclose(w["gross"] - w["payouts"] - w["costs"] - w["manager"], w["investor"], abs_tol=1e-12)


def test_ladder_and_overlay():
    daily = np.zeros((252, 1))
    daily[10:20, 0] = -0.01          # a 10 % drawdown over ten days
    out, ev = ps.ladder(daily, 0.05, 0.075)
    assert [e[0] for e in ev] == ["cut", "stop"]
    assert out[10:20, 0].sum() > -0.10 and out[25:, 0].sum() == 0
    rng = np.random.default_rng(1)
    s = ps.pods(30, 20, 0.5, 0.10, 0.3, rng)
    hedged = ps.overlay(s["daily"], s["beta"], s["factor"])
    assert hedged.std() < s["daily"].mean(1).std()


def test_firing_resets_carry_and_raises_payouts():
    ann = np.array([[-0.20], [0.10]])
    assert ps.payouts(ann, 0.2)[1, 0] == 0.0
    assert np.isclose(ps.payouts(ann, 0.2, fire=0.15)[1, 0], 0.02)
    assert np.isclose(ps.payouts(ann, 0.2, carry=False)[1, 0], 0.02)
