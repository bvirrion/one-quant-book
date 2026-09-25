import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_mergerarb import (  # noqa: E402
    DealConfig,
    annualised,
    collar_hedge,
    collar_value,
    implied_probability,
    portfolio,
    simulate_deals,
    spread,
)


def test_spread_and_probability_by_hand():
    assert abs(spread(38.6, 40.0) - 0.036269) < 1e-6
    assert abs(implied_probability(38.6, 40.0, 30.0) - 0.86) < 1e-12
    assert abs(annualised(0.036269, 126) - (1.036269**2 - 1)) < 1e-12


def test_collar():
    a = np.array([8.0, 10.0, 12.0, 14.0])
    assert np.allclose(collar_value(a, 2.0, 9.0, 13.0), [18.0, 20.0, 24.0, 26.0])
    assert np.allclose(collar_hedge(a, 2.0, 9.0, 13.0), [0.0, 2.0, 2.0, 0.0])


def test_deals_price_and_resolve():
    mkt = np.full(2000, 0.0002)
    deals = simulate_deals(mkt, DealConfig(), np.random.default_rng(0))
    assert len(deals) > 300
    d = deals[0]
    assert d["price"][-1] == (d["offer"] if not d["broke"] else d["price"][-1]) and 0.5 < d["implied"] < 1.0
    brk = np.mean([x["broke"] for x in deals])
    assert abs(brk - 0.06) < 0.03                                      # a flat market: the base break rate
    r, c = portfolio(deals, 2000)
    assert c.max() > 10 and r.mean() > 0
