"""Numbers gate: every numerical answer printed in Book 10, chapter 22 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from mx_riskbid import basket, bids, blind, price, transition_study, universe  # noqa: E402


def r(x, d=1):
    return round(float(x), d)


def test_universe_basket_and_cost():
    u = universe()
    assert len(u["adv"]) == 786
    assert (r(np.median(u["adv"]) / 1e6), r(np.median(u["sigma"]), 0), r(np.median(u["spread"]))) == (37.5, 171, 5.9)
    names, q = basket()
    assert len(names) == 500 and r(q.sum() / 1e6) == 250.0
    assert (round(q.min(), -3), r(q.max() / 1e6), r(100 * np.median(q / u["adv"][names]))) == (38_000, 4.8, 1.0)
    p = price(names, q)
    assert (r(p["cost"]), r(p["risk"]), r(p["risk_hedged"]), p["days_max"]) == (14.9, 40.4, 12.5, 1.0)
    prof = blind()["profile"]["buckets"]
    assert r(100 * prof[:4].sum()) == 98.8


def test_bids_named_result():
    b = bids()
    d, bl = b["disclosed"], b["blind"]
    assert (r(d["bid"]), r(bl["bid"]), r(d["curse"]), r(bl["curse"])) == (33.6, 36.4, 4.2, 4.4)
    assert (r(d["sigma_est"]), r(d["naive_profit"]), r(d["shaded_profit"])) == (4.1, -2.2, 2.0)
    s = blind()
    assert (r(s["cost"][0]), r(s["cost"][1]), r(s["risk"][0]), r(s["risk"][1])) == (17.0, 0.4, 13.0, 1.1)
    assert (r(s["cost"][0] - b["disclosed_true"]["cost"]), r(bl["curse"] - d["curse"]), r(bl["bid"] - d["bid"])) == (2.1, 0.2, 2.8)
    assert r(math.sqrt(1) * 1.029375, 2) == 1.03


def test_transition_and_exercises():
    t = transition_study()
    assert (r(t["full"] / 1e6, 0), r(t["netted"] / 1e6, 0), r(t["crossed"] / 1e6, 0)) == (500, 322, 258)
    assert (r(t["cost_full"]), r(t["cost_netted"]), r(t["cost_crossed"])) == (50.4, 32.8, 24.0)
    from firm_riskbid import curse, liquidation
    liq = liquidation([0.3], [1.0], [200.0], [6.0])
    assert (r(liq["days"][0], 2), r(liq["cost_bp"][0])) == (1.5, 65.6)
    assert r(150 * math.sqrt(3 / 3), 0) == 150 and (r(curse(4.0, 5), 2), r(curse(1.0, 5), 2)) == (5.07, 1.27)
    b = bids()["disclosed_true"]
    base = b["cost"] + 2 * b["risk_hedged"]
    sh = curse(0.15 * base, 3)
    assert (r(2 * b["risk_hedged"]), r(sh), r(base + sh + 2.0)) == (25.0, 6.2, 48.1)
