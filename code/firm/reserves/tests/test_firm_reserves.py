"""Acceptance tests of the Book 5, Chapter 27 build (reserve calculator)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_reserves import (
    aggregate,
    bid_offer_reserve,
    concentration_days,
    day_one,
    model_reserve,
    parameter_reserve,
    prudent_point,
    release_schedule,
    stress_grid,
)


def test_prudent_point_and_model_reserve():
    vals = np.linspace(0.0, 10.0, 101)
    assert abs(prudent_point(vals, 0.9) - 1.0) < 0.06                   # the 10 % quantile of a uniform grid
    assert prudent_point([5.0, 1.0, 3.0], 0.9) == 1.0                    # below the first plotting position: the worst
    assert model_reserve({"a": -98.0, "b": -99.0, "c": -97.0}, "a") == 1.0
    assert model_reserve({"a": -99.0, "b": -98.0}, "a") == 0.0           # the booked model is already the prudent one


def test_parameter_reserve():
    r = parameter_reserve(lambda x: -10.0 * x, 0.5, 0.35, 0.65)          # value falls as the input rises
    assert abs(r["booked"] + 5.0) < 1e-12 and r["worst"] == -6.5 and r["best"] == -3.5
    assert abs(r["reserve"] - 1.2) < 0.05                                 # the 90 % point of a uniform range
    assert parameter_reserve(lambda x: 1.0, 0.5, 0.0, 1.0)["reserve"] == 0.0


def test_bid_offer_aggregation_day_one_release():
    b = bid_offer_reserve({"v": -200.0, "d": 1_000.0}, {"v": 0.5, "d": 0.001})
    assert b == {"v": 100.0, "d": 1.0, "total": 101.0}
    assert aggregate([1.0, 2.0, 3.0]) == 3.0
    d = day_one(100.0, 98.0, 0.6, 1.0)
    assert (round(d.margin, 12), round(d.recognised, 12)) == (2.0, 0.4)
    s = release_schedule([(0.0, 1.0), (1.0, 0.6), (2.0, 0.7), (3.0, 0.0)])
    assert [round(x[2], 12) for x in s] == [0.0, 0.4, -0.1, 0.7] and abs(sum(x[2] for x in s) - 1.0) < 1e-12


def test_stress_and_concentration():
    g = stress_grid(lambda ds, dv: -100 * ds + 10 * dv, (-0.1, 0.0, 0.1), (-0.05, 0.05), hedge_delta=100.0)
    assert np.allclose(g, [[-0.5] * 3, [0.5] * 3])
    assert concentration_days(-50_000.0, 10_000.0, 0.1) == 50.0
