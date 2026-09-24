"""Numbers in the solutions of Book 3, Chapter 20."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import m3_amm as m
from firm_amm import cp_amount_out

E18 = 10**18


def test_exercises():
    out = cp_amount_out(10 * E18, 1_000 * E18, 3_000_000 * E18) / E18
    assert round(out, 2) == 29_614.74 and round(out / 10, 2) == 2_961.47
    assert round(m.impermanent_loss(4), 2) == -0.20
    assert round(0.64 / 8, 2) == 0.08 and round(1e4 * 0.64 / 8 / 365, 2) == 2.19
    assert round(50e6 * 0.25 / 365 / 8) == 4_281 and round(20e6 * 0.0005) == 10_000
    assert round(100 * m.breakeven_turnover(0.5, 0.0005), 1) == 17.1
    daily = [round(1e4 * m.lvr_mean(steps_per_day=s, paths=400)[0][-1], 1) for s in (96, 24, 1)]
    assert daily == [37.0, 37.0, 37.7]
    assert round(1e4 * (1 - math.exp(-0.36 / 8 * 30 / 365)), 1) == 36.9


def test_problem():
    sd = 0.36 / 365 / 8
    assert round(1e4 * sd, 2) == 1.23 and round(10e6 * sd) == 1_233
    assert round(6e6 * 0.003 * 10 / 200) == 900
    assert round(100 * m.breakeven_turnover(0.6, 0.003), 2) == 4.11
    assert round((900 - 10e6 * sd) * 365) == -121_500
    assert round((900 - 10e6 * 1.44 / 365 / 8) * 365) == -1_471_500
    assert round(6e6 * 0.0005 * 10 / 200) == 150 and round(100 * m.breakeven_turnover(0.6, 0.01), 2) == 1.23
