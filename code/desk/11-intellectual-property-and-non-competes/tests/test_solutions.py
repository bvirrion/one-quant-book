"""Numbers gate: every numerical answer printed in Book 16, chapter 11 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import fm_ip as m  # noqa: E402

gl = m.gl


def r(x, d=2):
    return round(float(x), d)


def test_hand_example():
    lam = math.log(2)
    assert (r(gl.protected(10, 0.5, lam, 0, 0.5)), r(gl.protected(10, 0.5, lam, 0, 1.0))) == (2.11, 3.61)
    assert r(gl.loss_if_start(10, 0.5, lam, 0, 0)) == 7.21 and gl.leave_cost(1, 0, 1.0) == 1.0
    t = gl.best_length(10, 0.5, lam, 1)
    assert r(t) == 2.32 and r(gl.net(10, 0.5, lam, 0, 1, t)) == 3.45 and r((5 - 1 - math.log(5)) / lam) == 3.45
    assert r(gl.net(10, 0.5, lam, 0, 1, 1.0)) == 2.61


def test_named_result():
    for ratio, hl in ((8, 2.0), (4, 3.0), (4 / 1.5, 4.24)):
        assert r(6 / math.log2(ratio)) == hl
    assert [r(gl.leave_cost(m.S, m.R, t)) for t in m.LENGTHS] == [0.37, 0.74, 1.44]


def test_table():
    t, e = m.table(), m.estimates()
    assert [r(e[k]["hl_est"], 1) for k in m.CASES] == [24.9, 5.7, 12.1]
    assert [r(t[k]["best_years"]) for k in m.CASES] == [4.14, 1.42, 1.43]
    assert [r(t[k]["best_years"] * 12 / e[k]["hl_est"]) for k in m.CASES] == [2.0, 3.0, 1.42]
    assert [[r(t[k]["protected"][x]) for x in m.LENGTHS] for k in m.CASES] == [
        [1.42, 2.71, 4.91], [2.49, 4.18, 6.12], [0.91, 1.66, 2.79]]
    assert [[r(t[k]["net"][x]) for x in m.LENGTHS] for k in m.CASES] == [
        [1.05, 1.97, 3.47], [2.12, 3.45, 4.67], [0.54, 0.93, 1.35]]
    assert [r(t[k]["loss_no_leave"]) for k in m.CASES] == [14.47, 7.78, 5.22]
    assert [r(100 * t[k]["protected"][0.5] / t[k]["loss_no_leave"], 0) for k in m.CASES] == [19, 54, 32]
    at_best = [gl.net(m.P, e[k]["L"], e[k]["lam"], m.R, m.S, t[k]["best_years"]) for k in m.CASES]
    assert [r(x) for x in at_best] == [6.58, 4.90, 1.45]
    s = e["structure"]
    two = gl.protected(m.P, s["L"], s["lam"], m.R, 2.0) / gl.loss_if_start(m.P, s["L"], s["lam"], m.R, 0.0)
    assert r(100 * two, 0) == 56 and r(gl.net(m.P, s["L"], s["lam"], m.R, m.S, 2.0)) == 5.38


def test_other_seed():
    t = m.table(seed=12)
    assert [r(t[k]["best_years"]) for k in m.CASES] == [3.99, 1.65, 1.38]
    assert [r(t[k]["hl_est"], 1) for k in m.CASES] == [23.9, 6.6, 11.7]


def test_small_runs():
    t, prot, cost = m.curves(tmax=1.0)
    assert len(t) == 9 and all(abs(prot[k][-1] - m.table()[k]["protected"][1.0]) < 1e-9 for k in m.CASES)
    assert cost[0] == 0.0 and all(b > a for a, b in zip(cost[:-1], cost[1:], strict=True))
