"""Numbers gate: every numerical answer printed in Book 5, Chapter 12 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from dv_roughvol import (
    NOISE,
    PUBLISHED_H,
    bergomi_match,
    log_vol_paths,
    pdv_shock,
    rough_kernel,
    roughness_table,
    skew_term,
    variance_curve,
    vix_smile,
    vol_paths,
)
from firm_fwdvar import rbergomi_vix, roughness

CURVE, ROWS = variance_curve()
ST = skew_term()
R = roughness_table()


def test_curve():
    assert [round(100 * r["vs"], 1) for r in ROWS] == [16.3, 18.2, 20.1, 22.1, 23.6]
    assert [round(100 * r["atm"], 1) for r in ROWS] == [14.9, 16.4, 17.8, 19.2, 19.9]
    assert [round(100 * r["fwd_vol"], 1) for r in ROWS] == [16.3, 19.1, 21.8, 24.0, 24.9]
    gaps = [r["vs"] - r["atm"] for r in ROWS]
    assert 0.013 < min(gaps) and max(gaps) < 0.04 and gaps == sorted(gaps)
    assert CURVE.negative_intervals() == []


def test_roughness():
    assert (round(R["rough"], 2), round(R["ou"], 2), round(R["noisy"], 2)) == (0.09, 0.44, 0.17)
    assert round(math.sqrt(2 / 78), 2) == 0.16 and round(NOISE, 2) == 0.08
    hs = list(PUBLISHED_H.values())
    assert len(hs) == 21 and (min(hs), max(hs)) == (0.075, 0.158) and PUBLISHED_H["SPX"] == 0.124


def test_kernels_and_paths():
    assert [round(float(rough_kernel(t)), 2) for t in (1.0, 1 / 12, 1 / 52, 1 / 252)] == [0.85, 2.30, 4.13, 7.76]
    om, k = bergomi_match()
    assert (round(om, 2), round(k, 2)) == (2.51, 1.08)
    b1 = om * math.exp(-k / 252)
    assert round(b1, 2) == 2.50 and round(float(rough_kernel(1 / 252)) / b1, 1) == 3.1
    vp = vol_paths()
    assert round(float(np.mean(np.abs(np.diff(np.log(vp["rough"]))))), 2) == 0.53
    assert round(float(np.mean(np.abs(np.diff(np.log(vp["bergomi"]))))), 2) == 0.06


def test_skews():
    mk, rb, hs = ST["market"], ST["rbergomi"], ST["heston"]
    assert (round(rb[0], 2), round(rb[6], 2)) == (-1.76, -0.32)
    assert (round(mk[0], 2), round(mk[6], 2)) == (-1.44, -0.25)
    assert (round(hs[0], 2), round(hs[6], 2)) == (-0.70, -0.25)
    assert max(abs(hs[i] - mk[i]) for i in range(4, 8)) < 0.04
    assert round(ST["fits"]["market"][1], 2) == -0.44 and round(ST["fits"]["rbergomi"][1], 2) == -0.44
    assert round(ST["short"]["heston"][1], 2) == -0.09
    assert round(mk[0] / mk[6], 1) == 5.7 and round(52 ** 0.44, 1) == 5.7
    assert round(0.5 + ST["fits"]["market"][1], 2) == 0.06 and round(0.5 + ST["fits"]["rbergomi"][1], 2) == 0.06


def test_pdv():
    d, u = pdv_shock(-0.04), pdv_shock(0.04)
    assert round(100 * d[0], 1) == 11.4 and round(100 * d[1], 1) == 22.0 and round(100 * u[1], 1) == 10.6
    half = d[0] + 0.5 * (d[1] - d[0])
    assert int(np.argmax(d[1:] < half)) == 10
    assert round(100 * d[1 + 21], 1) == 13.8 and round(100 * u.max(), 1) == 12.4
    assert round(0.04 / 0.35, 3) == 0.114


def test_vix():
    v = vix_smile()
    assert round(v["vix2"], 4) == 0.0400 and round(100 * v["future"], 2) == 18.74
    assert round(20 - 100 * v["future"], 2) == 1.26
    assert [round(100 * x, 1) for x in v["vols"][[0, 2, 6]]] == [123.1, 123.9, 125.7]
    assert round(100 * rbergomi_vix(0.04, 0.1, 2.5, 1 / 12).mean(), 2) == 17.88


def test_exercises_and_problem():
    assert round(100 * math.sqrt(2 * 0.22 ** 2 - 0.2 ** 2), 1) == 23.8
    assert round(math.log(1.15) / (2 * math.log(2)), 2) == 0.10
    w1, w6 = (ROWS[3]["vs"] + 0.01) ** 2, 0.5 * ROWS[2]["vs"] ** 2
    assert round(100 * math.sqrt((w1 - w6) / 0.5), 1) == 25.8
    est = {k: [] for k in ("rough", "ou", "noisy")}
    for s in range(1, 6):
        for k, x in log_vol_paths(seed=10 * s).items():
            est[k].append(roughness(x))
    assert (round(min(est["ou"]), 2), round(max(est["ou"]), 2)) == (0.45, 0.50)
    assert (round(min(est["noisy"]), 2), round(max(est["noisy"]), 2)) == (0.20, 0.23)
    assert (round(min(est["rough"]), 2), round(max(est["rough"]), 2)) == (0.10, 0.12)
