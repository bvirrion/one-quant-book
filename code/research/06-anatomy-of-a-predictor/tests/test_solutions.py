"""Numbers gate: every numerical answer printed in Book 7, chapter 6 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "predictor"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "synthmkt"))
from firm_predictor import ic_series, ic_summary
from firm_synthmkt import MarketConfig, simulate
from rs_anatomy import BURN, card, horizon_ics, lag_profile, neutralisation, panel, study


def r(x, d=4):
    return round(float(x), d)


def test_horizons():
    h = horizon_ics()
    assert (r(h[(1, 1)][0]), r(h[(1, 1)][1], 1)) == (0.0385, 17.8)
    assert (r(h[(5, 5)][0]), r(h[(5, 5)][1], 1)) == (0.0074, 2.4)
    assert (r(h[(1, 5)][0]), r(h[(5, 1)][0])) == (0.0162, 0.0187)
    lp = lag_profile(range(1, 3))
    assert (r(lp[1]), r(lp[2])) == (0.0385, 0.0008)


def test_study():
    s = study()
    assert r(s["raw"]["mean"]) == r(s["excess"]["mean"]) == 0.0074
    assert r(s["residual"]["mean"]) == 0.0064 and round(s["share_residual_var"], 1) == 0.9
    assert (r(s["raw"]["t_naive"], 2), r(s["raw"]["t_hac"], 2)) == (3.85, 2.39)
    assert r(s["residual_every_h"]["t_naive"], 2) == 1.31


def test_strong_industries():
    nz = neutralisation(simulate(MarketConfig(ind_vol=0.30)))
    assert r(nz["share"], 3) == 0.476 and round(100 * (1 - nz["share"])) == 52 and r(1 / math.sqrt(nz["share"]), 2) == 1.45
    assert (r(nz["raw"]["mean"]), r(nz["residual"]["mean"]), r(nz["neutral"]["mean"])) == (0.0043, 0.0067, 0.0086)
    assert (r(nz["raw"]["t_hac"], 1), r(nz["residual"]["t_hac"], 1), r(nz["neutral"]["t_hac"], 1)) == (0.8, 3.5, 3.5)


def test_card():
    c = card()
    assert (r(c.stats["ic"], 3), r(c.stats["icir_annual"], 1), r(c.stats["t"], 1)) == (0.040, 6.4, 20.1)
    assert c.half_life < 1.0


def test_exercises():
    assert r(1 / math.sqrt(799)) == 0.0354 and round((2 / math.sqrt(799) / 0.01) ** 2) == 50
    assert r(0.012 / 0.08 * math.sqrt(252), 2) == 2.38 and r(0.03 / math.sqrt(0.6), 3) == 0.039
    assert (r(math.sqrt(20), 2), r(6 / math.sqrt(20), 2)) == (4.47, 1.34) and r(14 / math.sqrt(60), 1) == 1.8
    assert r(1 / math.sqrt(999), 3) == 0.032 and round((2 / (0.02 * 31.6)) ** 2) == 10
    p = panel()
    ret = np.where(p.listed, p.ret, np.nan)
    ic = ic_series(-ret[BURN:-1], ret[BURN + 1:], "rank")
    m = np.abs(p.mkt[BURN:-1])
    hi = m >= np.quantile(m, 0.9)
    a, b = ic_summary(ic[hi]), ic_summary(ic[~hi])
    assert (r(a["mean"], 3), r(a["t_hac"], 1), r(b["mean"], 3), r(b["t_hac"], 1)) == (0.037, 5.0, 0.039, 17.1)
