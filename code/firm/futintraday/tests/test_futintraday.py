import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_futintraday import SessionConfig, fade, orb, pre_announcement, simulate_sessions  # noqa: E402


def test_session_volatility_and_bounce():
    S = simulate_sessions(SessionConfig(days=4000, trend_sd=0.0, pre_drift=0.0), np.random.default_rng(1))
    day = S["r"].sum(1) + S["gap"]
    # the bounce shrinks the session's variance by (1 - 0.1)^2 over a day
    assert abs(day.std() * math.sqrt(252) / (0.16 * math.sqrt(0.25 + 0.75 * 0.81)) - 1) < 0.03
    ac = np.corrcoef(S["r"][:, 1:].ravel(), S["r"][:, :-1].ravel())[0, 1]
    assert abs(ac + 0.1) < 0.01


def test_strategies_by_hand():
    r = np.zeros((1, 10))
    r[0, 0], r[0, 1] = 0.001, -0.001                  # opening range [0, 0.001] over two minutes
    r[0, 3], r[0, 6] = 0.002, 0.001                   # breakout up at minute 3, close 0.004 above the entry's base
    S = {"r": r, "gap": np.zeros(1), "ann": np.array([False]), "ann_minute": 5}
    assert math.isclose(orb(S, 2, 0.0001)[0], (0.003 - 0.002) - 0.0002)
    r2 = np.zeros((2, 10))
    r2[1, :3] = 0.001
    S2 = {"r": r2, "gap": np.array([0.0, 0.002]), "ann": np.array([False, True]), "ann_minute": 3}
    assert math.isclose(pre_announcement(S2, 0.0)[1], 0.002 + 0.003)
    assert fade({"r": np.zeros((1, 20))}, 5, 2.0, 5, 0.0)[0] == 0.0
