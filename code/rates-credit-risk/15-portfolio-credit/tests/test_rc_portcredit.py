"""Tutorial of Book 6, chapter 15: the printed end state is reproduced."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_portcredit as m


def test_equity_compound_equals_its_base_correlation():
    assert abs(m.compound_table()[0][2][0] - m.BASE_RHO[0.03]) < 1e-6


def test_deltas_fall_up_the_structure():
    r = [m.deltas()["ratio"][t] for t in m.TRANCHES]
    assert all(b < a for a, b in zip(r, r[1:], strict=False))
