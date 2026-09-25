import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_mbsrv import MbsConfig, PrepayModel, coupon_stack, io_trade, strip_paths, tranche_rv  # noqa: E402

CFG = MbsConfig(paths=200)


def test_io_and_po_add_up_to_the_pass_through():
    s = strip_paths(CFG, PrepayModel())
    assert np.allclose(s["io"] + s["po"], s["pt"]) and (s["io"] > 0).all()


def test_no_view_no_gain_and_the_hedge_is_long_treasuries():
    r = io_trade(CFG, PrepayModel(), PrepayModel(), shifts=(0.0, 0.01))
    assert abs(r["gain"][0]) < 1e-9 and r["hedge"] > 0
    assert io_trade(CFG, PrepayModel(), PrepayModel(burnout=1.0))["gain"][0] > 0


def test_same_model_same_oas():
    row = coupon_stack(CFG, PrepayModel(), PrepayModel(), [0.06])[0]
    assert abs(row["oas_view"] - CFG.market_oas) < 1e-6 and row["duration"] > 0


def test_tranche_same_correlation():
    r = tranche_rv(rho_true=0.30, trials=200)
    assert abs(r["el_market"] - r["el_true"]) < 1e-12 and 0 <= r["wipeout"] <= r["p_loss"] + 1e-12
