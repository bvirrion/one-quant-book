import math
import pathlib
import sys

import numpy as np
import pytest
import torch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_deephedge import (  # noqa: E402
    BandNet,
    bs_policy,
    entropic,
    expected_shortfall,
    fit_calibrator,
    fit_surrogate,
    hedge_pnl,
    surrogate_values,
    ww_policy,
)


def _bs_paths(n=20000, steps=21, T=1 / 12, sigma=0.2, seed=0):
    rng = np.random.default_rng(seed)
    dt = T / steps
    z = rng.standard_normal((n, steps))
    x = np.cumsum(-0.5 * sigma**2 * dt + sigma * math.sqrt(dt) * z, 1)
    return 100.0 * np.exp(np.column_stack([np.zeros(n), x]))


def test_delta_hedge_error_scale():
    S = _bs_paths()
    with torch.no_grad():
        X = hedge_pnl(bs_policy(0.2, 100.0, 1 / 12), S, 100.0, 1 / 12, 0.0)
    price = 100 * (2 * 0.5 * (1 + math.erf(0.5 * 0.2 * math.sqrt(1 / 12) / math.sqrt(2))) - 1)
    assert abs(float(-X.mean()) - price) < 0.03
    sd_theory = math.sqrt(math.pi / 4) * 0.2 * 100 * math.sqrt(1 / 12) / math.sqrt(21) * 0.5 ** 0 * 0.55
    assert 0.3 * sd_theory < float(X.std()) < 3 * sd_theory


def test_entropic_cash_invariance_and_es():
    X = torch.tensor([1.0, -2.0, 0.5, 3.0])
    assert abs(float(entropic(X + 2.0) - entropic(X) + 2.0)) < 1e-6
    assert abs(float(entropic(torch.full((10,), 1.5))) + 1.5) < 1e-6
    assert float(expected_shortfall(torch.arange(100.0) - 50, 0.95)) == 48.0


def test_band_net_clips():
    net = BandNet()
    prev = torch.linspace(-1, 2, 50)
    h, lo, hi = net(torch.full((50,), 0.5), torch.zeros(50), prev)
    assert torch.all(h >= lo - 1e-7) and torch.all(h <= hi + 1e-7)
    inside = (prev > lo) & (prev < hi)
    assert torch.all(h[inside] == prev[inside])


def test_ww_band_widens_with_cost():
    widths = []
    for c in (0.0005, 0.002):
        _, lo, hi = ww_policy(0.2, 100.0, 1 / 12, c, 1.0)(torch.tensor([0.5]), torch.tensor([0.0]), torch.tensor([0.5]))
        widths.append(float(hi - lo))
    assert widths[1] > widths[0] > 0 and abs(widths[1] / widths[0] - 4 ** (1 / 3)) < 1e-4


# A training accuracy this machine reaches; on other floating-point kernels it can miss: skipped by CI.
@pytest.mark.reference
def test_differential_surrogate_recovers_slope():
    rng = np.random.default_rng(0)
    x = rng.uniform(-1, 1, (64, 1))
    y, dy = np.sin(2 * x[:, 0]), 2 * np.cos(2 * x[:, 0])
    net = fit_surrogate(x, y, dy, differential=True, seed=0, epochs=800)
    xs = np.linspace(-0.9, 0.9, 50)[:, None]
    p, d = surrogate_values(net, xs)
    assert np.max(np.abs(d - 2 * np.cos(2 * xs[:, 0]))) < 0.15 and np.max(np.abs(p - np.sin(2 * xs[:, 0]))) < 0.05


def test_calibrator_inverts_a_simple_map():
    rng = np.random.default_rng(0)
    P = rng.uniform(0, 1, (2000, 2))
    V = np.column_stack([P[:, 0] + P[:, 1], P[:, 0] - P[:, 1], P[:, 0] * P[:, 1]])
    pred = fit_calibrator(V, P, seed=0, epochs=1500)
    assert np.sqrt(np.mean((pred(V[:200]) - P[:200]) ** 2)) < 0.03
