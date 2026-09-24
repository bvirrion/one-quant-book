"""Numbers gate: every numerical answer printed in Book 6, chapter 15 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_portcredit as m

Q = m.quotes()
D = m.deltas()
M = m.may_2005()
T = {round(100 * x): (g, t) for x, g, t in m.tail_table()}


def test_text():
    assert round(100 * m.pd5(), 2) == 4.08 and round(m.default_corr(), 3) == 0.070
    assert round(m.expected_defaults(), 1) == 5.1
    lhp, fin = m.lhp_vs_finite()
    assert (round(100 * lhp, 1), round(100 * fin, 1)) == (51.6, 49.6)
    assert round(100 * Q[0][2], 2) == 37.21
    assert [round(1e4 * q[2], 1) for q in Q[1:]] == [195.0, 83.6, 43.6, 17.9, 3.6]
    assert round(1e4 * m.index_spread(), 1) == 49.6
    c = m.compound_table()
    assert [round(100 * x, 1) for x in c[0][2]] == [15.0]
    assert [round(100 * x, 1) for x in c[1][2]] == [2.1, 89.9]
    assert [round(100 * r[2][0], 1) for r in c[2:]] == [12.9, 18.4, 25.2, 50.0]
    top = max(m.mezz_curve(), key=lambda x: x[1])
    assert round(top[1]) == 374 and round(top[0], 2) == 0.29
    r = D["ratio"]
    assert [round(r[t], 2) for t in m.TRANCHES] == [17.25, 7.32, 3.28, 1.77, 0.72, 0.14]
    assert round(r[m.TRANCHES[0]], 1) == 17.3 and round(r[m.TRANCHES[0]] / r[m.TRANCHES[1]], 2) == 2.36
    assert round(100 * m.super_senior_loss_prob(), 2) == 1.88
    assert (round(100 * T[12][0], 2), round(100 * T[12][1], 2)) == (2.24, 5.23)
    assert (round(100 * T[24][0], 2), round(100 * T[24][1], 2)) == (0.13, 1.13)
    assert round(T[24][1] / T[24][0], 1) == 8.6


def test_exercises():
    assert round(125 * m.pd5(), 2) == 5.10
    assert round(0.6 / 125 * 100, 2) == 0.48 and round(3 / 0.48, 2) == 6.25 and round(22 / 0.48, 1) == 45.8
    assert round(50 * D["ratio"][(0.06, 0.09)]) == 164
    from statistics import NormalDist
    assert round(-NormalDist().inv_cdf(m.pd5()), 2) == 1.74


def test_problem():
    assert round(M["hedge"] / 1e6, 2) == 23.56 and round(Q[0][2] * 10e6 / 1e6, 3) == 3.721
    assert round(Q[1][2] * M["hedge"]) == 459_502
    assert round((0.05 * 10e6 - Q[1][2] * M["hedge"]) / 1e3) == 40
    b, c, both = M["blowout"], M["corr"], M["both"]
    assert round(100 * b["eq_upfront"], 2) == 42.79 and round(1e4 * b["mezz_par"], 1) == 236.5
    assert (round(b["equity"]), round(b["mezz"]), round(b["total"])) == (-557_577, 424_041, -133_536)
    assert round(0.48 / 3 * 100) == 16
    assert (round(c["equity"]), round(c["mezz"]), round(c["total"])) == (-269_618, -594_873, -864_491)
    assert round(1e4 * c["mezz_par"]) == 138
    assert (round(both["equity"]), round(both["mezz"]), round(both["total"])) == (-828_391, -171_869, -1_000_261)
