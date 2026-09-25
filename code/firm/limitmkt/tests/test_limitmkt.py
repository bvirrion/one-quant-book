import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_limitmkt import LimitConfig, apply_limits, holdings_seen, northbound  # noqa: E402


def test_lock_backlog_attention_and_fill():
    R = np.zeros((4, 1))
    R[1, 0] = 0.15 / 1.5                                     # a fair move of 15% after scaling
    cfg = LimitConfig(push=0.0)
    o = apply_limits(R, cfg, np.random.default_rng(0))
    ub = math.log1p(0.10)
    assert o["up"][1, 0] and not o["up"][2, 0]
    assert math.isclose(o["close"][1, 0], ub)
    assert math.isclose(o["fill"][1, 0], math.exp(-(math.log1p(0.15) - ub) / 0.02))
    # the next open carries the backlog and the attention premium
    assert math.isclose(o["open"][2, 0], math.log1p(0.15) + 0.03)
    assert math.isclose(o["premium"][3, 0], 0.03 * 0.6)


def test_magnet_pushes_near_the_limit():
    R = np.zeros((2, 1))
    R[1, 0] = 0.09 / 1.5
    o = apply_limits(R, LimitConfig(push=1.0), np.random.default_rng(0))
    assert o["pushed"][1, 0] and o["fill"][1, 0] == 1.0
    assert math.isclose(o["close"][1, 0], math.log1p(0.10))
    o = apply_limits(R, LimitConfig(push=0.0), np.random.default_rng(0))
    assert not o["up"][1, 0] and math.isclose(o["close"][1, 0], math.log1p(0.09))


def test_holdings_published_late_and_rarely():
    f = np.ones((10, 1))
    assert holdings_seen(f, 1, 0)[:, 0].tolist() == list(range(1, 11))
    seen = holdings_seen(f, 4, 2)[:, 0]
    assert np.isnan(seen[:2]).all() and seen[2:6].tolist() == [1, 1, 1, 1] and seen[6:10].tolist() == [5, 5, 5, 5]


def test_northbound_skill():
    rng = np.random.default_rng(1)
    a = rng.standard_normal((200, 500))
    f = northbound(a, 0.3, np.random.default_rng(2))
    assert abs(np.corrcoef(a.ravel(), f.ravel())[0, 1] - 0.3) < 0.01
