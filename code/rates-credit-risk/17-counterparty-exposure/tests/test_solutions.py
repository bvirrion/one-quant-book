"""Numbers gate: every numerical answer printed in Book 6, chapter 17 (text and solutions)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_exposure as m

PS = m.profile_set()
S = {k: v[1] for k, v in PS.items()}
T = m.scenarios().times[:-1]
W = m.wrong_way()
C = {c: m.corporate(c) for c in ("none", "zero", "th5")}


def mn(x, d=2):
    return round(x / 1e6, d)


def test_text():
    usd, eur, usd5 = m.par_rates()
    assert (round(100 * usd, 2), round(100 * eur, 2)) == (3.80, 2.59)
    assert mn(S["swap"]["peak_ee"]) == 3.13 and round(T[int(PS["swap"][0]["ee"].argmax())]) == 3
    assert mn(S["swap"]["peak_pfe"]) == 18.26 and round(S["swap"]["t_peak_pfe"], 1) == 3.9
    assert mn(S["xccy"]["peak_ee"]) == 7.09 and mn(S["xccy"]["peak_pfe"]) == 39.93
    net = PS["net"][0]["ee"]
    k = int(net.argmax())
    tot = PS["swap"][0]["ee"][k] + PS["xccy"][0]["ee"][k]
    assert mn(net[k]) == 7.77 and round(T[k], 1) == 3.9 and mn(tot) == 9.24 and round(1 - net[k] / tot, 2) == 0.16
    assert round(PS["net"][0]["ene"].min() / 1e6, 1) == -21.0
    assert (mn(S["csa10"]["peak_ee"]), mn(S["csa10"]["peak_pfe"])) == (1.30, 6.45)
    assert (mn(S["net"]["epe_life"]), mn(S["csa10"]["epe_life"])) == (6.44, 0.95)
    assert round(S["csa10"]["epe_life"] / S["net"]["epe_life"], 2) == 0.15
    assert mn(S["csa20"]["peak_ee"]) == 1.83 and mn(S["csa_th"]["peak_ee"]) == 3.81
    assert round(1.1 ** -5, 2) == 0.62 and round(0.9 ** -5 - 1, 1) == 0.7
    assert (round(W["ratio_peak"], 2), round(W["ratio_avg"], 2)) == (2.52, 2.22)


def test_exercises():
    assert round(S["csa20"]["peak_ee"] / S["csa10"]["peak_ee"], 2) == 1.41
    assert round(np.sqrt(2), 3) == 1.414


def test_problem():
    n, z, t5 = C["none"], C["zero"], C["th5"]
    assert round(100 * n["k_swap"], 2) == 3.48 and round(n["k_fx"], 4) == 1.1166
    assert mn(n["peak_pfe"]) == 4.42 and round(n["t_peak_pfe"], 2) == 0.96
    assert (round(n["epe_1y"]), round(n["epe_life"])) == (626_224, 545_826)
    assert mn(z["peak_pfe"]) == 3.63 and z["t_peak_pfe"] == 1.0
    assert (round(z["epe_1y"]), round(z["epe_life"])) == (199_002, 97_606)
    assert mn(t5["peak_pfe"]) == 4.38 and round(t5["epe_life"]) == 544_793
    assert round(20e6 * 0.11 / 1e6, 1) == 2.2
