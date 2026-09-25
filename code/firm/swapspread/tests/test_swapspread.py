import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_swapspread import YEAR, SwapConfig, long_spread, simulate_spread  # noqa: E402


def test_flat_spread_earns_its_carry_and_the_charge_is_fifty_bp():
    cfg = SwapConfig()
    s = {"spread": np.full(YEAR + 1, -40.0)}
    r = long_spread(s, cfg, 0, YEAR, True)
    assert abs(r["carry"].sum() * 1e4 - 40.0) < 1e-9 and abs(r["marks"]).max() == 0
    assert abs(r["charge"].sum() * 1e4 + 50.0) < 1e-9 and abs(r["float_repo"].sum() * 1e4 - 5.0) < 1e-9


def test_quarter_end_dips_after_the_regulation_only():
    cfg = SwapConfig(noise_sd=0.0)
    s = simulate_spread(cfg)
    q = YEAR // 4
    assert s["dip"][:cfg.regulation].max() == 0
    t_year_end = 6 * YEAR - 1
    assert s["year_end"][t_year_end] and abs(s["dip"][t_year_end] - 2 * cfg.qe_dip) < 1e-12
    assert abs(s["dip"][5 * YEAR + q - 1] - cfg.qe_dip) < 1e-12 and s["dip"][5 * YEAR + q] == 0
