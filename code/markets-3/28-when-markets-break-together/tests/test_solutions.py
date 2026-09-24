"""Numbers in the solutions of Book 3, Chapter 28."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import m3_break as m
from firm_marginspiral import forced_sale_multiplier


def test_exercises():
    assert 10e6 / 0.125 == 80e6
    t = {name: s for name, s, _, _ in m.ablation_table()}
    assert round(t["base case"] - t["no price impact"], 1) == 99.3
    assert round(9 * (1.18 - 0.54), 2) == 5.76
    half = m.run(leverage=4.0)
    assert half.forced_sales == 0 and forced_sale_multiplier(half) == 0


def test_problem():
    r = m.run()
    assert round(r.initial_shortfall / 1e9, 1) == 25.2 and round(r.forced_sales / 1e9, 1) == 223.6
    assert round(forced_sale_multiplier(r), 2) == 8.88
    assert [round(x, 1) for x in r.prices[20]] == [82.8, 93.0, 79.6]
    d = dict((x[0], x[2]) for x in m.march_2020())
    assert round(100 * (d["2020-03-23"] / d["2020-03-09"] - 1), 1) == 7.6
