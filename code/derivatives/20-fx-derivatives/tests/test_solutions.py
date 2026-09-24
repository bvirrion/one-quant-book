"""Numbers gate: every numerical answer printed in Book 5, Chapter 20 (text and solutions)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from dv_fx import (
    RD,
    RF,
    S0,
    forward,
    leverage,
    one_touches,
    quotes,
    repricing,
    tarf_scenario,
    tarf_summary,
    vv_smile,
)

Q = quotes()


def test_quotes_and_vv():
    assert (round(100 * Q["atm"], 2), round(Q["k_atm"], 3), round(forward(S0, 1.0, RD, RF), 3)) == (5.32, 6.871, 6.861)
    assert (round(100 * Q["rr25"], 2), round(100 * Q["bf25"], 2), round(Q["k25p"], 3), round(Q["k25c"], 3)) == (1.89, 0.46, 6.662, 7.177)
    assert (round(100 * Q["rr10"], 2), round(100 * Q["bf10"], 2), round(Q["k10p"], 3), round(Q["k10c"], 3)) == (3.77, 1.71, 6.442, 7.702)
    v = vv_smile()
    inner = (v["ks"] > Q["k25p"]) & (v["ks"] < Q["k25c"])
    assert np.max(np.abs(v["market"][inner] - v["vv"][inner])) < 0.0006
    from firm_fxvol import vv_implied
    pill = (Q["k25p"], Q["k_atm"], Q["k25c"])
    vols = (Q["v25p"], Q["atm"], Q["v25c"])
    assert (round(100 * vv_implied(Q["k10c"], pill, vols, S0, 1.0, RD, RF), 2), round(100 * Q["v10c"], 2)) == (7.94, 8.91)


def test_one_touches():
    ot = one_touches()
    got = {k: [round(100 * x, 1) for x in v] for k, v in ot.items()}
    assert got["bs"] == [45.5, 18.1, 6.0, 1.7, 0.4]
    assert got["vv"] == [34.5, 23.8, 21.8, 14.3, 6.7]
    assert got["mix0.0"] == [43.3, 23.3, 14.3, 9.4, 6.5]
    assert got["mix0.5"] == [42.2, 22.8, 14.0, 9.2, 6.4]
    assert got["mix1.0"] == [38.9, 21.3, 13.3, 8.9, 6.2]
    assert round(100 * (ot["mix0.0"][0] - ot["mix1.0"][0]), 1) == 4.4
    assert ot["vv"][2] / max(ot["mix0.0"][2], ot["mix1.0"][2]) > 1.5


def test_slv():
    iv, mkt, _ = repricing(0.5)
    assert [round(100 * x, 2) for x in iv] == [5.22, 4.90, 5.38, 6.77, 8.96]
    assert [round(100 * x, 2) for x in mkt] == [5.14, 4.84, 5.32, 6.72, 8.91]
    assert np.max(np.abs(iv - mkt)) < 0.001
    _, (times, table) = leverage(0.5)
    near = []
    for t in (0.25, 0.5, 1.0):
        c, lev = table[round(t * 252) - 1]
        near.append(round(float(lev[np.argmin(np.abs(c - forward(S0, t, RD, RF)))]), 2))
        assert 1.35 < lev.max() < 1.55
    assert near == [0.76, 0.73, 0.79]


def test_tarf():
    s = {m: tarf_summary(m) for m in (0.0, 0.5, 1.0)}
    assert [round(s[m]["strike"], 3) for m in (0.0, 0.5, 1.0)] == [7.325, 7.312, 7.305]
    assert [round(s[m]["expected_fixings"], 2) for m in (0.0, 0.5, 1.0)] == [1.64, 1.73, 1.78]
    b = s[0.5]
    assert (round(100 * b["redeemed"], 1), round(b["pnl_5"], -3), round(100 * (b["strike"] / b["fwd1y"] - 1), 1)) == (98.1, 126_000, 6.6)
    assert abs(b["pnl_mean"]) < 2_000
    up = tarf_scenario(0.10)
    assert (round(up["pnl_mean"] / 1e6, 2), round(up["first_quarter"] / 1e6, 2), round(up["fixings"], 1)) == (-7.12, -1.01, 11.7)
    assert round(tarf_scenario(0.05)["pnl_mean"] / 1e6, 2) == -0.99
    assert round(tarf_scenario(0.025)["pnl_mean"] / 1e6, 2) == 0.30
