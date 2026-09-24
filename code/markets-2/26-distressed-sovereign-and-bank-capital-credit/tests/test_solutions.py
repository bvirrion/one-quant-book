"""Numbers gate: every numerical answer printed in Book 2, Chapter 26 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/recovery"))
from firm_recovery import Holdout, bond_pv, breakeven_participation
from restructuring_demo import HOLDOUT, OFFER, capital, tutorial

T = tutorial()


def test_text():
    assert round(T["new_bonds"], 2) == 29.85 and round(T["tender"], 2) == 34.85
    assert T["face_haircut"] == 0.5 and round(100 * T["npv_haircut"], 1) == 65.2
    assert (round(T["value_6"], 2), round(T["value_12"], 2)) == (45.29, 27.76)
    assert (round(T["paid_soon"], 2), round(T["lawsuit_pv"], 2)) == (91.74, 77.51)
    assert [round(T[k], 2) for k in ("h0", "h60", "h74", "h90")] == [33.75, 34.73, 38.97, 58.72]
    assert round(100 * T["p_star"], 1) == 60.9
    assert round(100 * T["greek_face_haircut"]) == 51
    c = capital()
    assert c["eu"] == {"CET1": 25.0, "AT1": 16.0, "Tier 2": 12.0, "senior bail-in": 80.0}
    assert c["at1_first"]["AT1"] == 0.0 and c["at1_first"]["CET1"] == 45.0
    assert round(0.3 * 77.51 + 0.7 * 15, 2) == 33.75


def test_exercises():
    v = bond_pv(60, 0.05, 10, 0.08)
    assert round(v, 2) == 47.92 and round(100 * (1 - v / 100), 1) == 52.1
    assert round(100 * (2 / 3), 1) == 66.7 and round(100 * T["p_star_two_thirds_band"], 1) == 5.8
    assert round(100 * (0.75 - 2 / 3), 1) == 8.3
    strong = Holdout(HOLDOUT.paid_soon, 0.5, HOLDOUT.lawsuit_pv, HOLDOUT.stuck)
    assert round(strong.value(0.0), 2) == 46.26 and breakeven_participation(strong, T["tender"]) < 1e-9


def test_problem():
    assert round(OFFER.value(0.09) * 1e6 / 1e6, 2) == 34.85 and OFFER.cash == 5.0
