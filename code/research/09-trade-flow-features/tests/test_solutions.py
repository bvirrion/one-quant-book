"""Numbers gate: every numerical answer printed in Book 7, chapter 9 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "tradeflow"))
from firm_tradeflow import bvc, lee_ready, tick_rule, vpin
from rs_tradeflow import (
    CFG,
    hawkes_fits,
    kyle,
    memory,
    orders,
    signed_flow,
    signing,
    stale_quotes,
    tape,
    toxicity_race,
)


def r(x, d=3):
    return round(float(x), d)


def test_signing():
    s = signing()
    assert r(s["quote (on time)"], 4) == 1.0
    assert (r(s["quote (0.2 s late)"], 3), r(s["Lee-Ready (0.2 s late)"], 3)) == (0.991, 0.993)
    assert (r(s["quote (1 s late)"], 3), r(s["Lee-Ready (1 s late)"], 3), r(s["tick"], 3)) == (0.963, 0.971, 0.952)
    assert r(s["BVC, 1-minute bars (volume)"], 3) == 0.804
    assert r(100 * (s["quote (on time)"] - s["quote (1 s late)"]), 1) == 3.7
    q = stale_quotes()
    assert (r(100 * q[0.05], 1), r(100 * q[0.5], 1), r(100 * q[2.0], 1)) == (99.7, 97.9, 93.8)
    assert r(100 * (1 - q[2.0]), 1) == 6.2


def test_memory_and_hawkes():
    acf, h = memory()
    assert len(orders()[0]) == 7_273
    assert (r(acf[1], 2), r(acf[10], 3), r(acf[100], 3), r(h)) == (0.20, 0.087, 0.028, 0.715)
    assert (3 - 1.5) / 2 == 0.75
    here, flat = hawkes_fits()
    assert (r(here["branching"], 2), r(flat["branching"], 3)) == (0.65, 0.403)


def test_signed_flow():
    f = signed_flow()
    got = [(r(f[n]["sign_corr"], 2), r(100 * f[n]["hit"], 1), r(f[n]["ahead"], 2), r(f[n]["behind"], 2)) for n in (5, 20, 100)]
    assert got == [(0.25, 56.1, 0.16, 0.22), (0.24, 58.4, 0.14, 0.31), (0.18, 57.1, 0.12, 0.17)]
    assert f[20]["behind"] > 2 * f[20]["ahead"]


def test_toxicity_race():
    t = toxicity_race()
    assert t["bucket"] == 2_649 and round(CFG.seconds / 400) == 27
    assert (round(100 * t["informed_pre"]), round(100 * t["informed_ep"])) == (15, 45)
    assert (r(t["markout_trade_pre"], 2), r(t["markout_trade_ep"], 2)) == (-0.36, 0.96)
    v, m = t["vpin"], t["markout"]
    assert (r(v["pre"], 2), r(v["ep"], 2), round(100 * (v["ep"] / v["pre"] - 1))) == (0.31, 0.35, 13)
    assert v["argmax"] > 6000 and r(v["argmax"] / 60, 1) == 119.7 and round((v["argmax"] - 6000) / 60) == 20
    assert (round(v["first"] - 5400), r(100 * v["false"], 1)) == (16, 6.0)
    assert (r(m["pre"], 2), r(m["ep"], 2), m["argmax"], m["first"], r(100 * m["false"], 1)) == (
        -0.38, 0.84, 5740.0, 5440.0, 8.4)


def test_kyle():
    k = kyle()
    assert (r(k["lambda"], 2), round(100 * k["r2"])) == (0.10, 14)
    assert r(30 * 0.10, 1) == 3.0


def test_exercises():
    px = np.array([20.00, 20.01, 20.01, 20.00, 19.99])
    assert list(tick_rule(px)) == [0, 1, 1, -1, -1]
    assert list(lee_ready(px, np.full(5, 20.00), np.full(5, 20.01))) == [-1, 1, 1, -1, -1]
    assert r(bvc([0.8], [1.0], 1.0)[0]) == 0.788
    assert (r(1.4 - 1, 1), r((3 - 1.4) / 2, 1)) == (0.4, 0.8)
    b = np.array([700, 400, 900, 500, 200], float)
    per_trade_buys = np.repeat(b, 2) / 2
    per_trade_sells = np.repeat(1000 - b, 2) / 2
    buy_vol = np.ravel(np.column_stack([per_trade_buys[::2] + per_trade_buys[1::2], np.zeros(5)]))
    vol = np.ravel(np.column_stack([per_trade_buys[::2] + per_trade_buys[1::2],
                                    per_trade_sells[::2] + per_trade_sells[1::2]]))
    assert r(vpin(buy_vol, vol, 1000.0, 5)[-1], 3) == 0.4
    assert math.isclose(tape().trades["qty"].sum() / 400, 2_649, rel_tol=1e-9)
