"""Numbers gate: every numerical answer printed in Book 12, chapter 1 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import ml_why as w  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def pct(x, d=2):
    return round(100 * float(x), d)


def test_table_and_hook():
    c = w.compare()
    assert (pct(c["ceiling_is"]), pct(c["ceiling_oos"])) == (0.72, 0.60)
    got = {k: (pct(c[k]["is"]), pct(c[k]["oos"]), r(c[k]["corr_truth"])) for k in w.FITS}
    assert got == {"ridge": (0.39, 0.38, 0.74), "boosting": (1.45, 0.57, 0.92), "network": (0.64, 0.28, 0.74)}
    shares = {k: round(100 * c[k]["oos"] / c["ceiling_oos"]) for k in w.FITS}
    assert shares == {"ridge": 64, "boosting": 95, "network": 47}
    s = w.strong_signal()
    assert {k: (r(s[k]["is"]), r(s[k]["oos"])) for k in w.FITS} == {"ridge": (0.72, 0.72), "boosting": (0.92, 0.92),
                                                                    "network": (0.94, 0.93)}
    assert round(math.sqrt(c["ceiling_oos"]), 3) == 0.077


def test_months_and_detection():
    c = w.compare()
    b = c["months_oos"]["boosting"]
    assert (pct(b.mean()), pct(b.std(ddof=1)), r(w.detect_months(), 1)) == (0.62, 0.64, 4.3)
    d = b - c["months_oos"]["ridge"]
    assert (pct(d.mean()), pct(d.std(ddof=1)), round(w.months_to_detect(d))) == (0.21, 0.47, 21)
    assert round(100 * (b < 0).mean()) == 18 and round(100 * (c["months_truth"] < 0).mean()) == 19
    assert int((c["months_truth"] < 0).sum()) == 23


def test_effective_sample_and_raw_target():
    rho, neff = w.effective_stocks()
    assert (r(rho), r(neff, 1)) == (0.27, 3.7)
    raw = w.compare(target="raw")
    assert [pct(raw[k]["oos"]) for k in w.FITS] == [-0.29, -0.09, -0.30]
    P = w.stock_panel(1)
    assert (pct(P.r[:240].mean()), pct(P.r[240:].mean()), r(np.mean(P.r**2), 4)) == (-0.56, 0.29, 0.0093)


def test_learning_and_drift():
    lc = {m: (pct(g), pct(rd)) for m, g, rd in w.learning_curve()}
    assert lc[24] == (0.18, 0.29) and lc[48] == (0.29, 0.33) and lc[96] == (0.47, 0.37)
    rows = w.drift_by_year()
    late = [v for d, y, v, _ in rows if d and y >= 6]
    ceil = [cl for d, y, v, cl in rows if d and y >= 6]
    assert (pct(np.mean(late)), pct(np.mean(ceil))) == (0.01, 0.83)


def test_exercises():
    rho = 0.05
    assert (pct(rho**2), pct(rho**2 * (2 * 3 - 9))) == (0.25, -0.75)
    assert (r(500 / (1 + 499 * 0.27), 1), r(500 / (1 + 499 * 0.05), 1)) == (3.7, 19.3)
    assert (r((2 * 0.8 / 0.5) ** 2, 1), r((3 * 0.8 / 0.5) ** 2, 1)) == (10.2, 23.0)
    assert (pct(0.045 / math.sqrt(240)), r(0.56 / 29.05 * 100, 1)) == (0.29, 1.9)
    assert (pct(0.0056**2 / 0.0093), pct(2 * 0.0056 * 0.0029 / 0.0093)) == (0.34, 0.35)
    s = w.strong_signal(snr=0.0101 / 0.9899)
    assert (pct(s["bayes"]), pct(s["ridge"]["oos"]), pct(s["boosting"]["oos"]), pct(s["network"]["oos"])) == (
        1.01, 0.67, 0.42, 0.12)
    assert round(100 * s["boosting"]["is"], 1) == 5.1
    assert round(0.92 * math.sqrt(0.006), 3) == 0.071
