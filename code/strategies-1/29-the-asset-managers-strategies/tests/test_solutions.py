"""Numbers gate: every numerical answer printed in Book 8, chapter 29 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s1_assetmgr import SIZES, full_turnover, replicate, transition_plan, value_product  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def test_sampling():
    got = {n: (r(100 * replicate(n)["te"]), r(100 * replicate(n)["te_ex"]), r(replicate(n)["turnover"]),
               r(1e4 * replicate(n)["cost"], 1), r(100 * replicate(n)["mean_active"])) for n in SIZES}
    assert got == {25: (4.84, 4.7, 1.34, 13.4, 3.0), 50: (2.96, 2.81, 1.13, 11.3, 2.21), 100: (1.64, 1.52, 0.92, 9.2, 1.29),
                   200: (0.81, 0.71, 0.58, 5.8, 0.42), 400: (0.32, 0.26, 0.31, 3.1, 0.03)}
    assert r(full_turnover(), 3) == 0.064


def test_value_product():
    got = {k: (r(100 * value_product(k)["te"]), r(100 * value_product(k)["excess"]), r(value_product(k)["exposure"]),
               r(value_product(k)["ir"])) for k in (0.25, 0.5, 1.0)}
    assert got == {0.25: (1.57, 0.07, 0.26, 0.04), 0.5: (3.08, 0.07, 0.52, 0.02), 1.0: (6.0, 0.06, 1.03, 0.01)}


def test_transition():
    plan, turn, ase = transition_plan()
    assert (r(turn, 3), r(100 * ase)) == (0.592, 3.46)
    assert {d: (r(1e4 * c, 1), r(1e4 * s, 1), r(1e4 * (c + s), 1)) for d, (c, s) in plan.items()} == \
        {1: (27.6, 21.8, 49.4), 2: (21.3, 24.4, 45.6), 3: (18.5, 27.2, 45.6), 5: (15.6, 32.3, 48.0), 10: (12.8, 42.8, 55.6)}


def test_exercises():
    assert r(1 / math.sqrt(2), 3) == 0.707 and r(4.84 / 2.96, 2) == 1.64 and r(1.64 / 0.81, 2) == 2.02
    assert r(0.064 * 10, 2) == 0.64 and r(3.46 / math.sqrt(252) * 100, 1) == 21.8
    assert r(0.03 * 0.52, 4) == 0.0156


def test_two_sd_planner():
    plan, _, _ = transition_plan()
    got = {d: r(1e4 * (c + 2 * s), 1) for d, (c, s) in plan.items()}
    assert got == {1: 71.2, 2: 70.0, 3: 72.8, 5: 80.3, 10: 98.3}
