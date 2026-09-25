import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_supplytrade import SupplyConfig, simulate_auctions, supply_trade  # noqa: E402


def test_without_noise_the_trade_earns_the_concession_and_its_giveback():
    cfg = SupplyConfig(years=2, daily_vol=0.0, cost=0.0)
    sim = simulate_auctions(cfg)
    r = supply_trade(sim, cfg)
    assert np.allclose(r["before"], sim["concession"]) and np.allclose(r["after"], 0.7 * sim["concession"])


def test_costs_per_leg():
    cfg = SupplyConfig(years=2, daily_vol=0.0, cost=0.1)
    sim = simulate_auctions(cfg)
    both, before = supply_trade(sim, cfg), supply_trade(sim, cfg, True, False)
    assert np.allclose(both["pnl"], 1.7 * sim["concession"] - 0.4)
    assert np.allclose(before["pnl"], sim["concession"] - 0.2)


def test_concession_scales_with_size_over_capacity():
    sim = simulate_auctions(SupplyConfig())
    assert np.allclose(sim["concession"], 0.07 * sim["size"] / sim["capacity"])
