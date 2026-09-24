"""Tutorial of Book 6, chapter 3: the printed end state is reproduced."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_ratesrisk as m


def test_book_is_parallel_neutral_but_loses_on_the_twist():
    book, _ = m.balanced_book()
    assert abs(m.hedge(book)["ladder"].sum()) < 1e-3
    assert m.full_revaluation(book, m.MOVE_2022_10_21) < -3.0e6


def test_the_best_trio_beats_the_textbook_trio():
    book, _ = m.balanced_book()
    assert m.hedge(book)["residual_share"] < 0.05 < 0.5 < m.hedge(book, (1, 5, 7))["residual_share"]
