import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_synthfut import FutConfig, contracts, curve, season, simulate_futures  # noqa: E402


def test_shapes_classes_and_determinism():
    cfg = FutConfig(years=4, per_class=3)
    F, G = simulate_futures(cfg), simulate_futures(cfg)
    assert F["r"].shape == (1008, 12) and F["cls"].tolist() == [0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3]
    assert np.array_equal(F["r"], G["r"]) and F["names"][0] == "EQU01" and F["names"][-1] == "COM03"


def test_volatility_by_class():
    F = simulate_futures(FutConfig(years=20, crashes=()))
    vols = [F["r"][:, F["cls"] == k].std() * math.sqrt(252) for k in range(4)]
    for v, target in zip(vols, (0.16, 0.06, 0.09, 0.25), strict=True):
        assert abs(v / target - 1) < 0.15


def test_crash_moves_equities_down():
    cfg = FutConfig(years=10, crash_move=(-0.9, 0.0, 0.0, 0.0))
    F = simulate_futures(cfg)
    s, e = F["crashes"][0]
    assert F["r"][s:e, F["cls"] == 0].mean(1).sum() < -0.5


def test_curve_carry_and_season():
    F = simulate_futures(FutConfig(years=2, per_class=2))
    t = 100
    c = curve(F, t, [0, 252])
    s0, s1 = season(F["amp"], F["phase"], t), season(F["amp"], F["phase"], t + 252)
    assert np.allclose(s0, s1) and np.allclose(c[:, 0] - c[:, 1], F["carry"][t])
    assert np.allclose(c[:, 0], F["x"][t] + s0)
    k = contracts(F, 100, 3, 21)
    assert np.allclose(k, curve(F, 100, [5, 26, 47]))
