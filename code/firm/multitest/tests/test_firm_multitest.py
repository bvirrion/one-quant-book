"""Acceptance tests of firm.multitest."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_multitest import (
    benjamini_hochberg,
    benjamini_yekutieli,
    bonferroni,
    deflated_sharpe,
    effective_trials,
    expected_max_sr,
    holm,
    maxt_pvalues,
    norm_cdf,
    norm_ppf,
)


def test_normal_functions():
    assert abs(norm_ppf(0.975) - 1.959963984540054) < 1e-9
    assert abs(float(norm_cdf(1.959963984540054)) - 0.975) < 1e-12
    assert abs(norm_ppf(1 - 0.05 / 200) - 3.4807564) < 1e-6


def test_textbook_example():
    # Worked example with hand-checked adjusted p-values (m = 5).
    p = np.array([0.01, 0.04, 0.03, 0.005, 0.2])
    assert np.allclose(bonferroni(p), [0.05, 0.2, 0.15, 0.025, 1.0])
    assert np.allclose(holm(p), [0.04, 0.09, 0.09, 0.025, 0.2])
    assert np.allclose(benjamini_hochberg(p), [0.025, 0.05, 0.05, 0.025, 0.2])
    c = 1 + 1 / 2 + 1 / 3 + 1 / 4 + 1 / 5
    assert np.allclose(benjamini_yekutieli(p), np.minimum(1, benjamini_hochberg(p) * c))


def test_fwer_and_fdr_control_by_simulation():
    rng = np.random.default_rng(1)
    fw_b = fw_h = 0
    fdp = []
    for _ in range(2000):
        z = rng.standard_normal(50)
        z[:10] += 3.0
        p = 1 - norm_cdf(z)
        fw_b += np.any(bonferroni(p)[10:] <= 0.05)
        fw_h += np.any(holm(p)[10:] <= 0.05)
        rej = benjamini_hochberg(p) <= 0.1
        fdp.append(rej[10:].sum() / max(1, rej.sum()))
    assert fw_b / 2000 <= 0.05 + 0.012 and fw_h / 2000 <= 0.05 + 0.012 and fw_h >= fw_b
    assert abs(np.mean(fdp) - 0.1 * 40 / 50) < 0.01          # BH: FDR = q m0 / m under independence


def test_maxt_limits():
    t = np.array([3.1, 1.0, 0.0])
    ind = maxt_pvalues(t, np.eye(3), n_sim=400_000, seed=2)
    assert abs(ind[0] - (1 - float(norm_cdf(3.1)) ** 3)) < 3e-4
    one = maxt_pvalues(t, np.ones((3, 3)), n_sim=400_000, seed=3)        # perfectly correlated: no penalty
    assert abs(one[0] - (1 - float(norm_cdf(3.1)))) < 2e-4
    step = maxt_pvalues(t, np.eye(3), n_sim=400_000, seed=2, stepdown=True)
    assert np.all(step <= ind + 1e-12) and abs(step[0] - ind[0]) < 1e-12


def test_null_draws_hook():
    rng = np.random.default_rng(4)
    draws = rng.standard_normal((100_000, 4))
    p = maxt_pvalues(np.array([2.5, 0, 0, 0]), null_draws=draws)
    assert abs(p[0] - (1 - float(norm_cdf(2.5)) ** 4)) < 2e-3


def test_effective_trials_and_deflation():
    p1 = 0.001
    assert abs(effective_trials(p1, 1 - (1 - p1) ** 37) - 37) < 1e-9
    rng = np.random.default_rng(5)
    mx = rng.standard_normal((20_000, 100)).max(1).mean()
    assert abs(expected_max_sr(100, 1.0) / mx - 1) < 0.015            # the approximation is within about 1%
    assert abs(deflated_sharpe(0.0, 1000) - 0.5) < 1e-12
    sr = 0.05
    assert abs(deflated_sharpe(sr, 1001) - float(norm_cdf(sr * math.sqrt(1000) / math.sqrt(1 + 0.5 * sr**2)))) < 1e-12
