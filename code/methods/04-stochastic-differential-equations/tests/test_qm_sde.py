"""Tutorial of Book 4, Chapter 4: the printed steps reproduce the printed end state."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from qm_sde import gamma_cdf, stationary_gamma


def test_gamma_cdf_integrates_the_density():
    grid = np.linspace(1e-6, 0.2, 200_001)
    dens = stationary_gamma(grid, 2.0, 0.04, 0.2)
    assert abs(np.trapezoid(dens, grid) - gamma_cdf(0.2, 4.0, 0.01)) < 1e-4
    assert abs(gamma_cdf(50.0, 1.0, 1.0) - 1) < 1e-12 and abs(gamma_cdf(1.0, 1.0, 1.0) - (1 - np.exp(-1))) < 1e-12
