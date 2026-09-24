"""Numbers gate: every numerical answer printed in Book 5, Chapter 15 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from dv_barrier import (
    barrier_table,
    calendar_example,
    digital_prices,
    hook,
    local_vol_doc,
    monitoring,
    overhedge,
    reverse_barrier,
    symmetry_example,
    width_for_loss_cap,
)
from firm_barrier import BGK_BETA, barrier, bgk_shift, mc_barrier

M = 1e6


def test_hook_and_digital():
    h = hook()
    assert round(h["per_point"] / M, 2) == 1.25 and round(h["index_notional"] / 1e9, 2) == 6.25
    assert round(h["value"] / M, 1) == 4.9
    d = digital_prices()
    assert (round(100 * d["atm"], 1), round(d["flat"] / M, 2), round(d["smile"] / M, 2), round(d["vega_term"] / M, 2)) == (
        16.4, 4.84, 5.77, 0.93)


def test_overhedge():
    assert width_for_loss_cap() == 200
    costs = {w: overhedge(w)["cost"] / M for w in (50, 100, 200, 400)}
    assert [round(costs[w], 2) for w in (50, 100, 200, 400)] == [0.25, 0.48, 0.89, 1.56]
    o = overhedge(200)
    assert round(o["spread"] / M, 2) == 6.66 and o["per_point"] == 50_000
    assert 1e7 / 200 * (4900 - 4800) == 5e6


def test_barrier_sheet():
    b = barrier_table()
    got = {k: round(v, 2) for k, v in b.items() if k in ("call", "doc", "dic", "doc_rebate", "uoc")}
    assert got == {"call": 8.83, "doc": 7.23, "dic": 1.60, "doc_rebate": 8.41, "uoc": 3.10}
    assert (round(b["one_touch_hit"], 3), round(b["one_touch_exp"], 3), round(b["no_touch"], 3), round(b["dnt"], 3)) == (
        0.592, 0.581, 0.390, 0.141)
    assert round(7.23 + 1.70, 2) == 8.93


def test_monitoring():
    rows = {r["n"]: r for r in monitoring()}
    assert round(rows[252]["cont"], 2) == 7.23
    got = {n: (round(r["mc"], 2), round(r["shifted"], 2)) for n, r in rows.items()}
    assert got == {252: (7.48, 7.45), 52: (7.62, 7.68), 12: (8.01, 8.04), 4: (8.33, 8.38)}
    assert round(rows[252]["se"], 2) == 0.03
    up = {r["n"]: r for r in monitoring(120.0, "up-out")}
    assert (round(up[252]["mc"], 2), round(up[252]["shifted"], 2), round(up[4]["mc"], 2), round(up[4]["shifted"], 2)) == (
        1.26, 1.28, 2.19, 2.50)
    lv = local_vol_doc()
    assert (round(lv["lv"], 2), round(lv["bs_atm"], 2), round(100 * lv["atm"], 1)) == (6.15, 6.51, 19.2)


def test_static():
    s = symmetry_example()
    assert (round(s["ratio"], 2), s["puts_strike"], round(s["price"], 3), round(s["closed"], 3)) == (1.11, 81.0, 1.498, 1.498)
    assert (round(s["hit_puts"], 2), round(s["hit_call"], 2)) == (2.08, 0.83)
    c = calendar_example()
    assert round(c["uoc"], 3) == 1.105
    assert (round(c["prices"][4], 2), round(c["prices"][16], 2), round(c["prices"][64], 2)) == (1.77, 1.28, 1.15)
    early = c["times"] < 0.75
    assert round(float(np.abs(c["on_barrier"][4][early]).max()), 1) == 5.4
    assert round(float(np.abs(c["on_barrier"][16][early]).max()), 2) == 0.16


def test_gap():
    r = reverse_barrier()
    assert (round(r["v119"], 2), round(r["d119"], 2), round(r["pnl_gap"], 2), round(r["pnl_small"], 3)) == (
        1.38, -1.37, -6.81, 0.005)
    assert round(-r["d119"] * 6, 2) == 8.19 and round(-r["pnl_gap"] / r["v119"]) == 5
    i = int(np.argmax(r["value"]))
    assert round(float(r["spots"][i])) == 111 and round(float(r["value"][i]), 2) == 7.68
    assert round(100 * (1.0280 / 1.2010 - 1), 1) == -14.4


def test_exercises():
    assert (round(bgk_shift(90.0, 100.0, 0.2, 1 / 252), 2), round(bgk_shift(120.0, 100.0, 0.2, 1 / 252), 2)) == (89.34, 120.88)
    # beta = -zeta(1/2) / sqrt(2 pi): zeta(1/2) from the alternating series, accelerated by repeated averaging
    partial, s = [], 0.0
    for n in range(1, 41):
        s += (-1) ** (n - 1) / math.sqrt(n)
        partial.append(s)
    avg = partial
    for _ in range(30):
        avg = [0.5 * (a + b) for a, b in zip(avg[:-1], avg[1:], strict=True)]
    zeta_half = avg[-1] / (1 - 2 ** 0.5)
    assert round(-zeta_half / math.sqrt(2 * math.pi), 4) == BGK_BETA
    cont = barrier(100, 100, 90, 1.0, 0.03, 0.01, 0.2, "down-out", "P")
    assert round(cont, 3) == 0.162
    got = []
    for n in (252, 52, 12, 4):
        mc = mc_barrier(100, 100, 90, 1.0, 0.03, 0.01, 0.2, "down-out", "P", n)[0]
        sh = barrier(100, 100, bgk_shift(90, 100, 0.2, 1 / n), 1.0, 0.03, 0.01, 0.2, "down-out", "P")
        got.append((round(mc, 3), round(sh, 3)))
    assert got == [(0.205, 0.207), (0.262, 0.270), (0.383, 0.430), (0.564, 0.735)]
