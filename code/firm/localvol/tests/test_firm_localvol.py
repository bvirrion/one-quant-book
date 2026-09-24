"""Acceptance tests of the Book 5, Chapter 9 build (local volatility)."""
import math
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "bs"))
from firm_bs import implied_vol
from firm_localvol import build_grid, local_variance, simulate


def test_flat_surface_gives_flat_local_vol():
    assert abs(math.sqrt(local_variance(lambda k, t: 0.04 * t, 0.2, 0.5)) - 0.2) < 1e-6


def test_term_structure_gives_forward_vols():
    def w(k, t):
        return 0.04 * t + 0.02 * t * t                    # instantaneous variance 0.04 + 0.04 t
    assert abs(local_variance(w, 0.0, 0.5) - (0.04 + 0.04 * 0.5)) < 1e-6


def test_arbitrage_raises():
    with pytest.raises(ValueError):
        local_variance(lambda k, t: 0.04 * t - 0.5 * k * k * t, 0.3, 0.5)      # concave smile
    with pytest.raises(ValueError):
        local_variance(lambda k, t: 0.04 * (1 - t) * t, 0.0, 0.9)             # total variance falling in time


def test_simulation_reprices_flat_vol():
    g = build_grid(lambda k, t: 0.04 * t, np.array([0.01, 0.5, 1.0]), np.linspace(-1, 1, 21))
    st, _ = simulate(g, 100.0, 0.5, 126, 200_000, 3)
    pay = np.maximum(st - 100, 0).mean()
    assert abs(implied_vol(float(pay), 100, 100, 0.5, 1.0, "C") - 0.2) < 0.002
