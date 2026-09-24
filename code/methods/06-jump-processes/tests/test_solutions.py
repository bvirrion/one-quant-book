"""Numbers gate: every numerical answer printed in Book 4, Chapter 6 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/levy"))
from firm_levy import cumulants, merton_cumulants, psi_merton, psi_vg, simulate_merton
from qm_jumps import LAM, SIG_J, YEAR, calibrate, charfn_check, day_tail, kurtosis_term, problem

P = problem()
K = {h: (th, sim) for h, th, sim in kurtosis_term(P["mu_j"], P["sig_c"])}


def test_text():
    assert round(P["log10_p_normal"]) == -97
    assert round(P["kurt_day"]) == 76 and round(P["kurt_month"], 1) == 3.6
    assert round(math.log10(P["tail_per_day"]) - P["log10_p_normal_20"]) == 88
    for _u, re_e, re_t, im_e, im_t in charfn_check(P["mu_j"], P["sig_c"]):
        assert abs(re_e - re_t) < 0.01 and abs(im_e - im_t) < 0.01


def test_exercises():
    assert round(100 * math.exp(-5 / 12), 1) == 65.9
    assert (round(100 * -0.06), round(100 * math.sqrt(3 * (0.02**2 + 0.04**2)), 2)) == (-6, 7.75)
    c = cumulants(lambda u: 2 * (50 / (50 - 1j * u) - 1))
    assert abs(c[0] - 0.04) < 1e-6 and abs(c[1] - 0.0016) < 1e-6
    assert (round(76.4 / 5, 1), round(76.4 / 252, 2)) == (15.3, 0.30)
    th, s, nu = -0.1, 0.2, 0.3
    exact = [th, s**2 + nu * th**2, 2 * th**3 * nu**2 + 3 * s**2 * th * nu,
             3 * s**4 * nu + 6 * th**4 * nu**3 + 12 * s**2 * th**2 * nu**2]
    num = cumulants(lambda u: psi_vg(u, th, s, nu))
    assert all(abs(a - b) < 1e-6 for a, b in zip(num, exact, strict=True))
    assert [round(x, 6) for x in exact] == [-0.1, 0.043, -0.00378, 0.001888]
    assert round(1.2 * 21) == 25


def test_problem():
    assert round(100 * P["drop_1987"], 1) == 20.6 and round(P["log10_p_normal_20"], 1) == -92.2
    assert round(100 * P["annual_vol"], 1) == 15.6
    assert round(100 * P["mu_j"], 1) == -11.1 and round(100 * P["sig_c"], 2) == 12.96
    assert round(P["years_between"]) == 50 and round(100 * P["jump_var_share"]) == 31
    assert round(100 * P["p_jump_day"], 2) == 0.20
    assert round(100 * P["p_10pct_jd"], 3) == 0.116 and round(1 / (P["p_10pct_jd"] * YEAR), 1) == 3.4
    assert (round(P["skew_day"], 2), round(P["kurt_day"], 1)) == (-4.64, 76.4)
    assert round(P["kurt_month"], 2) == 3.64 and round(-100 * P["drift_correction"], 1) == 5.2
    assert (round(K[5][0], 1), round(K[5][1], 1)) == (15.3, 15.6)


def test_interview():
    assert round(100 * (1 - 3 * math.exp(-2)), 1) == 59.4


def test_time_step_and_ablation():
    """WRITING section 9. The calibration's tail probability is computed exactly (a Poisson mixture),
    so check it against simulation of the daily return split into four sub-steps (a Levy process is
    exact under any partition); and ablate the mechanism: without jumps (lambda = 0) the same
    variance gives a 20% fall a probability below 1e-90."""
    c = calibrate()
    x = simulate_merton(1 / YEAR, 4, 3_000_000, seed=77, mu=0.0, sigma=c["sig_c"], lam=LAM, mu_j=c["mu_j"],
                        sigma_j=SIG_J)[:, -1]
    freq = np.mean(x <= -0.20)
    assert abs(freq - c["tail"]) < 4 * math.sqrt(c["tail"] / 3_000_000)
    assert math.log10(max(day_tail(0.20, c["mu_j"], 0.0098 * math.sqrt(YEAR), lam=0.0), 1e-300)) < -90
    k = merton_cumulants(0.0, c["sig_c"], LAM, c["mu_j"], SIG_J)
    num = cumulants(lambda u: psi_merton(u, 0.0, c["sig_c"], LAM, c["mu_j"], SIG_J))
    assert all(abs(a - b) < 1e-7 for a, b in zip(num, k, strict=True))
