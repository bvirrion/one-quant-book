"""Numbers gate: every numerical answer printed in Book 7, chapter 2 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "bars"))
from firm_bars import continuous, imbalance_bars, vwap
from rs_marketdata import clocks, day, kurtosis, mid_returns, mixture_kurtosis, realised_variance, wti_summary


def r(x, d=2):
    return round(float(x), d)


TP = day()
C = clocks(TP)


def test_feed():
    k = TP.msgs["kind"]
    assert len(TP.msgs) == 1_555_872 and len(TP.trades) == 55_542 and r(len(TP.msgs) / len(TP.trades), 1) == 28.0
    shares = (r(100 * (k == b"A").mean(), 1), r(100 * (k == b"X").mean(), 1), r(100 * (k == b"E").mean(), 1))
    assert shares == (49.3, 47.2, 3.6)
    assert r(len(TP.msgs) * 36 / 1e6, 1) == 56.0


def test_clocks_and_kurtosis():
    assert {k: len(b) for k, b in C.items()} == {"time": 390, "tick": 391, "volume": 388, "dollar": 388}
    kc = {k: r(kurtosis(b.returns())) for k, b in C.items()}
    assert kc == {"time": 5.47, "tick": 3.58, "volume": 4.04, "dollar": 3.92}
    v = C["time"].volume
    assert r(v.std() / v.mean()) == 0.94 and r(mixture_kurtosis(v)) == 5.67
    assert r(kurtosis(mid_returns(TP, C["time"]))) == 5.44
    counts = np.histogram(C["volume"].end, bins=np.arange(0.0, 23_400.1, 900.0))[0]
    assert (counts.min(), counts.max()) == (2, 42)


def test_signature():
    rv = {w: realised_variance(TP, w) for w in (1, 5, 30, 45, 60, 300)}
    assert (r(rv[1][0]), r(rv[1][1]), r(rv[1][0] / rv[1][1], 1)) == (0.83, 0.23, 3.6)
    assert (r(rv[5][0]), r(rv[5][1]), r(rv[60][0]), r(rv[60][1]), r(rv[300][0]), r(rv[300][1])) == (
        0.58, 0.39, 0.96, 0.93, 0.84, 0.85)
    assert abs(rv[300][0] / rv[300][1] - 1) < 0.02 and abs(rv[30][0] / rv[30][1] - 1) > 0.05
    assert r(rv[45][0]) == 0.95 and r(rv[45][1]) == 0.91 and r(100 * (rv[45][0] / rv[45][1] - 1), 1) == 3.4


def test_wti():
    w = wti_summary()
    assert (w["n_rolls"], w["first_c1"], w["last_c1"]) == (111, 52.69, 86.91)
    assert r(100 * (math.exp(w["raw_return"]) - 1), 0) == 65 and r(100 * (math.exp(w["held_return"]) - 1), 0) == -27
    assert abs(w["ratio_return"] - w["held_return"]) < 1e-9
    assert (r(w["ratio_first"]), r(w["back_first"]), r(w["back_min"]), str(w["back_min_date"])) == (
        118.33, 70.23, -5.89, "2020-04-21")
    assert w["held_min"] == 11.57 and w["c1_min"] == -37.63


def test_exercises():
    assert r(vwap([20.00, 20.02, 19.99], [300, 500, 200]), 3) == 20.008
    extra = 20_000 * (0.01 / 20) ** 2 / 2
    assert r(extra, 4) == 0.0025 and r(100 * math.sqrt(0.0004 + extra)) == 5.39 and r(math.sqrt(0.0029) / 0.02, 1) == 2.7
    assert 40 * 1.5e6 * 5000 * 252 == 7.56e13
    assert r(3 * (1 + 0.8**2)) == 4.92
    out = continuous([70.0, 71.0, 72.0], [73.0, 74.0, 76.0], [False, False, True], days_before=1)
    assert list(out["held"]) == [70.0, 71.0, 76.0] and list(out["back"]) == [73.0, 74.0, 76.0]
    assert r(out["ratio"][0]) == 72.96 and r(100 * (76 / 74 - 1), 1) == 2.7
    tr = TP.trades
    b = imbalance_bars(tr["t"], tr["price"] * 0.01, tr["qty"].astype(float), tr["sign"], expected_n=142)
    assert len(b) == 3472 and r(b.n.mean(), 1) == 16.0 and np.median(b.n) == 7
    assert r(kurtosis(mid_returns(TP, b)), 1) == 35.4 and r(kurtosis(b.returns()), 1) == 24.2
