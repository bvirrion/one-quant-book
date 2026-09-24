"""Tutorial of Book 6, chapter 27: the printed end state is reproduced."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_pnlexplain as m


def test_book_is_a_pure_delta_position_at_the_start():
    g = m.day()["greeks"]
    assert abs(m.value(m.START)) < 1e-6 and abs(g["gamma"]) < 1e-3 and abs(g["vega"]) < 1e-3
