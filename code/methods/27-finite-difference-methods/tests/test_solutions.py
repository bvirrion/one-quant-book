"""Numbers gate: every numerical answer printed in Book 4, Chapter 27 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import qm_fd as q  # noqa: E402
from firm_pde import amplification, interp, solve_1d, uniform_grid  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def test_explicit_and_amplification():
    e = q.explicit_blowup()
    assert (e[0.49]["steps"], r(e[0.49]["lam"], 3), r(e[0.49]["price"], 4)) == (409, 0.489, 4.3576)
    assert (e[0.51]["steps"], r(e[0.51]["lam"], 3), round(e[0.51]["max"])) == (393, 0.509, 2413)
    assert r(q.bs(q.K), 4) == 4.3576 and r(q.lam(400, 25)) == 32.0
    assert r(amplification(0.0, 0.51, math.pi)) == -1.04 and r(amplification(0.5, 32.0, math.pi), 3) == -0.969
    assert r(amplification(1.0, 16.0, math.pi) * 65, 6) == 1.0


def test_sawtooth_and_convergence():
    s = q.sawtooth()
    assert (r(s[0]["err"]), r(s[0]["price_err"], 3), r(s[0]["gamma"].min()), r(s[0]["gamma"].max())) == (0.84, 0.018, -0.81, 0.55)
    assert r(q.bs_gamma(100.0), 3) == 0.04 and r(s[2]["err"] * 1e4, 1) == 4.7
    c = q.convergence()
    assert [r(v[2]) for v in c["cn"]] == [0.46, 0.84, 1.69, 3.38]
    g4 = [v[2] for v in c["cn+4"]]
    assert [r(g4[1] * 1e5), r(g4[2] * 1e6), r(g4[3] * 1e6)] == [1.76, 4.35, 1.07]
    assert (r(g4[1] / g4[2]), r(g4[2] / g4[3])) == (4.05, 4.07)
    g2 = [v[2] for v in c["cn+2"]]
    assert all(1.9 < a / b < 2.1 for a, b in zip(g2, g2[1:], strict=False))
    assert [r(v[1], 4) for v in c["cn"]] == [0.0407, 0.0181, 0.0092, 0.0046]
    assert all(3.8 < a[1] / b[1] < 4.3 for a, b in zip(c["cn+4"], c["cn+4"][1:], strict=False))
    assert all(0.09 < v[3] < 0.13 for v in c["cn"])


def test_digital_grids_extrapolation_upwind_adi():
    d = q.digital_placement()
    assert [f"{v[1]:.2g}" for v in d] == ["0.0099", "0.0049", "0.0025", "0.0012"]
    assert [f"{v[2]:.2g}" for v in d] == ["6.6e-06", "1.5e-06", "3.8e-07", "9.5e-08"]
    assert (r(d[0][2] / d[1][2], 1), r(d[1][2] / d[2][2], 1), r(d[2][2] / d[3][2], 1)) == (4.4, 4.0, 4.0)
    st = q.stretched()
    assert (r(st[0][1], 4), r(st[0][2], 4), r(st[-1][1] * 1e4, 2), r(st[-1][2] * 1e4, 1)) == (0.0225, 0.0079, 3.45, 1.2)
    assert all(2.8 < a / b < 3.0 for _, a, b in st)
    rd = q.richardson_demo()
    assert (r(rd["coarse"] * 1e3, 1), r(rd["fine"] * 1e4, 1), r(rd["extrapolated"] * 1e7, 1)) == (1.8, 4.6, 3.2)
    u = q.upwind_demo()
    assert (r(u["peclet"]), r(u["central"]["max"], 3), r(u["central"]["tv"]), r(u["bound"], 3)) == (2.49, 1.03, 1.23, 0.951)
    assert r(u["upwind"]["max"], 3) == 0.951 and abs(u["upwind"]["tv"] - u["upwind"]["max"]) < 1e-9
    assert r(q.boundary_compare() * 1e8) == 6.11
    a = [q.adi_exchange(n, n // 2) for n in (40, 80, 160)]
    assert r(a[0]["exact"], 4) == 10.5243 and [r(v["err"], 3) for v in a] == [0.045, 0.026, 0.014]


def test_exercises():
    assert r(0.0025**2 / 0.04 * 1e4, 4) == 1.5625 and round(1 / (0.0025**2 / 0.04)) == 6400
    assert r(4.3572 + (4.3572 - 4.3558) / 3, 5) == 4.35767
    assert round(math.log(100) / -math.log(63 / 65)) == 147 and math.ceil(math.log(100) / -math.log(63 / 65)) == 148


def test_time_step_refinement_at_fixed_space():
    """WRITING section 9: at fixed space grid, halving the time step with four half steps changes the price by less
    than the space error, and the explicit ablation (theta = 0) at the chapter's time step explodes."""
    x = uniform_grid(q.LO, q.HI, 400)
    v = [interp(x, solve_1d(x, q.call, q.A, q.B, q.C, q.T, m, theta=0.5, rannacher=4), math.log(q.K)) for m in (25, 50)]
    assert abs(v[0] - v[1]) < abs(v[1] - q.bs(q.K))
    with np.errstate(over="ignore", invalid="ignore"):
        u = solve_1d(x, q.call, q.A, q.B, q.C, q.T, 25, theta=0.0)
    assert not np.isfinite(u).all() or np.abs(u).max() > 1e10
