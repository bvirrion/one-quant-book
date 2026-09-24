"""Numbers gate: every numerical answer printed in Book 6, chapter 8 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_lmm as m
from firm_lmm import black, rebonato_vol

SW = m.swaption_table()


def premium(beta):
    mm = m.model(beta)
    s, ann, _ = mm.swap(5, 10)
    return black(s, s, 5, rebonato_vol(mm, 5, 10), ann) * 1e8


def test_text():
    assert round(dict(m.hw_as_hjm())[10.0], 1) == 4.1
    assert (round(m.F0[0] * 100, 2), round(m.F0[9] * 100, 2)) == (1.98, 3.03)
    assert (round(m.CAPLET_BLACK[1] * 100, 1), round(m.CAPLET_BLACK[9] * 100, 1)) == (33.0, 23.1)
    assert round(math.exp(-0.4 * 8), 2) == 0.04
    assert (round(SW[0][1], 1), round(SW[0][3], 1)) == (25.0, 25.0)
    assert (round(SW[4][1], 1), round(SW[4][3], 1)) == (22.1, 17.3)
    mm = m.model(0.02)
    s, ann, _ = mm.swap(5, 10)
    assert (round(s * 100, 3), round(ann, 3)) == (2.933, 4.102)
    assert (round(premium(0.02) / 1e6, 2), round(premium(0.40) / 1e6, 2)) == (2.35, 1.84)
    assert round((1 - premium(0.40) / premium(0.02)) * 100) == 22
    for row in SW:                                 # Monte Carlo within ~2 standard errors (0.9 vol points)
        assert abs(row[1] - row[2]) < 0.9 and abs(row[3] - row[4]) < 0.9


def test_exercises():
    assert (round(math.exp(-0.4 * 8), 4), round(math.exp(-0.02 * 8), 3)) == (0.0408, 0.852)
    v = [math.sqrt(0.25 * 0.04 * (2 + 2 * r)) for r in (1.0, 0.5)]
    assert [round(x * 100, 2) for x in v] == [20.0, 17.32]
    assert (round(premium(0.02)), round(premium(0.40)), round(premium(0.02) - premium(0.40))) == (
        2_351_823, 1_840_368, 511_456)


def test_problem():
    lo, hi = 0.02, 0.4
    for _ in range(50):
        b = (lo + hi) / 2
        lo, hi = (b, hi) if rebonato_vol(m.model(b), 5, 10) > 0.20 else (lo, b)
    assert round(b, 2) == 0.16
