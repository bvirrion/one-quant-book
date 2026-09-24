"""Numbers gate: every numerical answer printed in Book 5, Chapter 25 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from dv_volpnl import book_explain, carry, risk_reversal, scalp, short_vol


def test_scalp_and_named_result():
    s = scalp()
    assert round(s["uniform"]["premium"], 2) == 4.15
    assert all(round(s[k]["realised"], 12) == 0.25 for k in ("uniform", "wrong", "right"))
    assert [round(s[k]["daily"].sum(), 2) for k in ("uniform", "wrong", "right")] == [3.28, -0.78, 2.87]
    assert [round(s[k]["approx"].sum(), 2) for k in ("uniform", "wrong", "right")] == [3.05, -0.86, 3.03]
    w = s["wrong_split"]
    assert (round(w["quiet"], 2), round(w["wild"], 2), round(100 * w["move"], 2)) == (-0.80, 0.02, 2.84)
    assert (round(100 * w["quiet_vol"], 1), round(100 * w["wild_vol"])) == (7.9, 45)
    assert round(s["wrong"]["path"][15], 1) == 107.8 and round(100 * 0.25 / math.sqrt(252), 2) == 1.57
    cg = s["uniform"]["cash_gamma"][0]
    assert round(cg, -1) == 770 and round(s["wrong"]["cash_gamma"][15]) == 39 and round(cg / s["wrong"]["cash_gamma"][15]) == 20
    assert round(cg * (0.02 ** 2 - 0.18 ** 2 / 252), 3) == 0.208 and round(cg * 0.18 ** 2 / 252, 3) == 0.099
    assert round(100 * 0.18 / math.sqrt(252), 2) == 1.13
    assert round(15 * 0.005 ** 2 + 6 * w["move"] ** 2, 5) == round(0.25 ** 2 * 21 / 252, 5) == 0.00521


def test_carry():
    c = carry()
    assert [round(100 * v, 2) for v in c["vols"]] == [19.70, 20.92, 21.79, 23.89]
    assert (round(c["v0"], 2), round(c["v1"], 2), round(c["carry"], 2)) == (8.69, 6.81, -1.88)
    assert (round(c["theta_only"], 2), round(c["roll"], 2), round(100 * c["roll_down"], 2)) == (-1.59, -0.28, -0.87)
    assert (round(c["ratio"], 2), round(c["cal_day"], 2), round(c["cal_gamma"], 2)) == (1.73, 0.13, -0.17)


def test_risk_reversal():
    r = risk_reversal()
    assert (round(r["kp"], 1), round(r["kc"], 2), round(100 * r["vol_p"], 1), round(100 * r["vol_c"], 1)) == (93.6, 106.96, 21.3, 18.7)
    assert round(-r["sticky_strike_hedge"], 2) == 0.5
    ss, sd = r["sticky_strike"], r["sticky_delta"]
    assert [round(ss[k], 3) for k in ("gamma", "vega", "vanna", "unexplained", "total")] == [0.053, -0.003, 0.0, -0.077, -0.023]
    assert [round(sd[k], 3) for k in ("gamma", "vega", "vanna", "unexplained", "total")] == [0.053, -0.003, 0.112, -0.085, 0.081]
    assert round(0.10 * math.log(0.95) / 0.5, 4) == -0.0103


def test_book_explain():
    b = book_explain()
    assert (round(b["spot"][-1], 1), round(b["spot"].min(), 1), round(100 * b["vol"][-1])) == (98.6, 94.3, 19)
    tot = {k: {a: round(float(x.sum()), 2) for a, x in b[k].items()} for k in ("sticky_strike", "sticky_delta")}
    assert tot["sticky_strike"] == {"delta": 0.0, "gamma": 2.87, "theta": -1.90, "vega": 1.65, "vanna": -2.24, "volga": -0.76,
                                    "total": -0.53, "unexplained": -0.16}
    assert tot["sticky_delta"] == {"delta": 0.0, "gamma": 2.90, "theta": -1.90, "vega": 1.15, "vanna": -1.67, "volga": -0.62,
                                   "total": -0.22, "unexplained": -0.09}
    assert round(max(float(np.abs(b[k]["unexplained"]).max()) for k in ("sticky_strike", "sticky_delta")), 2) == 0.08


def test_short_vol():
    v = short_vol()
    assert len(v["pnl"]) == 120
    assert (round(100 * v["implied"].mean(), 1), round(100 * v["realised"].mean(), 1)) == (23.5, 20.6)
    assert (round(v["mean"], 2), round(v["sd"], 2), round(v["sharpe"], 2), round(100 * v["hit"])) == (0.44, 1.33, 1.15, 74)
    assert (round(v["best"], 2), round(v["worst"], 2), round(v["skew"], 2)) == (2.89, -5.04, -1.35)
    assert round((v["mean"] - v["worst"]) / v["sd"], 1) == 4.1
    z = short_vol(premium=0.0)
    assert (round(z["mean"], 3), round(z["sd"], 2), round(z["sharpe"], 2), round(z["sd"] / math.sqrt(120), 2)) == (-0.008, 1.33, -0.02, 0.12)
    assert (round(100 * z["implied"].mean(), 1), round(100 * math.sqrt(np.mean(z["implied"] ** 2)), 1),
            round(100 * math.sqrt(np.mean(z["realised"] ** 2)), 1)) == (21.5, 23.0, 23.2)
