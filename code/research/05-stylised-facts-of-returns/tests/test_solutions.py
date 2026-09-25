"""Numbers gate: every numerical answer printed in Book 7, chapter 5 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "synthmkt"))
from firm_synthmkt import MarketConfig, simulate
from rs_stylised import (
    acf,
    aggregated_kurtosis,
    correlation_asymmetry,
    eigen,
    french_summary,
    french_table,
    intraday_profile,
    market,
    synth_series,
)

F = french_summary()
S = synth_series()


def r(x, d=2):
    return round(float(x), d)


def test_french_facts():
    assert F["n"] == 26296 and r(F["kurtosis"], 1) == 19.1 and r(F["hill_left_k500"]) == 2.90
    assert r(F["hill_right_k500"]) == 2.58 and F["days_beyond_5sd"] == 103 and r(F["normal_beyond_5sd"], 3) == 0.015
    assert r(F["r_19871019_pct"]) == -17.44 and r(-F["sigmas_1987"], 1) == 22.0 and r(F["sd_prior5y_pct"]) == 0.79
    assert (r(F["acf_abs_1"]), r(F["acf_abs_20"]), r(F["acf_abs_100"]), r(F["acf_r_1"], 3)) == (0.30, 0.22, 0.13, 0.046)
    assert r(F["max_pct"], 1) == 15.7 and F["max_date"] == 19330315 and r(F["skewness"]) == -0.16
    g = french_table("agg")
    assert [r(k, 1) for k in g["kurtosis"][:5]] == [20.0, 11.5, 10.2, 9.5, 7.3]
    assert (r(g["skewness"][1]), r(g["skewness"][3])) == (-0.76, -0.90)
    a = french_table("acf")
    assert (r(a["sq"][0]), r(a["sq"][19]), r(a["sq"][99])) == (0.26, 0.11, 0.04)
    lev = french_table("lev")
    assert r(lev["corr"][lev["lag"] == 1][0], 3) == -0.085 and r(lev["corr"][lev["lag"] == -1][0], 3) == 0.025
    asym = french_table("asym")
    i = list(asym["threshold"]).index(1.0)
    assert (r(asym["down"][i]), r(asym["up"][i])) == (0.61, 0.56) and (asym["down"] > asym["up"]).all()


def test_scorecard():
    m, e, st = S["market"], S["ew"], S["stock_median"]
    assert [r(m[k], 1) for k in ("kurtosis",)] == [20.5] and r(e["kurtosis"], 1) == 18.0 and r(st["kurtosis"], 1) == 8.7
    assert (r(m["hill_left"]), r(e["hill_left"]), r(st["hill_left"])) == (2.83, 2.88, 3.35)
    assert (r(m["acf_abs_1"]), r(e["acf_abs_1"]), r(st["acf_abs_1"])) == (0.23, 0.25, 0.11)
    assert (r(m["acf_abs_20"]), r(e["acf_abs_20"]), r(st["acf_abs_20"])) == (0.21, 0.22, 0.08)
    assert (r(m["acf_abs_100"]), r(e["acf_abs_100"]), r(st["acf_abs_100"])) == (-0.02, -0.03, -0.01)
    assert (r(m["acf_r_1"]), r(e["acf_r_1"]), r(st["acf_r_1"])) == (-0.01, 0.01, -0.03)
    assert (r(m["leverage_1"], 3), r(e["leverage_1"], 3), r(st["leverage_1"], 3)) == (-0.111, -0.103, -0.024)
    assert (r(m["kurtosis_21"], 1), r(e["kurtosis_21"], 1), r(st["kurtosis_21"], 1)) == (3.8, 3.9, 3.5)
    k = aggregated_kurtosis(market().mkt, (1, 21))
    assert (r(k[0], 1), r(k[1], 1)) == (18.3, 3.8)


def test_cross_section_and_intraday():
    down, up, _ = correlation_asymmetry(1.0)
    assert (r(down), r(up)) == (0.20, 0.25)
    ev, hi, shape = eigen()
    assert shape == (252, 200) and r(ev[0], 1) == 44.5 and round(100 * ev[0] / ev.sum()) == 22 and r(hi) == 3.58
    assert int((ev > hi).sum()) == 4
    v = intraday_profile()
    assert (r(v[0] / np.median(v), 1), r(v[-1] / np.median(v), 1)) == (2.6, 1.7)
    m = market().mkt
    assert r(acf(np.abs(m), 50), 2) == 0.13 and r(acf(np.abs(m), 70), 2) == 0.01


def test_exercises():
    z = 17.4 / 1.08
    assert r(z, 1) == 16.1 or r(17.44 / 1.07735, 1) == 16.2
    p = 0.5 * math.erfc(16.2 / math.sqrt(2))
    assert 1e-59 < p < 1e-58 and 26296 * p < 1e-53
    assert (r(3 + 17 / 5, 1), r(3 + 17 / 21, 1), r(3 + 17 / 63, 1)) == (6.4, 3.8, 3.3)
    assert 1000 * 2**3 == 8000 and 1000 * 2**4 == 16000 and 4 + 6 / 16 == 4.375
    assert (r(math.sqrt(0.1 + 0.9 * 0.61), 3), r(math.sqrt(0.1 + 0.9 * 0.56), 3)) == (0.806, 0.777)
    assert r(math.log(0.5) / math.log(0.99), 0) == 69 and r(0.02 + 0.05 + 0.92) == 0.99
    q = simulate(MarketConfig(garch_alpha=0.01, garch_gamma=0.05, garch_beta=0.965))
    assert (r(acf(np.abs(q.mkt), 20)), r(acf(np.abs(q.mkt), 100))) == (0.37, 0.26)
    assert r(100 * q.mkt.std() * math.sqrt(252), 1) == 7.7
    assert (r(100 * math.sqrt(q.h.min() * 252), 1), r(100 * math.sqrt(q.h.max() * 252), 1)) == (1.7, 23.6)
