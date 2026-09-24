"""Tutorial of Book 6, chapter 7: the printed end state is reproduced."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_shortrate as m


def test_piecewise_fit_is_exact_and_constant_is_flat():
    rows = m.fit_table()
    assert max(abs(r[3] - r[1]) for r in rows) < 0.01
    assert max(r[2] for r in rows) - min(r[2] for r in rows) < 1.0


def test_tree_reprices_the_ten_year_bond():
    t = m.tree_check()
    assert abs(t["bond10_tree"] - t["bond10_curve"]) < 1e-12
