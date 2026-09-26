"""Numbers gate: every numerical answer printed in Book 12, chapter 20 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import ml_regimes as m  # noqa: E402


def test_clustering():
    c = m.clustering()
    r = {k: tuple(round(x, 2) for x in v) for k, v in c.items() if k != "names"}
    assert r[(0.15, 63)] == (0.38, 0.42) and r[(0.15, 252)] == (0.60, 0.75) and r[(0.15, 1260)] == (0.99, 1.0)
    assert r[(0.08, 63)] == (0.06, 0.03) and r[(0.08, 252)] == (0.06, 0.06) and r[(0.08, 1260)] == (0.15, 0.21)
    assert r[(0.15, "stability")] == (0.32, 0.35) and r[(0.08, "stability")] == (0.08, 0.06)
    assert c["names"] == {0.08: 168, 0.15: 160}


def test_hmm_fit():
    h = m.hmm(2)
    assert (round(100 * h.sd[0], 2), round(100 * h.sd[1], 2), round(h.P[0, 0], 3), round(h.P[1, 1], 3)) == (0.80, 2.60,
                                                                                                            0.988, 0.958)
    t = m.three_state()
    assert round(t["loglik 3"] - t["loglik 2"], 1) == 5.7 and round(0.5 * 6 * math.log(2520), 1) == 23.5
    assert (round(100 * t["sd 3"][1], 2), round(100 * t["sd 3"][2], 2)) == (2.28, 2.65)
    assert (round(1 / (1 - h.P[0, 0]), 1), round(1 / (1 - h.P[1, 1]), 1), round(h.P[0, 1] / (h.P[0, 1] + h.P[1, 0]), 3)) == (
        82.2, 23.9, 0.225)


def test_regimes():
    r = m.regimes()
    got = {k: (round(100 * r[k]["accuracy"], 1), r[k]["median delay"], round(r[k]["mean delay"], 1), r[k]["missed"])
           for k in ("filtered", "smoothed", "Viterbi", "volatility threshold")}
    assert got == {"filtered": (95.9, 1.0, 1.5, 1), "smoothed": (97.7, 0.0, 0.8, 1), "Viterbi": (97.5, 0.0, 0.9, 4),
                   "volatility threshold": (89.8, 1.0, 3.8, 5)}
    b = {k: round(v, 3) for k, v in r["P(stress) day before"].items()}
    assert b == {"filtered": 0.032, "smoothed": 0.353, "filtered, calm days": 0.041, "smoothed, calm days": 0.019}
    assert round(r["stress share"], 3) == 0.215 and r["filtered"]["switches"] == 20
    v = {k: round(x, 2) for k, x in m.vol_targeting().items()}
    assert v == {"filtered, predicted": 1.0, "smoothed, same day": 1.21, "buy and hold": 0.91}
    t = m.test_loglik()
    assert (round(t[2], 1), round(t[3], 1), round(t[2] - t[3], 1)) == (7866.6, 7864.4, 2.2)


def test_anomalies():
    a = m.anomalies()
    got = {k: (round(v["tpr"], 2), round(v["precision"], 2)) for k, v in a.items() if k != "counts"}
    assert got == {"order-to-trade": (0.0, 0.0), "fill-rate gap": (0.37, 0.24), "cancel after fill": (0.51, 0.31),
                   "gap x cancel": (0.77, 0.40), "isolation forest": (1.0, 0.47), "autoencoder": (0.32, 0.22)}
    assert a["counts"] == (100, 11500) and round(100 / (100 + 115), 2) == 0.47


def test_exercises():
    assert (math.sqrt(2 * (1 - 0.5)), round(math.sqrt(2), 2)) == (1.0, 1.41)
