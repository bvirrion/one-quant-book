"""Acceptance tests of the Book 6, chapter 12 build (prepayment model and OAS)."""
import math
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_mbsoas import Pool, PrepayModel, analyse, pool_flows, pv_paths, simulate_paths, solve_oas


class Flat:
    def df_t(self, t):
        return math.exp(-0.04 * t)


POOL = Pool(term=120, age=0)


def test_no_prepayment_gives_the_amortising_loan():
    m = PrepayModel(turnover_speed=0.0, refi_top=0.0)
    rs, p10 = simulate_paths(Flat(), 0.03, 0.009, 120, 200)
    io, po = pool_flows(POOL, m, p10)
    assert po.sum(axis=1) == pytest.approx(np.full(200, 100.0), rel=1e-10)
    assert np.allclose(io, io[0]) and np.allclose(po, po[0])


def test_oas_reprices_and_strips_add_up():
    rs, p10 = simulate_paths(Flat(), 0.03, 0.009, 120, 400)
    io, po = pool_flows(POOL, PrepayModel(), p10)
    oas = solve_oas(100.0, io + po, rs)
    assert pv_paths(io + po, rs, oas).mean() == pytest.approx(100.0, abs=1e-8)
    assert pv_paths(io, rs, oas).mean() + pv_paths(po, rs, oas).mean() == pytest.approx(100.0, abs=1e-8)


def test_negative_convexity_and_burnout():
    out = analyse(Flat(), Pool(term=240, age=12, wac=0.0625, coupon=0.0575), PrepayModel(mortgage_spread=0.017),
                  100.0, paths=800)
    assert out["convexity"] < 0 and out["option_cost"] > 0 and out["duration"] > 0
    assert out["io_up"] > out["io"] > out["io_dn"] and out["po_up"] < out["po"] < out["po_dn"]
    m0, m1 = PrepayModel(burnout=0.0), PrepayModel(burnout=0.5)
    inc, cum = np.array([0.02]), np.array([4.0])
    assert m1.cpr(60, inc, cum)[0] < m0.cpr(60, inc, cum)[0]
