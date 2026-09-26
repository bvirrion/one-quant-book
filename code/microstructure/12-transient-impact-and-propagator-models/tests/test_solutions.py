"""Numbers gate: every numerical answer printed in Book 10, chapter 12 (text and solutions)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from mx_prop import kernel_family, kernel_study  # noqa: E402, I001
from firm_propagator import impact_matrix, obizhaeva_wang, optimal_liquidation, round_trip  # noqa: E402, I001


def r(x, d=2):
    return round(float(x), d)


def test_kernel_study():
    k = kernel_study()
    assert (k["n"], r(k["gamma"])) == (10_764, 0.62)
    assert [r(k["acf"][i], 3) for i in (1, 10, 50)] == [0.27, 0.106, 0.023]
    assert [r(k["response"][i]) for i in (1, 10, 100)] == [0.52, 1.05, 2.3]
    assert [r(k["G"][i], 3) for i in (1, 10, 100)] == [0.541, 0.452, 0.419]
    assert [r(x) for x in k["var_market"]][::3] == [1.98, 1.36, 1.35]
    assert [r(x) for x in k["var_model"]][::3] == [0.29, 0.56, 1.34]
    assert [r(x) for x in k["var_shuffled"]][::3] == [0.32, 0.24, 0.18]


def test_kernel_family():
    f = kernel_family()
    assert [r(f[k]["round_trip"], 3) for k in (0.5, 1.0, 1.5, 1.8, 2.2, 2.5, 3.0)] == \
        [-0.136, -0.042, -0.008, -0.002, 0.028, 0.091, 0.213]
    assert [f[k]["buys"] for k in (0.5, 1.0, 1.5, 1.8)] == [0, 0, 2, 2]
    assert (r(f[1.5]["min_trade"], 3), r(f[1.8]["min_trade"])) == (-0.086, -0.33)


def test_exercises():
    # 3: Obizhaeva-Wang, X = 10,000 shares, rho = 4 per hour, T = 2 hours
    b0, rate, b1 = obizhaeva_wang(10_000, 4.0, 2.0)
    assert (r(b0, 1), r(rate, 1), r(b1, 1)) == (1000.0, 4000.0, 1000.0)
    # 4: two trades at times 0 and 1 with G(t) = exp(-t): a round trip (+1, -1) costs 1 - exp(-1)
    gam = impact_matrix(np.array([0.0, 1.0]), lambda x: np.exp(-x))
    assert r(-round_trip(gam) * 2, 3) == r(1 - np.exp(-1), 3) == 0.632
    x = optimal_liquidation(gam, 1.0)
    assert (r(x[0]), r(x[1])) == (0.5, 0.5)
    # 6: Lillo-Farmer-style splitting, alpha = 1.5: gamma = alpha - 1
    assert 1.5 - 1 == 0.5


def test_exercise_7_oscillating_round_trip():
    t = np.linspace(0, 1, 21)
    g = impact_matrix(t, lambda x: np.exp(-((x / 0.3) ** 2.5)))
    q, _ = np.linalg.qr(np.column_stack([np.ones(21), np.eye(21)[:, :20]]))
    b = q[:, 1:]
    lam, v = np.linalg.eigh(b.T @ g @ b)
    x = b @ v[:, 0]
    x = x * np.sign(x[0])
    changes = int(np.sum(np.diff(np.sign(x[np.abs(x) > 0.02])) != 0))
    assert (r(lam[0], 3), changes) == (-0.181, 6)
    assert (r(x[0]), r(x[3]), r(x[6]), r(x[10])) == (0.2, -0.26, 0.33, -0.37)
    # 1: predicting the next sign equal to the last
    assert r((1 + 0.27) / 2, 3) == 0.635
