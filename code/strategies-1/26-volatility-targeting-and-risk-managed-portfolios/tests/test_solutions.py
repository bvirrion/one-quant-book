"""Numbers gate: every numerical answer printed in Book 8, chapter 26 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s1_voltarget import classes, seeds, spike, summary  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def test_seeds():
    m = summary()
    assert [r(x) for x in m["mean"]] == [0.49, 0.52, 0.48] and (m["better_vol"], m["better_var"]) == (10, 8)
    assert (r(m["gain_vol"], 3), r(m["gain_sd"]), [r(x, 2) for x in m["dd"]]) == (0.028, 0.22, [2.7, 2.58, 2.67])
    a = np.array([x for x, _ in seeds()])
    assert (r(a[:, 0].min()), r(a[:, 0].max()), r(a[:, 0].std(ddof=1))) == (-0.44, 1.18, 0.49)


def test_classes():
    c = {k: tuple(r(x) for x in v) for k, v in classes().items()}
    assert c == {"equity": (0.19, 0.19, 5.68, 6.04), "bond": (0.35, 0.28, 6.19, 4.99),
                 "currency": (-0.18, -0.08, 13.28, 11.45), "commodity": (-0.21, -0.25, 8.3, 9.42)}


def test_spike():
    got = {i: (r(100 * spike(i)["next_day"], 1), r(100 * spike(i)["twenty"], 1), r(100 * spike(i)["ret"], 1))
           for i in (0.0, 0.1, 0.3)}
    assert got == {0.0: (-14.5, -20.5, -16.6), 0.1: (-14.9, -20.6, -18.7), 0.3: (-12.8, -17.8, -22.0)}
    e = spike(0.0)["exposure"]
    assert (r(e[0]), r(e[1])) == (0.73, 0.25)


def test_exercises():
    assert (r(0.10 / 0.12, 2), r(0.10 / 0.40, 2)) == (0.83, 0.25)
    assert r(0.002 * (0.73 - 0.41) / 0.004 * 100, 0) == 16
    assert r(0.06 / 0.16, 3) == 0.375 and r(1 / math.sqrt(10), 2) == 0.32 and r(0.22 / math.sqrt(20), 3) == 0.049


def test_self_generated_volatility():
    from firm_voltarget import spike_flows
    from s1_voltarget import base_path
    b = base_path()
    o, p = spike_flows(b, 0.005, 0.004, 0.3, 0.10, 20.0, 2.0), spike_flows(b, 0.005, 0.004, 0.0, 0.10, 20.0, 2.0)
    assert (r(o["exposure"][249]), r(p["exposure"][249])) == (0.46, 0.73)
    assert (r(100 * np.std(o["r"][:250]) * math.sqrt(252), 1), r(100 * np.std(p["r"][:250]) * math.sqrt(252), 1)) == (18.7, 13.0)
    assert r(100 * np.abs(o["flow"][21:250]).mean(), 1) == 1.9
