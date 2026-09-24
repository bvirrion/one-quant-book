"""Numbers gate: every numerical answer printed in Book 2, Chapter 10 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from ccp_demo import MODEL, basis_table, one_way_book

S = one_way_book(notional=1e8)
P = one_way_book()


def test_text():
    assert round(MODEL.im_per_dv01(), 1) == 36.4
    assert round(S["im"] / 1e6, 2) == 2.95 and round(S["mva"]) == 76_442
    assert round(S["basis_one"], 2) == 0.94
    assert round(dict((r[0], r[2]) for r in basis_table())[30], 2) == 2.30
    assert round(726_545 / 1e3) == 727 and round(1.3 + 2.1, 1) == 3.4


def test_exercises():
    assert round(S["dv01"]) == 81_109 and round(3 * S["dv01"]) == 243_327
    assert [round(x, 2) for x in basis_table()[-1][1:]] == [1.15, 2.30, 3.45]
    assert round(one_way_book(notional=1e8, maturity=30)["basis_two"], 2) == 4.60
    assert 9 > 8 and 70 - 50 == 20


def test_problem():
    assert round(P["dv01"] / 1e6, 2) == 1.62 and round(P["dv01"] / 2e9 * 1e4, 3) == 8.111
    assert round(P["im"] / 1e6, 1) == 59.1 and round(P["vm_5bp"] / 1e6, 2) == 8.11
    assert round(P["mva"] / 1e6, 2) == 1.53 and round(P["mva_two"] / 1e6, 2) == 3.06
    assert (round(P["basis_one"], 2), round(P["basis_two"], 2)) == (0.94, 1.88)
    assert round(P["basis_two_30y"], 2) == 4.60
    assert round(P["im_10day"] / 1e6, 1) == 83.5
