"""Numbers gate: every numerical answer printed in Book 11, chapter 22 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import hf_rfq as h  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def test_equilibria():
    e = h.equilibria()
    assert [e[n]["markup"] for n in h.DEALERS] == [47.5, 40.0, 40.0, 42.5, 45.0, 50.0]
    assert [r(e[n]["pnl"]) for n in h.DEALERS] == [7.96, 3.46, 1.96, 0.94, 0.41, 0.45]
    assert [r(100 * e[n]["win"], 1) for n in h.DEALERS] == [27.7, 24.0, 19.1, 13.2, 9.1, 6.9]
    assert [r(e[n]["curse"], 1) for n in h.DEALERS] == [18.8, 25.6, 29.7, 35.4, 40.5, 43.5]
    assert [e[n]["naive"] for n in h.DEALERS] == [37.5, 30.0, 27.5, 25.0, 22.5, 25.0]
    assert [r(e[n]["naive_pnl"]) for n in h.DEALERS] == [7.50, 2.99, 1.25, -0.07, -1.13, -0.65]
    assert r(100 * e[5]["naive_win"]) == 30.48


def test_models():
    c = h.curse_theory()
    assert (r(c[5], 1), r(c[10], 1), r(c[2], 1)) == (29.1, 38.5, 14.1)
    w = h.win_model()
    assert (r(w["a"], 3), r(w["b"], 4), r(100 * w["fitted_at_eq"], 1), r(100 * w["simulated_at_eq"], 1)) == (0.665, -0.0612, 12.6, 13.2)
    assert r(100 / (1 + math.exp(-(0.665 - 0.0612 * 20))), 1) == 36.4
    assert r(h.etf_example(), 3) == 99.915
    b = h.better_model()
    assert (b["markup"], r(b["pnl"]), r(100 * b["win"], 1)) == (25.0, 2.48, 23.4)
    assert r(25 / math.sqrt(math.pi) / 25, 3) == 0.564
