"""Numbers gate: every numerical answer printed in Book 5, Chapter 13 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from dv_jumps import (
    EVENT,
    Merton,
    black,
    event_hedge,
    event_hedge_uncertain,
    event_smile,
    event_summary,
    fit_bates,
    fit_event,
    fit_models,
    hedge_experiment,
    market_event_smile,
    moments_table,
    otm_put_decay,
    skew_terms,
)

FITS = fit_models()
M = FITS["merton"][0]
BATES, BATES_RMSE = fit_bates()
ST = skew_terms(FITS, BATES)
EH, EU = event_hedge(), event_hedge_uncertain()
MK = market_event_smile()


def test_short_expiries():
    od = otm_put_decay(M)
    assert round(od["limit"], 2) == 1.00 and round(od["jump"][0] / od["t"][0], 2) == 1.02
    vol = math.sqrt(M.cumulants(1.0)[0])
    assert round(100 * vol, 1) == 16.4
    p1, p5 = black(100.0, 90.0, 1 / 365, 1.0, vol, "P"), black(100.0, 90.0, 5 / 365, 1.0, vol, "P")
    assert f"{p1:.0e}" == "3e-36" and f"{p5:.0e}" == "6e-09"


def test_fits():
    m, k, v = FITS["merton"], FITS["kou"], FITS["vg"]
    assert (round(100 * m[0].sigma, 1), round(m[0].lam, 2), round(100 * m[0].mu, 1), round(100 * m[0].delta, 1),
            round(100 * m[2], 2)) == (9.8, 3.16, -5.8, 4.6, 0.18)
    ko = k[0]
    assert (round(100 * ko.sigma, 1), round(ko.lam, 1), round(ko.p, 2), round(ko.eta1), round(ko.eta2, 1),
            round(100 * k[2], 2)) == (8.4, 11.7, 0.24, 85, 30.4, 0.06)
    assert round(100 * v[2], 2) == 0.24
    b = BATES
    assert (round(b.v0, 3), round(b.kappa, 2), round(b.vbar, 3), round(b.eta, 2), round(b.rho, 2), round(b.lam, 2),
            round(100 * b.mu, 1), round(100 * b.delta, 1), round(100 * BATES_RMSE, 2)) == (
        0.018, 2.06, 0.062, 0.85, -0.70, 2.34, -3.6, 3.0, 0.34)


def test_skews():
    assert (round(ST["market"][0], 2), round(ST["market"][6], 2)) == (-1.44, -0.25)
    assert round(ST["merton"][6], 2) == -0.07 and round(ST["vg"][0], 2) == -3.66
    assert (round(ST["bates"][0], 2), round(ST["bates"][6], 2)) == (-1.36, -0.23)


def test_moments():
    tab = moments_table(M, (1 / 52, 1 / 12, 1.0))
    assert [round(s, 2) for _, s, _ in tab] == [-2.90, -1.39, -0.40]
    assert [round(k, 1) for _, _, k in tab] == [15.2, 3.5, 0.3] and round(tab[2][2], 2) == 0.29
    tv = moments_table(FITS["vg"][0], (1 / 52, 1 / 12, 1.0))
    assert all(abs(a[1] / b[1] - 1) < 0.05 for a, b in zip(tab, tv, strict=True))


def test_hedging():
    he = hedge_experiment(M)
    assert round(he["premium"], 2) == 1.89 and abs(np.mean(he["merton"])) < 0.02
    assert (round(float(np.std(he["merton"])), 2), round(float(np.percentile(he["merton"], 1)), 1)) == (0.97, -4.1)
    diff = he["diffusion"]
    assert (round(float(np.std(diff)), 3), round(float(np.percentile(diff, 1)), 2)) == (0.185, -0.50)
    m2 = Merton(M.sigma, 2 * M.lam, M.mu / 2, M.delta / 2)
    h2 = hedge_experiment(m2)
    assert (round(float(np.std(h2["merton"])), 2), round(float(np.percentile(h2["merton"], 1)), 1)) == (0.55, -2.1)
    assert round(100 * math.sqrt(m2.cumulants(1.0)[0]), 1) == 13.5 and round(h2["premium"], 2) == 1.55


def test_event():
    s = event_summary()
    assert (round(100 * s["atm"], 1), round(100 * s["up"], 1), round(100 * s["down"], 1)) == (160.4, 22.1, -14.8)
    assert round(s["straddle"], 2) == 8.86
    move = s["implied_move"]
    assert (round(100 * move, 1), round(100 * move * math.sqrt(2 / math.pi), 1)) == (21.7, 17.3)
    assert round(100 * s["true_move_sd"], 1) == 17.6
    assert round(100 * (EVENT.p * EVENT.a + (1 - EVENT.p) * abs(EVENT.b)), 1) == 17.6
    assert round(s["atm"] ** 2 / 52 - 0.35 ** 2 / 52, 3) == 0.047
    assert round(100 * event_smile().max()) == 162
    p = {k: v[2] for k, v in EH["pnl"].items()}
    assert (round(p["none"], 2), round(p["model"], 2), round(p["black"], 2)) == (1.81, 2.01, 1.01)
    assert (round(100 * p["none"] / EH["premium"], 1), round(100 * p["black"] / EH["premium"], 1)) == (20.4, 11.4)
    assert p["minvar"] < 1e-10
    d = EH["deltas"]
    assert (round(d["model"], 2), round(d["black"], 2), round(d["minvar"], 2)) == (-0.02, 0.09, 0.20)
    assert (round(EU["ratio"], 2), round(EU["sd"], 2), round(100 * EU["sd_rel"], 1)) == (0.20, 1.45, 16.5)
    dv = EH["dv"]
    assert (round(dv[0], 2), round(dv[1], 2)) == (2.21, -1.48)


def test_problem_and_exercises():
    assert (round(100 * MK[6], 1), round(100 * MK[0], 1), round(100 * MK[12], 1)) == (159.5, 79.3, 116.4)
    ev = MK[6] ** 2 / 52 - 0.35 ** 2 / 52
    assert (round(ev, 4), round(100 * math.sqrt(ev), 1), round(100 * math.sqrt(ev * 2 / math.pi), 1)) == (
        0.0465, 21.6, 17.2)
    m, rmse = fit_event(MK)
    assert (round(100 * m.sigma, 1), round(m.p, 3), round(m.a, 3), round(100 * rmse, 2)) == (40.6, 0.399, 0.199, 0.07)
    assert (round(100 * (math.exp(m.a) - 1), 1), round(100 * (math.exp(m.b) - 1), 1)) == (22.1, -14.7)
    assert round(100 * ((1 - 0.4 * 1.2214) / 0.6 - 1), 1) == -14.8
    assert (round(100 * (1 - math.exp(-3 / 52)), 1), round(100 * (1 - math.exp(-3)), 1)) == (5.6, 95.0)
    assert (round(-0.4 * math.sqrt(52), 2), round(-0.4 / 2, 2)) == (-2.88, -0.20)
    assert round((2.21 + 1.48) / (50 * (0.221 + 0.148)), 2) == 0.20
