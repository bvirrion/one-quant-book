import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_teamtenure as tt  # noqa: E402


def test_survival_and_median_on_known_times():
    t = np.array([0.5, 1.0, 2.0, np.inf])
    assert list(tt.survival(t, [0, 1, 3])) == [1.0, 0.5, 0.25]
    assert tt.median_tenure(t) == 1.5 and tt.median_tenure([1.0, 2.0, 3.0]) == 2.0
    assert abs(tt.turnover(t, 4) - 3 / (0.5 + 1 + 2 + 4)) < 1e-12


def test_skill_and_wider_ladder_lengthen_tenure():
    lad, wide = tt.Ladder(0.05, 0.075), tt.Ladder(0.10, 0.15)
    a = tt.stop_times(0.5, 0.08, lad, 400, 5, np.random.default_rng(1))
    b = tt.stop_times(1.5, 0.08, lad, 400, 5, np.random.default_rng(2))
    c = tt.stop_times(0.5, 0.08, wide, 400, 5, np.random.default_rng(1))
    assert np.isfinite(a).mean() > np.isfinite(b).mean() > 0
    assert np.isfinite(c).mean() < np.isfinite(a).mean()


def test_false_cut_share():
    d = {0.0: np.array([1.0, np.inf]), 1.0: np.array([2.0, 3.0, np.inf])}
    assert tt.false_cut_share(d, {1.0}) == 2 / 3
