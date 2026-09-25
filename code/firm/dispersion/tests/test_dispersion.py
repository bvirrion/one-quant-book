import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_dispersion import average_corr, corr_swap_pnl, dispersion_pnl, realised_var  # noqa: E402


def test_average_corr_recovers_a_common_correlation():
    w = np.array([0.5, 0.3, 0.2])
    vol = np.array([0.2, 0.3, 0.25])
    rho = 0.4
    C = rho * np.outer(vol, vol)
    np.fill_diagonal(C, vol**2)
    var_index = w @ C @ w
    assert math.isclose(float(average_corr(var_index, vol**2, w)), rho)


def test_realised_var_and_legs():
    R = np.array([[0.0, 0.0], [0.01, 0.02], [-0.01, 0.02]])
    assert np.allclose(realised_var(R, 0, 2), [0.0001 * 252, 0.0004 * 252])
    w = np.array([0.5, 0.5])
    # all legs realise their implied variance: zero P&L either way
    assert abs(float(dispersion_pnl(0.2, np.array([0.3, 0.3]), 0.04, np.array([0.09, 0.09]), w))) < 1e-12
    v = float(dispersion_pnl(0.2, np.array([0.3, 0.3]), 0.04, np.array([0.10, 0.10]), w, vega_neutral=True))
    assert math.isclose(v, 0.01 * (0.2 / 0.3))                # member notionals scaled by iv_I / sum w iv_i
    assert corr_swap_pnl(0.3, 0.5) == -0.2
