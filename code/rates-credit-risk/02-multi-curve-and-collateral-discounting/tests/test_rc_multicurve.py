"""Tutorial of Book 6, chapter 2: the printed end state is reproduced."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_multicurve as m


def test_basis_table_matches_the_quotes():
    assert [round(b) for _, b in m.basis_table()] == [20, 19, 18, 17, 16, 15, 14, 13, 12]


def test_forward_basis_is_positive_and_decays():
    rows = m.forward_table(1.0)
    assert all(b > 5 for *_, b in rows) and rows[0][3] > rows[-1][3]


def test_switch_gains_grow_with_maturity_for_an_in_the_money_receiver():
    ch = [c for _, _, c in m.switch_table()]
    assert all(b > a > 0 for a, b in zip(ch, ch[1:], strict=False))
