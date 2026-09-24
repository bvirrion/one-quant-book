"""Numbers gate: every numerical answer printed in Book 4, Chapter 21 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from qm_hf import day, epps, estimators, jumps, mse_by_interval, optimal_interval, signature

S = signature()
E = estimators()
OPT = optimal_interval()


def r(x, d=2):
    return round(float(x), d)


def test_signature_and_noise():
    assert [r(100 * S[s][0], 1) for s in (1, 5, 60, 300)] == [60.1, 35.1, 26.1, 25.4]
    assert r(100 * S[1][1], 1) == 36.8 and all(abs(S[s][2] - 0.25) < 0.012 for s in S)
    assert (r(OPT["noise_sd_bp_est"]), r(OPT["noise_sd_bp_true"])) == (1.75, 1.60)
    assert r(1e4 * 0.01 / 36, 1) == 2.8 and r(1e4 * 0.01 / 36 / math.sqrt(3), 2) == 1.60
    assert r(100 * E["roll"], 2) == 1.14
    assert r(OPT["ratio_1s"], 1) == 5.8 and r(100 * OPT["vol_1s"], 1) == 60.1


def test_optimal_interval():
    assert r(OPT["noise_to_signal"] * 1e4, 2) == 1.24
    assert (round(OPT["n"]), round(OPT["seconds"]), round(OPT["seconds_true"])) == (254, 92, 82)
    m = mse_by_interval()
    assert [r(m[s]) for s in (1, 5, 30, 60, 120, 300, 1800)] == [4.80, 0.98, 0.18, 0.11, 0.12, 0.14, 0.34]
    assert min(m, key=m.get) == 60
    assert r(2 ** (2 / 3)) == 1.59 and round(OPT["seconds"] / 2 ** (2 / 3)) == 58
    assert round(100 * 254 / 23400) == 1


def test_estimators():
    v = {k: r(100 * E[k]["vol"], 1) for k in ("rv300", "tsrv", "rv_opt", "preavg", "kernel", "rv1")}
    assert v == {"rv300": 25.4, "tsrv": 25.2, "rv_opt": 25.8, "preavg": 25.1, "kernel": 25.1, "rv1": 60.1}
    s = {k: r(100 * E[k]["sd_rel"], 1) for k in ("rv300", "tsrv", "rv_opt", "preavg", "kernel")}
    assert s == {"rv300": 14.3, "tsrv": 11.9, "rv_opt": 7.9, "preavg": 7.2, "kernel": 4.8}


def test_epps_and_jumps():
    p = epps()
    assert [r(p["corr"][s]) for s in (1, 10, 60, 300, 1800)] == [0.03, 0.21, 0.49, 0.59, 0.63]
    assert (r(p["hy"], 3), r(p["hy_sd"], 3), r(p["refresh"])) == (0.594, 0.030, 0.48)
    j = jumps()
    assert (r(j["rv"]), r(j["bv"]), r(j["rv_j"]), r(j["bv_j"]), r(j["jump_share"])) == (1.0, 1.0, 1.43, 1.16, 0.29)


def test_ablation():
    """WRITING section 9: remove the mechanism the text credits (bounce and grid) and the signature plot is flat;
    halve the number of simulated days and the optimum stays near a minute."""
    d = day(3, tick=1e-6)
    assert abs(math.sqrt(252 * np.sum(np.diff(d["logtrade"]) ** 2)) - 0.25) < 0.02
    m = mse_by_interval(n_days=30)
    assert min(m, key=m.get) in (60, 120)


def test_exercises():
    assert (r(1e-4 + 2 * 23400 * 4e-8, 5), r(100 * math.sqrt(1e-4 + 2 * 23400 * 4e-8), 1)) == (0.00197, 4.4)
    assert r(2 * math.sqrt(0.0004)) == 0.04
    n = (1e-8 / (4 * 1.6e-15)) ** (1 / 3)
    assert (round(n), round(23400 / n)) == (116, 202)
    iv = (0.25 / math.sqrt(252)) ** 2
    assert (r(iv / 23400 * 1e8), r(-2.56 / (1.06 + 5.12))) == (1.06, -0.41)
    ac = np.mean([np.corrcoef(np.diff(day(k)["logtrade"])[1:], np.diff(day(k)["logtrade"])[:-1])[0, 1] for k in range(10)])
    assert r(ac) == -0.41
    assert r(100 * 0.2 / 15, 1) == 1.3
