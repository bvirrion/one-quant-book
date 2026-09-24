"""Numbers gate: every numerical answer printed in Book 6, chapter 26 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_modelval as m
from firm_modelval import ModelRecord, relative_change

V = m.validation()
A = m.averaging_error()


def test_text():
    assert V["summary"]["points"] == 216
    q, mo = V["by_dt"][0.25], V["by_dt"][1 / 12]
    assert (q["points"], q["failures"], round(1e4 * q["max_abs"], 1)) == (108, 54, 15.8)
    assert (mo["failures"], round(1e4 * mo["max_abs"], 1)) == (23, 3.2)
    rows = {r[0]: r for r in m.errors_by_expiry()}
    assert rows[1][4] == 14
    p = {"kappa": 0.01, "sigma": 0.006, "expiry": 1, "tenor": 5, "moneyness": 0.0}
    assert round(1e4 * m.closed_price(**p, dt=1 / 12), 2) == 104.81
    assert round(1e4 * m.tree_price(**p, dt=1 / 12), 2) == 103.07 and round(1e4 * m.tree_price(**p, dt=0.25), 2) == 98.55
    assert m.tiers() == {1: 5, 2: 2, 3: 1}
    t = {r.model_id: r.tier for r in m.inventory()}
    assert [k for k, v in t.items() if v == 1] == ["B6-05", "B6-12", "B6-17", "B6-21", "B6-24"]
    assert round(A["hedge"], 1) == 12.0
    assert (round(A["intended"]["var"] / 1e6, 2), round(A["error"]["var"] / 1e6, 2)) == (14.06, 7.01)
    assert round(100 * A["ratio"], 1) == 49.9 and round(A["ratio"], 3) == 0.499


def test_exercises():
    assert (round(100 * relative_change(1.10, 1.00), 2), round(100 * relative_change(1.10, 1.00, True), 2)) == (9.52, 4.76)
    assert ModelRecord("x", "x", "o", "u", 3, 1, 1).tier == 2
    assert round(100 * m.exceptions_pvalue(250, 8), 2) == 0.40
    s = m.one_year_fine()
    assert (s["points"], s["failures"], round(1e4 * s["max_abs"], 2), round(100 * s["max_rel"])) == (36, 3, 1.40, 15)


def test_problem():
    assert round(1 - A["ratio"], 2) == 0.50
