"""Numbers gate: every numerical answer printed in Book 2, Chapter 25 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from clo_demo import base_case, deal, paths, problem
from firm_waterfall import run

B = base_case()
P = problem()


def test_text():
    assert (round(1549 / 1000, 2), 264, 617) == (1.55, 264, 617)
    assert round(B["interest"], 2) == 37.5 and B["fee"] == 2.25 and round(B["note_interest"], 2) == 26.14
    assert round(B["equity_year"], 2) == 9.11 and round(100 * B["cash_yield"], 1) == 18.2
    assert round(100 * B["irr"], 1) == 19.5
    assert [round(B["oc"][k], 3) for k in (1, 2, 3, 4)] == [1.370, 1.266, 1.176, 1.111]
    assert round(B["cushion_bb"], 1) == 27.5 and round(27.5 / 0.3, 1) == 91.7 and round(100 * 27.5 / 0.3 / 500, 1) == 18.3
    assert round(100 * (1 - 310 / 500)) == 38
    assert [round(100 * P["irr"][k], 1) for k in (0.02, 0.04)] == [13.1, 5.0] and P["irr"][0.06] < 0
    ps = paths()
    assert next(p[0] for p in ps[0.07] if p[3] < 1e-9) == 12
    assert next(p[0] for p in ps[0.048] if p[3] < 0.01) == 17
    assert all(p[3] > 0.5 for p in ps[0.02][:-1])


def test_exercises():
    assert round(500 - 1.18 * 395, 1) == 33.9 and round((500 - 1.18 * 395) / 0.3) == 113
    assert round(100 * (500 - 1.18 * 395) / 0.3 / 500, 1) == 22.6
    assert round(100 * 26.14 / 450, 2) == 5.81
    assert round(100 * P["no_reinvest_cutoff"], 2) == 5.35 and round(100 * P["cutoff"], 2) == 4.78


def test_problem():
    assert round(100 * P["irr"][0.06], 1) == -5.8
    assert [round(P["diverted"][k], 1) for k in (0.04, 0.06, 0.1)] == [2.0, 12.5, 28.4]
    assert P["first_cut_quarter"] == 19 and round(P["par_loss_at_cut"], 1) == 33.6
    assert round(P["bb_left_10"], 1) == 6.5
    assert next(p.quarter for p in run(deal(), 0.10) if p.equity < 1e-9) == 8
