import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_genmkt import (  # noqa: E402
    GAN,
    VAE,
    Diffusion,
    block_bootstrap,
    c2st,
    fit_garch,
    garch_windows,
    nn_distance,
    scorecard,
    tstr,
    windows,
)


def test_garch_fit_recovers_parameters():
    W = garch_windows((0.0, 0.05, 0.1, 0.85, 6.0), 1, L=6000, seed=3, burn=500)
    mu, om, a, b, nu = fit_garch(W[0])
    assert abs(a - 0.1) < 0.04 and abs(b - 0.85) < 0.05 and 4 < nu < 10


def test_bootstrap_copies_blocks_and_nn_distance_is_zero_for_copies():
    r = np.random.default_rng(0).standard_normal(1000)
    B = block_bootstrap(r, 50, L=20, block=20, seed=1)
    Wr = windows(r, 20)
    assert np.allclose(nn_distance(B, Wr), 0.0, atol=1e-6)
    assert nn_distance(np.random.default_rng(2).standard_normal((20, 20)), Wr).min() > 1.0


def test_c2st():
    rng = np.random.default_rng(0)
    A, B = rng.standard_normal((2000, 32)), rng.standard_normal((2000, 32))
    assert abs(c2st(A, B) - 0.5) < 0.04
    C = rng.standard_t(3, (2000, 32))
    assert c2st(A, C) > 0.7


def test_tstr_recovers_a_planted_predictor():
    rng = np.random.default_rng(1)

    def make(n):
        W = rng.standard_normal((n, 32))
        W[:, -1] += 0.3 * np.sign(W[:, -21:-1].sum(1))
        return W

    ic, sharpe = tstr(make(5000), make(5000))
    assert ic > 0.15 and sharpe > 3
    ic0, _ = tstr(rng.standard_normal((5000, 32)), make(5000))
    assert abs(ic0) < ic


def test_networks_train_deterministically():
    rng = np.random.default_rng(0)
    W = rng.standard_normal((500, 8)) * 0.01
    for M in (VAE, GAN, Diffusion):
        a = M(8).fit(W, steps=50, seed=0).sample(10, seed=1)
        b = M(8).fit(W, steps=50, seed=0).sample(10, seed=1)
        assert a.shape == (10, 8) and np.array_equal(a, b)


def test_diffusion_learns_the_scale():
    rng = np.random.default_rng(0)
    W = rng.standard_normal((2000, 8)) * 0.02
    S = Diffusion(8, T=50).fit(W, steps=600, seed=0).sample(2000, seed=1)
    assert abs(S.std() / 0.02 - 1) < 0.25 and math.isfinite(S.mean())


def test_scorecard_on_gaussian_fails_tails():
    sc = scorecard(np.random.default_rng(0).standard_normal((2000, 32)))
    assert not sc["heavy tails"] and sc["no linear autocorrelation"] and not sc["volatility clustering"]
