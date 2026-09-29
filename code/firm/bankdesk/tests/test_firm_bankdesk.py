import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_bankdesk as bd  # noqa: E402

REPO = bd.Desk("repo", 2.0, 0.6, 15.0, 400.0, 0.8)
EQD = bd.Desk("eqd", 5.0, 2.8, 70.0, 120.0, 5.0)


def test_keys_and_binding():
    k = bd.Keys()
    e = bd.allocate([REPO, EQD], k)
    assert np.allclose(e["rwa"], [1.95, 9.1]) and np.allclose(e["leverage"], [20.0, 6.0])
    assert np.allclose(e["binding"], [20.0, 9.1])
    assert bd.binding(REPO, k) == "leverage" and bd.binding(EQD, k) == "rwa"
    r = bd.roae([REPO], e["leverage"][:1], k.tax)
    assert math.isclose(r[0], 1.4 * 0.75 / 20.0)


def test_charge_breakeven():
    c = bd.breakeven_charge(REPO)
    assert math.isclose(bd.balance_sheet_charge(REPO, c, 0.25), 0.0, abs_tol=1e-12)
    assert bd.balance_sheet_charge(REPO, 2 * c, 0.25) < 0


def test_optimal_mix_respects_constraints():
    k = bd.Keys()
    x = bd.optimal_mix([REPO, EQD], 20.0, k)
    assert k.k_rwa * (REPO.rwa * x[0] + EQD.rwa * x[1]) <= 20.0 + 1e-9
    assert k.k_le * (REPO.le * x[0] + EQD.le * x[1]) <= 20.0 + 1e-9
    assert x[1] > x[0]
