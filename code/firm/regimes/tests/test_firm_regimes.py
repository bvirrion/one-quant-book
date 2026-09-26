import itertools
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_regimes import (  # noqa: E402
    GaussianHMM,
    ari,
    hier_clusters,
    iforest_scores,
    kmeans_clusters,
    market_residuals,
    regime_series,
)


def test_clustering_recovers_separated_groups():
    rng = np.random.default_rng(0)
    f = rng.standard_normal((500, 3))
    groups = np.repeat(np.arange(3), 10)
    R = f[:, groups] + 0.5 * rng.standard_normal((500, 30)) + rng.standard_normal((500, 1))
    E = market_residuals(R)
    assert ari(kmeans_clusters(E, 3), groups) == 1.0 and ari(hier_clusters(E, 3), groups) == 1.0


def test_hmm_recovers_parameters():
    x, s = regime_series(6000, (0.0, 0.0), (0.01, 0.03), [[0.98, 0.02], [0.05, 0.95]], seed=1)
    h = GaussianHMM(2).fit(x)
    assert abs(h.sd[0] - 0.01) < 0.001 and abs(h.sd[1] - 0.03) < 0.003 and abs(h.P[0, 0] - 0.98) < 0.01
    assert np.mean(h.viterbi(x) == s) > 0.95


def test_filter_uses_no_future_data_and_agrees_with_smoother_at_the_end():
    x, _ = regime_series(1000, (0.0, 0.0), (0.01, 0.03), [[0.98, 0.02], [0.05, 0.95]], seed=2)
    h = GaussianHMM(2).fit(x)
    y = x.copy()
    y[600:] = 0.1
    assert np.allclose(h.filter(x)[:600], h.filter(y)[:600])
    assert np.allclose(h.filter(x)[-1], h.smooth(x)[-1])
    assert not np.allclose(h.smooth(x)[:600], h.smooth(y)[:600])


def test_viterbi_matches_brute_force():
    x, _ = regime_series(8, (0.0, 0.0), (0.01, 0.03), [[0.9, 0.1], [0.2, 0.8]], seed=3)
    h = GaussianHMM(2)
    h.mu, h.sd, h.P, h.pi = np.zeros(2), np.array([0.01, 0.03]), np.array([[0.9, 0.1], [0.2, 0.8]]), np.array([0.5, 0.5])
    lB = np.log(h._dens(x))

    def lp(path):
        return np.log(h.pi[path[0]]) + lB[0, path[0]] + sum(np.log(h.P[a, b]) + lB[t + 1, b]
                                                            for t, (a, b) in enumerate(zip(path, path[1:], strict=False)))
    best = max(itertools.product((0, 1), repeat=8), key=lp)
    assert list(h.viterbi(x)) == list(best)


def test_isolation_forest_ranks_outliers_first():
    rng = np.random.default_rng(0)
    X = np.vstack([rng.standard_normal((500, 3)), rng.standard_normal((5, 3)) + 6])
    s = iforest_scores(X)
    assert set(np.argsort(-s)[:5]) == set(range(500, 505))
