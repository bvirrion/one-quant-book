"""Numbers gate for Book 18, chapter 28: the loss-question arithmetic (the chapter's other answers are qualitative)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from iv_behave import days_between


def test_q5_three_sigma_day():
    assert round(2.4 / 0.8, 1) == 3.0
    d_norm = days_between(3)
    assert round(d_norm) == 741 and round(d_norm / 252, 1) == 2.9
    d_t = days_between(3, "t", 3)
    assert round(d_t) == 144 and round(d_t / 21, 1) == 6.9  # about every seven months of 21 trading days


def test_figure_tails():
    import csv

    import fig_iv_tails

    fig_iv_tails.main()
    rows = {r["k"]: r for r in csv.DictReader(open(fig_iv_tails.OUT / "tails.csv"))}
    assert round(float(rows["3.0"]["normal"])) == 741 and round(float(rows["3.0"]["t3"])) == 144
    assert float(rows["5.0"]["normal"]) / float(rows["5.0"]["t3"]) > 1000
