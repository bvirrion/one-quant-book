"""Tutorial of Book 6, chapter 9: the printed end state is reproduced."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_bermudan as m


def test_tree_europeans_match_jamshidian_and_regression_matches_tree():
    b = m.bermudan_summary()
    assert max(abs(a - c) for a, c in zip(b["euro_tree"], b["euro_exact"], strict=True)) < 1.5e-4
    price, se = m.lsm_check()
    assert abs(price - b["bermudan"]) < 3 * se
