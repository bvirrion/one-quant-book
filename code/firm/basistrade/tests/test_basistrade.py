import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_basistrade import BasisConfig, run_book, simulate_basis  # noqa: E402


def test_calm_book_earns_the_spread_times_leverage():
    cfg = BasisConfig(days=252, dev_sd=0.0, stress_start=10_000)
    r = run_book(simulate_basis(cfg), cfg, 20.0)
    assert abs(r["carry"][:63].sum() - 20 * 0.002 * 63 / 252) < 1e-12 and r["forced"] == 0
    assert abs(r["capital"][-1] - (1 + 20 * 0.002 / 252) ** 252) < 1e-3


def test_stress_forces_sales_only_when_capital_falls_short():
    cfg = BasisConfig(days=900)
    sim = simulate_basis(cfg)
    assert run_book(sim, cfg, 10.0)["forced"] == 0 and run_book(sim, cfg, 50.0)["forced"] > 0
    r = run_book(sim, cfg, 50.0)
    a = sim["stress"][0]
    need = sim["haircut"] + sim["margin"]
    assert (r["capital"][a:a + 80] >= r["face"][a:a + 80] * need[a:a + 80] - 1e-12).all()


def test_scenario_shape():
    cfg = BasisConfig()
    s = simulate_basis(cfg)
    a, b = s["stress"]
    assert s["haircut"][a] == 0.03 and s["haircut"][a - 1] == 0.01 and s["repo"][b] == 0.0 and s["repo"][a] == 0.01
    assert abs(s["shock"][b - 1] - 0.006) < 1e-12 and s["shock"][b + cfg.recover_days] == 0
    assert np.isclose(s["dev"].std(), 0.0003, rtol=0.2)
