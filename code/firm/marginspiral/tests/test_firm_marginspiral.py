"""Acceptance tests of the Book 3, Chapter 28 build (margin-spiral simulator)."""
import dataclasses as dc
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_marginspiral import Params, correlation, forced_sale_multiplier, simulate

CALM = dict(vols=(1e-9, 1e-9, 1e-9), corr=0.0, base_margin=(0.1, 0.1, 0.1), margin_spiral=False, shock=(-0.3, 0.0, 0.0))


def test_multiplier_is_one_over_margin_without_impact():
    r = simulate(dc.replace(Params(), impact=(0.0, 0.0, 0.0), **CALM))
    assert r.initial_shortfall > 0 and abs(forced_sale_multiplier(r) - 10.0) < 1e-6


def test_impact_amplifies_and_finer_steps_agree():
    base = simulate(Params())
    fine = simulate(dc.replace(Params(), substeps=8))
    flat = simulate(dc.replace(Params(), impact=(0.0, 0.0, 0.0)))
    assert forced_sale_multiplier(base) > 1.5 * forced_sale_multiplier(flat)
    assert abs(forced_sale_multiplier(fine) / forced_sale_multiplier(base) - 1) < 0.05


def test_ablations():
    base = simulate(Params())
    assert simulate(dc.replace(Params(), forced_selling=False)).forced_sales == 0
    one = simulate(dc.replace(Params(), cross_holding=False))
    assert correlation(one, 0, 1, range(10, 20)) < 0.5 < correlation(base, 0, 1, range(10, 20))
    assert all(p > 0 for day in base.prices for p in day)
