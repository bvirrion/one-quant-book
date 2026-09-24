"""Numbers gate: every numerical answer printed in Book 4, Chapter 28 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import qm_transforms as q  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def test_fourier():
    c = {n: (eb, em) for n, eb, em in q.cos_convergence()}
    assert c[64][0] < 1e-14 and r(c[64][1] * 1e7, 1) == 1.2 and r(c[128][1] * 1e12, 1) == 2.1
    assert c[8][1] > 1 and c[16][1] > c[32][1] > c[64][1]
    v = q.vg_check()
    assert (r(v["cos"], 4), r(v["mc"], 3), r(v["se"], 3)) == (9.5243, 9.528, 0.022)
    g = q.gil_pelaez_digital()
    assert r(g["gil_pelaez"], 7) == 0.3503999 and abs(g["gil_pelaez"] - g["exact"]) < 5e-10


def test_interpolation_and_roots():
    fc = q.forward_curves()
    assert (r(100 * fc["spline"].min()), r(fc["t"][fc["spline"].argmin()], 0)) == (2.63, 30.0)
    assert (r(100 * fc["monotone"].min()), r(100 * fc["monotone"].max())) == (3.32, 5.67)
    assert r(100 * np.abs(np.diff(fc["linear"])).max()) == 0.43
    assert r(q.runge()) == 1.92
    iv = q.implied_vol_iterations()
    assert [iv[k]["secant"] for k in (50, 70, 100, 150, 250, 400)] == [10, 7, 4, 7, 18, None]
    assert [iv[k]["newton"] for k in (50, 70, 100, 150, 250, 400)] == [9, 6, 3, 6, 13, None]
    assert [iv[k]["brent"] for k in (50, 70, 100, 150, 250, 400)] == [17, 17, 5, 17, 17, 18]
    assert all(iv[k]["bisection"] == 36 for k in iv)
    assert f"{q.bs(100, 400, 0.03, 0.25, 1):.1e}" == "2.5e-07" and f"{q._vega(100, 400, 0.03, 0.2, 1):.0e}" == "8e-09"
    assert r(0.2 + (q.bs(100, 400, 0.03, 0.25, 1) - q.bs(100, 400, 0.03, 0.2, 1)) / q._vega(100, 400, 0.03, 0.2, 1), 1) == 30.6


def test_aad_book_and_checkpointing():
    g = q.gradients()
    assert (g["ops"], g["partials"], r(g["ratio_reverse"]), g["ratio_bump"], round(g["ratio_forward"])) == (2864, 3698, 3.58, 401, 1433)
    assert np.abs(g["rev"] - g["fwd"]).max() < 3e-13 and 5e-6 < np.abs(g["rev"] - g["bump"]).max() < 1e-5
    assert (round(np.abs(g["rev"]).max()), int((np.abs(g["rev"]) > 0).sum()), r(g["value"])) == (517, 213, 112.37)
    cc = q.cost_curve()
    assert all(r(row[3]) == 3.58 for row in cc) and [row[1] for row in cc] == [26, 51, 101, 201, 401]
    cp = q.checkpoint_demo()
    assert (cp["full_nodes"], cp["peak_states"]) == (60003, 201)
    assert abs(cp["full"][0] - cp["check"][0]) < 1e-14 and abs(cp["full"][1] - cp["check"][1]) < 1e-13


def test_exercises():
    assert (4096**2, 2048 * 12) == (16777216, 24576)
    assert r(3 * math.e, 3) == 8.155 and math.ceil(math.log2(5e10)) == 36
    assert (r(math.cos(2), 3), r(1 + 2 * math.cos(2), 3), r(math.cos(2), 3)) == (-0.416, 0.168, -0.416)


def test_cos_terms_and_truncation_ablation():
    """WRITING section 9: doubling the number of cosine terms cuts the error by orders of magnitude until the
    truncation floor, and shrinking the truncation range (the ablation, L = 3) leaves a visible floor."""
    ref = q.merton_exact(100, 100, 0.03, 1, **q.MERTON)

    def psi(u):
        return q.psi_merton(u, 0.0, 0.15, 0.5, -0.1, 0.2)
    e = [abs(q.cos_call(psi, 100, 100, 0.03, 1, n) - ref) for n in (32, 64)]
    assert e[1] < 1e-4 * e[0]
    narrow = abs(q.cos_call(psi, 100, 100, 0.03, 1, 256, L=3.0) - ref)
    assert narrow > 1e3 * abs(q.cos_call(psi, 100, 100, 0.03, 1, 256) - ref)
