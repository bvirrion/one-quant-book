"""Numbers gate: every numerical answer printed in Book 4, Chapter 12 (text and solutions)."""
import math
import pathlib
import sys
from math import comb

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from qm_testing import (
    family_exceedance,
    fdr_correlated,
    fdr_experiment,
    ks_example,
    max_survival,
    problem,
    sharpe_power,
    years_needed,
)

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "multitest"))
from firm_multitest import (
    benjamini_hochberg,
    bonferroni,
    expected_max_sr,
    holm,
    maxt_pvalues,
    norm_cdf,
    norm_ppf,
)

P = problem()


def r(x, d=2):
    return round(float(x), d)


def test_hook_and_section_1():
    assert r(1 - norm_cdf(3.1), 3) == 0.001 and r(max_survival(3.1, 200), 3) == 0.176
    k = ks_example()
    assert (r(k["d"], 4), r(k["p"], 4), r(k["crit95"], 4), r(k["lam95"], 3)) == (0.0615, 0.0010, 0.0429, 1.358)
    assert (r(years_needed(2.0), 1), r(years_needed(1.0), 1), r(years_needed(0.5), 1)) == (1.5, 6.2, 24.7)
    assert r(sharpe_power(1.0, 5), 2) == 0.72


def test_section_2():
    assert r(expected_max_sr(200, 1.0)) == 2.77                                   # the approximation
    rng = np.random.default_rng(0)
    assert r(rng.standard_normal((20_000, 200)).max(1).mean()) == 2.75          # the text's 2.75 is the exact mean
    assert r(math.sqrt(2 * math.log(200))) == 3.26
    assert (P["best_lookback"], r(P["t_best"]), r(P["sr_best"])) == (42, 3.11, 0.98)
    assert (r(P["corr_next"]), r(P["corr_first"]), r(P["corr_last"])) == (0.95, 0.28, 0.20)
    assert (P["n_naive_5"], r(P["mean_t"])) == (33, 1.04)


def test_section_3():
    p = np.array([0.005, 0.01, 0.03, 0.04, 0.2])
    assert np.allclose(bonferroni(p), [0.025, 0.05, 0.15, 0.2, 1])
    assert np.allclose(holm(p), [0.025, 0.04, 0.09, 0.09, 0.2])
    assert np.allclose(benjamini_hochberg(p), [0.025, 0.025, 0.05, 0.05, 0.2])
    assert ((bonferroni(p) <= 0.05).sum(), (holm(p) <= 0.05).sum(), (benjamini_hochberg(p) <= 0.05).sum()) == (2, 2, 4)
    f = fdr_experiment()
    assert (round(f["none"]["disc"]), round(f["none"]["false"]), round(f["none"]["true"])) == (136, 45, 91)
    assert (round(f["bonferroni"]["disc"]), round(f["holm"]["disc"]), round(f["bonferroni"]["true"])) == (18, 19, 18)
    assert r(f["holm"]["true"]) == 18.52 and r(f["bonferroni"]["false"]) == 0.05 and r(f["bonferroni"]["fwer"], 3) == 0.054
    assert (round(f["bh"]["disc"]), r(f["bh"]["false"], 1), r(100 * f["bh"]["fdp"], 1), round(f["bh"]["true"])) == (63, 2.9, 4.4, 61)
    assert r(f["bh"]["fwer"]) == 0.92
    assert (r(P["p_bonf"], 3), r(P["p_holm"], 3), r(P["p_bh"], 3)) == (0.187, 0.187, 0.076)
    assert r(P["p_naive"], 5) == 0.00094 and P["n_bh_5"] == 0 and P["n_bonf_5"] == 0


def test_section_4():
    assert (r(P["p_maxt"], 3), r(P["p_step"], 3), r(P["p_indep"], 3)) == (0.030, 0.030, 0.171)
    assert round(P["n_eff"]) == 32 and P["n_maxt_5"] == 3
    assert (r(P["crit_maxt"]), r(P["crit_bonf"])) == (2.92, 3.48)
    assert (r(P["psr"], 3), r(P["sr0_200"]), r(P["dsr_200"]), r(P["sr0_eff"]), r(P["dsr_eff"])) == (0.999, 0.87, 0.63, 0.67, 0.84)


def test_family_on_fresh_histories():
    """WRITING section 9: the simulated max-statistic p-value is checked against the true law of the family
    (fresh histories), and each credited mechanism is ablated: correlation (identity -> independent formula,
    all ones -> naive p) and normal tails (Student t4 returns change little)."""
    fe = family_exceedance(3.11)
    assert r(fe, 3) == 0.026
    assert abs(fe - P["p_maxt"]) < 3 * math.sqrt(0.03 * 0.97 / 2000)
    assert r(family_exceedance(3.11, df=4.0), 4) == 0.0235
    t = np.array([P["t_best"], 0.0])
    one = maxt_pvalues(t, np.ones((2, 2)), n_sim=400_000, seed=9)[0]
    assert abs(one - P["p_naive"]) < 2e-4


def test_sampling_stability():
    """Quadrupling the Gaussian draws (the analogue of dividing a time step by four) moves the p-value by less than
    its Monte Carlo error."""
    q = problem(n_sim=800_000)
    assert abs(q["p_maxt"] - P["p_maxt"]) < 3 * math.sqrt(0.03 * 0.97 / 200_000)


def test_exercises_and_interview():
    assert (r(1 - norm_cdf(2.5), 4), r(20 * (1 - norm_cdf(2.5)), 3)) == (0.0062, 0.124)
    assert r(norm_cdf(2 - 1.645), 3) == 0.639 and r(norm_cdf(0.355), 3) == 0.639
    p = np.array([0.001, 0.012, 0.02, 0.3])
    assert np.allclose(holm(p), [0.004, 0.036, 0.04, 0.3]) and np.allclose(bonferroni(p), [0.004, 0.048, 0.08, 1])
    assert (r(norm_ppf(0.9), 3), r(years_needed(0.7, power=0.9), 1)) == (1.282, 17.5)
    lr = 1000 * math.log(1.22) - 500 * math.log(1.44)
    assert r(lr) == 16.53 and r(math.erfc(math.sqrt(lr / 2)) * 1e5, 1) == 4.8
    assert (r(max_survival(2.0, 10), 3), r(expected_max_sr(10, 1.0))) == (0.206, 1.57)
    rng = np.random.default_rng(1)
    assert r(rng.standard_normal((100_000, 10)).max(1).mean()) == 1.54
    c = fdr_correlated()
    assert (r(100 * c["fdr"], 1), r(100 * c["p_fdp_over_10"], 1), round(c["disc"])) == (3.0, 7.8, 63)
    assert (r(12 * 0.05, 1), r(1 - sum(comb(12, k) * 0.05**k * 0.95 ** (12 - k) for k in range(3)), 3)) == (0.6, 0.02)
    assert r(max_survival(2.8, 100)) == 0.23
    assert r((1.645 + 0.842) ** 2, 1) == 6.2
    assert r(math.log(1 - 0.030) / math.log(1 - 0.00094), 0) == 32
