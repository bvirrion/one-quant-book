"""Numbers in the solutions of Book 3, Chapter 16."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import m3_spot as m


def test_exercises():
    assert 3_000 / 60_000 == 0.05 and round(1e4 * -3 * math.log(1 - 0.001), 1) == 30.0
    assert round(60_000 / 60_030, 4) == 0.9995
    assert [round(100 * m.p_loss(100, 20, t, 0.6), 1) for t in (30, 60)] == [3.9, 10.6]
    assert round(1 - 0.12 * (1 + 0.6 / 0.4), 2) == 0.70
    assert [m.count_opportunities(f) for f in (0, 0.0002, 0.0005, 0.001)] == [
        (1254, 2953), (794, 1902), (309, 793), (26, 120)]


def test_problem():
    risk = 1.65 * 0.7 * math.sqrt(60 / 525_600)
    assert round(100 * (1.001 * 1.0005 - 1), 2) == 0.15 and round(100 * risk, 2) == 1.23
    kept = 0.9995 * 0.995 * 0.98
    assert round(100 * kept, 2) == 97.46
    assert round(100 * m.kimchi_breakeven(), 2) == 4.03
    assert round(100 * (1.15 * kept / (1.001 * 1.0005) - 1), 1) == 11.9
    assert round(100 * m.kimchi_breakeven(repatriation=0), 2) == 1.95
    assert round(100 * m.kimchi_breakeven(minutes=10), 2) == 3.28
    assert round(50_000 * (1.15 * kept / (1.001 * 1.0005) - 1)) == 5_956
