"""Numbers gate: every numerical answer printed in Book 5, Chapter 11 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from dv_sabr import (
    ALPHA,
    BETA,
    F0,
    NU,
    RHO,
    T,
    alpha_from_atm,
    equity_fit,
    hagan_lognormal,
    hedge_experiment,
    normal_vol,
    wing_density,
)
from firm_sabr import deltas, one_day_hedge_errors

H = hedge_experiment()
E = equity_fit()


def test_text():
    assert round(ALPHA, 4) == 0.0346
    assert (round(100 * hagan_lognormal(F0, 0.02, T, ALPHA, BETA, RHO, NU), 1), round(100 * hagan_lognormal(F0, 0.04, T, ALPHA, BETA, RHO, NU), 1)) == (28.8, 15.8)
    nv = [round(1e4 * normal_vol(F0, k, T, ALPHA, BETA, RHO, NU), 1) for k in (0.02, 0.03, 0.04)]
    assert nv == [70.8, 59.9, 55.0]
    assert (round(E["alpha"], 3), round(E["rho"], 2), round(E["nu"], 2), round(100 * E["rmse"], 2), round(100 * E["max_err"], 2)) == (0.194, -0.68, 0.72, 0.07, 0.15)
    assert abs(E["fitted"][0] - E["market"][0]) == max(abs(E["fitted"] - E["market"]))
    d = H["deltas"]
    assert (round(d["black"], 3), round(d["hagan"], 3), round(d["bartlett"], 3)) == (0.540, 0.580, 0.461)
    sd = H["sd"]
    assert (round(1e5 * sd["black"], 2), round(1e5 * sd["hagan"], 2), round(1e5 * sd["bartlett"], 2)) == (6.67, 7.46, 5.99)
    assert (round(100 * (1 - H["var_ratio"]["bartlett"])), round(100 * (H["var_ratio"]["hagan"] - 1))) == (19, 25)
    ks, dens = wing_density()
    neg = ks[dens < 0]
    assert round(100 * neg.max(), 1) == 1.6 and dens[ks > 0.017].min() > 0


def test_exercises():
    assert [round(100 * 0.2 * 0.03 ** (1 - b) * 0.025 ** (b - 1), 1) for b in (0, 0.5, 1)] == [24.0, 21.9, 20.0]
    a3 = alpha_from_atm(F0, T, 0.2, BETA, 0.3, 0.4)
    e = one_day_hedge_errors(F0, F0, T, a3, BETA, 0.3, 0.4)
    r = {k: (v / e["black"]) ** 2 for k, v in e.items()}
    assert round(r["bartlett"], 3) == 0.999 and round(100 * (r["hagan"] - 1)) == 10


def test_problem():
    assert round(100 * hagan_lognormal(0.035, 0.035, T, ALPHA, BETA, RHO, NU), 1) == 18.5
    assert round(RHO * NU / F0 ** BETA, 2) == -1.73
    assert (round(H["var_ratio"]["hagan"], 2), round(H["var_ratio"]["bartlett"], 2)) == (1.25, 0.81)
    a0 = alpha_from_atm(F0, T, 0.2, BETA, 0.0, NU)
    d0 = deltas(F0, F0, T, a0, BETA, 0.0, NU)
    e0 = one_day_hedge_errors(F0, F0, T, a0, BETA, 0.0, NU)
    assert abs(d0["hagan"] - d0["bartlett"]) < 1e-12 and round(100 * (1 - (e0["bartlett"] / e0["black"]) ** 2)) == 1
    assert round(100 * (1 - H["var_ratio"]["bartlett"] ** 0.5)) == 10
