import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_firmsize as fs  # noqa: E402

EDGES = [(11, 15), (16, 20), (21, 30), (31, 50), (51, 100), (101, 300), (301, 1000), (1001, None)]


def binned(x):
    return [fs.Bin(lo, hi, int(((x >= lo) & (x <= (hi if hi else 10**12))).sum())) for lo, hi in EDGES]


def test_recovers_alpha_on_simulated_sizes():
    x = fs.sample_pareto(20_000, 11, 1.2, np.random.default_rng(3))
    f = fs.pareto_fit(binned(x), 11)
    assert abs(f["alpha"] - 1.2) < 3 * f["se"] and f["se"] < 0.05


def test_probabilities_sum_to_one_and_ccdf():
    b = binned(fs.sample_pareto(5_000, 11, 1.0, np.random.default_rng(4)))
    e = fs.expected_counts(b, 11, {"alpha": 1.0})
    assert abs(sum(e) - sum(x.n for x in b)) < 1e-6
    c = fs.ccdf(b)
    assert c[0] == (11, 1.0) and all(c[i][1] >= c[i + 1][1] for i in range(len(c) - 1))


def test_lognormal_fit_runs_and_scores():
    b = binned(fs.sample_pareto(5_000, 11, 1.0, np.random.default_rng(5)))
    ln = fs.lognormal_fit(b, 11)
    assert ln["sigma"] > 0 and fs.chi2(b, fs.expected_counts(b, 11, ln)) >= 0
