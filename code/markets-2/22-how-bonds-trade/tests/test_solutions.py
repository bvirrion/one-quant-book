"""Numbers gate: every numerical answer printed in Book 2, Chapter 22 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/rfq"))
from firm_rfq import composite, expected_cost, expected_max_normal
from rfq_demo import composite_example, problem

P = problem()
Q = [(99.42, 10), (99.45, 40), (99.40, 90), (99.47, 5), (98.20, 20)]


def test_text():
    assert [round(expected_max_normal(n), 3) for n in (2, 3, 4)] == [0.564, 0.846, 1.029]
    assert [round(expected_cost(n, 10, 5, 1.0), 2) for n in (1, 2, 3, 4, 6)] == [10.0, 8.18, 7.77, 7.85, 8.66]
    assert round(P["usd_star"], -2) == 19_400 and round(P["usd_1"]) == 25_000
    assert (P["n_star_low"], P["n_star"], P["n_star_high"]) == (6, 3, 2)
    assert round(composite_example(), 3) == 99.441
    assert round(5.2, 1) == 5.2


def test_exercises():
    assert [round(expected_cost(n, 10, 5, 0.0), 2) for n in (1, 2, 4)] == [10.0, 7.18, 4.85]
    assert round(composite(Q, half_life=10), 3) == 99.449


def test_problem():
    assert round(P["cost_star"], 2) == 7.77 and round(P["saving_vs_6"], -2) == 2_200
