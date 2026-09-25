import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_cryptomf import (  # noqa: E402
    CoinConfig,
    basis_carry,
    carry_return,
    flow_ic,
    momentum_book,
    simulate_coins,
    venue_losses,
)


def test_carry_accounting():
    assert math.isclose(carry_return(0.30, 0.2, 0.0), 0.25)
    assert math.isclose(basis_carry(102.0, 100.0, 73.0), 0.10)


def test_momentum_and_flows_on_planted_coins():
    C = simulate_coins(CoinConfig(coins=30, days=1500), np.random.default_rng(3))
    p = momentum_book(C["r"], 28, 7, 0.2, 0.0)[60:]
    assert p.mean() > 0
    ic, t = flow_ic(C["flow"], C["r"], 30)
    assert ic < 0 and t < -3


def test_venue_losses():
    L = venue_losses(4, 0.1, 0.8, 200_000, np.random.default_rng(0))
    assert abs(L.mean() - 0.08) < 0.002 and set(np.round(np.unique(L), 6)) <= {0.0, 0.2, 0.4, 0.6, 0.8}
