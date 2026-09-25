import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_syscredit import SysCreditConfig, ap_arbitrage, factor_book, simulate_bonds  # noqa: E402


def test_stale_prices_only_move_on_trades_and_nav_is_their_mean():
    cfg = SysCreditConfig(bonds=20, days=300, stress_start=10_000)
    s = simulate_bonds(cfg)
    moved = s["stale"][1:] != s["stale"][:-1]
    assert moved.mean() < 0.35 and np.allclose(s["nav"], s["stale"].mean(axis=1))


def test_no_arbitrage_without_a_dislocation():
    cfg = SysCreditConfig(bonds=20, days=300, stress_start=10_000)
    s = simulate_bonds(cfg)
    assert (ap_arbitrage(s, cfg)["profit"] == 0).all()


def test_factor_books_are_long_short():
    cfg = SysCreditConfig(bonds=50, days=400, stress_start=10_000)
    s = simulate_bonds(cfg)
    for name in ("value", "momentum", "lowrisk"):
        x = factor_book(s, cfg, name)
        assert (x[:127] == 0).all() and np.isfinite(x).all() and x[200:].std() > 0
