"""Numbers gate: every numerical answer printed in the Chapter 19 text and solutions."""
import csv
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from alloc_demo import EXAMPLE, compare, fill_vs_size

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/match"))
from firm_match import Quote, Resting, best_of, fifo, implied_in, implied_out_front, pro_rata

FIG = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-1/19-matching-algorithms-and-implied-spreads"
FRONT, BACK, DIRECT = Quote(10050, 30, 10052, 25), Quote(10020, 40, 10023, 10), Quote(28, 5, 32, 7)


def test_text():
    r = compare(EXAMPLE, 100)
    assert r["fifo"] == {"A": 10, "B": 90} and r["pro_rata"] == {"A": 2, "B": 40, "C": 8, "D": 50}
    assert r["split"] == {"A": 10, "C": 13, "B": 51, "D": 26}
    assert 8 * 1000 / 92 == pytest.approx(86.96, abs=0.01)
    assert 100 * 87 // 1087 == 8 and 100 * 86 // 1086 == 7 and 1000 * 87 // 1087 == 80
    fills = dict(fill_vs_size(range(0, 30), 1000, 100))
    assert fills[20] == 0 and fills[21] == 2
    with open(FIG / "position.csv") as f:
        rows = [{k: float(v) for k, v in row.items()} for row in csv.DictReader(f)]
    assert round(rows[0]["fifo"] / rows[0]["pro_rata"], 1) == 4.1
    assert next(r["ahead"] for r in rows if r["fifo"] < r["pro_rata"]) == 170
    assert implied_in(FRONT, BACK) == Quote(27, 10, 32, 25)
    assert best_of(DIRECT, implied_in(FRONT, BACK)) == Quote(28, 5, 32, 32)


def test_exercises():
    assert fifo(EXAMPLE, 230) == {"A": 10, "B": 200, "C": 20}
    shares = [60 * q / 500 for q in (10, 200, 40, 250)]
    assert shares == pytest.approx([1.2, 24.0, 4.8, 30.0]) and sum(int(s) for s in shares) == 59
    assert pro_rata(EXAMPLE, 60) == {"A": 2, "B": 24, "C": 4, "D": 30}
    assert pro_rata([Resting("others", 2000), Resting("me", 5)], 100, 2) == {"others": 100}
    assert 100 * 5 / 2005 < 0.25 and 100 * 40 // 2040 == 1 and 100 * 41 // 2041 == 2
    with open(FIG / "position.csv") as f:
        first = next(csv.DictReader(f))
    assert (float(first["fifo"]), float(first["pro_rata"])) == (9.562, 2.344)


def test_problem():
    assert (5 * 28 + 7 * 27) / 12 == pytest.approx(27.4167, abs=1e-4)
    after_front, after_back = Quote(10050, 23, 10052, 25), Quote(10020, 40, 10023, 3)
    assert best_of(Quote(None, 0, 32, 7), implied_in(after_front, after_back)) == Quote(27, 3, 32, 32)
    assert (12 * 10050 - 10 * 10023 - 2 * 10024) / 12 == pytest.approx(26.8333, abs=1e-4)
    assert implied_out_front(DIRECT, BACK) == Quote(10048, 5, 10055, 7)
    assert implied_in(FRONT, Quote(10020, 40, 10021, 20)) == Quote(29, 20, 32, 25)
    assert 10050 - 32 == 10018 < 10021                          # implied-out back bid does not reach the new offer
