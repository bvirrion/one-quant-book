import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_deltaone import (  # noqa: E402
    DeltaOneConfig,
    dividend_market,
    financing_trade,
    index_arb,
    issuer_dividend_exposure,
    simulate_financing,
)

CFG = DeltaOneConfig(days=252, minutes=5000, scenarios=2000)


def test_arbitrage_without_lag_never_loses():
    sim = simulate_financing(CFG)
    assert (index_arb(sim, CFG, 0)["pnl"] > 0).all()
    sim["mispricing"] = np.array([0.0, 6.0, 3.0, -1.0, 0.0])
    assert np.allclose(index_arb(sim, CFG, 0)["pnl"], [(6.0 - -1.0) - 5.0])


def test_financing_trade_by_hand():
    sim = {"spread": np.full(252, 45.0)}
    f = financing_trade(sim, CFG)
    assert np.allclose(f["net"], (45 - 15) * 63 / 252 - 5.0) and f["taken"].all()


def test_issuer_is_long_dividends():
    assert issuer_dividend_exposure(n_paths=2000)["issuer_gain"] > 0


def test_dividend_futures_below_expected_and_zero_discount_is_fair():
    d = dividend_market(CFG)
    assert (d["futures"] < d["expected"]).all()
    d0 = dividend_market(DeltaOneConfig(scenarios=2000, discount=0.0))
    assert np.allclose(d0["return"].mean(axis=0), 0.0, atol=1e-12)
