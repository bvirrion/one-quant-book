import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_creditrv import CreditConfig, _banded, negative_basis, simulate_credit  # noqa: E402


def test_basis_is_minus_funding_without_noise():
    cfg = CreditConfig(issuers=3, days=1500, bond_noise=0.0, cds_disp=0.0)
    s = simulate_credit(cfg)
    assert np.allclose(s["basis"], -s["fund"][:, None]) and s["fund"][cfg.stress_start + cfg.stress_ramp] == 150.0


def test_negative_basis_carry_and_marks_by_hand():
    cfg = CreditConfig()
    sim = {"bond": np.array([[150.0], [160.0], [160.0]]), "cds": np.array([[100.0], [100.0], [100.0]])}
    nb = negative_basis(sim, cfg, 30.0)
    assert np.allclose(nb["carry"] * 1e4 * 252, [50 - 27, 60 - 27])
    assert np.allclose(nb["marks"] * 1e4, [-4.5 * 10, 0.0])
    assert np.allclose(nb["on_capital"], nb["total"] / 0.1)


def test_banded_position():
    pos = _banded(np.array([0.5, 1.5, 0.8, -0.2, -1.2, -0.1, 0.3]), 1.0, 1.0)
    assert pos.tolist() == [0.0, 1.0, 1.0, 0.0, -1.0, -1.0, 0.0]
