import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_statbook import attribution, borrow_fees, financing, hard_to_borrow, reg_t_equity, stress_equity


def test_fees_and_htb():
    f = borrow_fees(10000, seed=1, htb_share=0.05)
    assert abs(np.mean(f == 0.0025) - 0.95) < 0.01
    assert abs(np.median(f[f != 0.0025]) - 0.03) < 0.005
    assert hard_to_borrow([0.0025, 0.02]).tolist() == [False, True]


def test_margin_by_hand():
    assert reg_t_equity(100.0, -100.0) == 100.0                          # 2x gross on Reg T
    assert stress_equity([1.0, -1.0], 100.0, 0.15) == 30.0               # gross 2 x 15% on capital 100


def test_financing_by_hand():
    w = np.array([0.8, 0.7, -0.75, -0.75])                              # long 1.5, short 1.5
    fin = financing(w, 1.0, rate=0.05, long_spread=0.005, fees=np.array([0, 0, 0.0025, 0.08]))
    assert abs(fin["debit"] - 0.5) < 1e-12
    assert abs(fin["long_cost"] - 0.5 * 0.055 / 252) < 1e-15
    assert abs(fin["short_rebate"] - (0.75 * 0.0475 + 0.75 * -0.03) / 252) < 1e-15
    assert abs(fin["borrow_cost"] - 0.75 * 0.0825 / 252) < 1e-15
    assert abs(fin["total"] - (fin["short_rebate"] - fin["long_cost"])) < 1e-18


def test_attribution_adds_up():
    rng = np.random.default_rng(2)
    X = rng.standard_normal((50, 4))
    f = rng.standard_normal(4) * 0.01
    e = rng.standard_normal(50) * 0.02
    w = rng.standard_normal(50) * 0.02
    a = attribution(w, X, f, e, cost=1e-4, fin=-2e-5)
    assert abs(a["total"] - (w @ (X @ f + e) - 1e-4 - 2e-5)) < 1e-15
    assert abs(a["by_factor"].sum() - a["factor"]) < 1e-15
