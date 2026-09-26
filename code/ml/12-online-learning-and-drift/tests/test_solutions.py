"""Numbers gate: every numerical answer printed in Book 12, chapter 12 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import ml_online as m  # noqa: E402
from firm_onlinelearn import drift_stream  # noqa: E402


def pct(v, d=2):
    return round(100 * v, d)


def test_forgetting():
    got = {}
    for D in m.DURATIONS:
        f = m.forgetting(D)
        lam = m.best_lambda(D)
        got[D] = (lam, pct(f[lam]), pct(f["truth"]), pct(f["sgd"]))
    assert got == {100: (0.995, 0.75, 4.91, 0.57), 500: (0.995, 2.44, 4.93, 2.05),
                   2000: (0.998, 3.71, 5.37, 3.69), 10000: (1.0, 5.21, 5.29, 4.84)}
    assert pct(m.forgetting(10000)[0.9995]) == 5.16
    truths = [pct(m.forgetting(D)["truth"], 1) for D in m.DURATIONS]
    assert (min(truths), max(truths)) == (4.9, 5.4)


def test_thresholds_and_delays():
    th = m.thresholds()
    assert (th["CUSUM"], th["Page-Hinkley"], round(th["ADWIN"], 4)) == (9.0, 9.0, 0.0032)
    d = m.delays()
    got = {k: (round(v["mean"], 1), v["median"], v["false"]) for k, v in d.items()}
    assert got == {"CUSUM": (20.8, 17.0, 74), "Page-Hinkley": (27.4, 18.5, 78), "ADWIN": (42.5, 26.5, 91)}
    assert round(20 * 1000 / 252, 1) == 79.4
    g = m._gains(200, True)
    assert round(float(g[m.FLIP - m.WARM:].mean()), 2) == -0.38


def test_exercise_arithmetic():
    assert [round(1 / (1 - lam)) for lam in (0.99, 0.998, 0.9995)] == [100, 500, 2000]
    assert (round(0.99**500, 4), round(0.998**500, 2), round(0.9995**500, 2)) == (0.0066, 0.37, 0.78)
    assert round(9 / (0.38 - 0.1)) == 32


def test_schedules():
    s = {k: (pct(v[0]), v[1]) for k, v in m.schedules().items()}
    assert s == {"never": (-7.81, 0), "every 250 steps": (2.62, 75), "on a Page-Hinkley alarm": (-2.67, 2),
                 "RLS, lambda 0.998": (3.24, 19000), "truth": (4.62, 0)}
    changes = drift_stream(m.N, m.P, 2000.0, m.R2, 3)["changes"]
    assert sum(1 for c in changes if c >= m.WARM) == 10


def test_schedules_short_regimes():
    s = {k: (pct(v[0]), v[1]) for k, v in m.schedules.__wrapped__(D=500).items()}
    assert s == {"never": (-3.68, 0), "every 250 steps": (-0.60, 75), "on a Page-Hinkley alarm": (-8.24, 45),
                 "RLS, lambda 0.995": (2.24, 19000), "truth": (5.35, 0)}
