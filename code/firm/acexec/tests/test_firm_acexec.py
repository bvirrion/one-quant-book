import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_acexec import (  # noqa: E402
    ACScheduler,
    LinearScheduler,
    cost_var,
    discrete,
    frontier,
    kappa,
    time_to,
    trajectory,
)


def test_continuous_and_discrete_agree():
    k = kappa(eta=0.01, sigma=0.5, lam=0.04)
    assert math.isclose(k, math.sqrt(0.04 * 0.25 / 0.01))
    t = np.linspace(0, 1, 1001)
    d = discrete(1.0, 1.0, 1000, 0.01, 0.5, 0.04)
    assert np.allclose(d, trajectory(1.0, 1.0, k, t), atol=1e-4)
    assert np.allclose(discrete(1.0, 1.0, 4, 0.01, 0.5, 0.0), [1, 0.75, 0.5, 0.25, 0])


def test_cost_variance_and_frontier():
    lin = discrete(1.0, 1.0, 4, 0.01, 0.5, 0.0)
    e, v = cost_var(lin, 1.0, 0.0, 0.01, 0.5)
    assert math.isclose(e, 0.01 * 4 * 0.25**2 / 0.25) and math.isclose(v, 0.25 * 0.25 * (0.75**2 + 0.5**2 + 0.25**2))
    f = frontier(1.0, 1.0, 20, 0.0, 0.01, 0.5, [0.0, 0.1, 1.0, 10.0])
    costs, var = zip(*f, strict=True)
    assert all(a <= b for a, b in zip(costs, costs[1:], strict=False))
    assert all(a >= b for a, b in zip(var, var[1:], strict=False))
    k = kappa(0.01, 0.5, 1.0)
    t = time_to(0.95, k, 10.0)
    assert math.isclose(trajectory(1.0, 10.0, k, t), 0.05) and abs(t - math.log(20) / k) < 1e-6
    assert math.isclose(time_to(0.5, 0.0, 4.0), 2.0)


def test_schedulers():
    s = ACScheduler(1000.0, 10.0, 0.3)
    assert np.isclose(s.targets([0])[0], 1000.0) and np.isclose(s.targets([10, 20])[1], 0.0)
    assert np.allclose(LinearScheduler(100.0, 4.0).targets([0, 1, 2]), [100, 75, 50])
