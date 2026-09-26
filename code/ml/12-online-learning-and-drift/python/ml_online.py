"""Online learning and drift (One Quant Book 12, chapter 12).

A stream of 20,000 steps whose five coefficients are redrawn at regime ends (exponential durations of mean D steps),
with a signal worth 5% of the variance. Recursive least squares with forgetting factors from 0.95 to 1 against D;
online SGD; three drift detectors (CUSUM, Page-Hinkley, ADWIN) calibrated to one false alarm a year (252 steps) and
timed on streams whose coefficients flip sign once; and four retraining schedules (never, every 250 steps, when a
detector alarms, and recursive least squares) on a stream with regimes of 2,000 steps on average."""
from __future__ import annotations

import functools
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "onlinelearn"))
from firm_onlinelearn import (  # noqa: E402
    ADWIN,
    CUSUM,
    RLS,
    OnlineSGD,
    PageHinkley,
    alarm_times,
    calibrate,
    drift_stream,
    prequential,
    retrain_schedule,
)

R2, N, P = 0.05, 20000, 5
LAMS = (0.95, 0.98, 0.99, 0.995, 0.998, 0.999, 0.9995, 1.0)
DURATIONS = (100, 500, 2000, 10000)
WARM = 1000


def _r2(y, p):
    return float(1 - np.sum((y - p) ** 2) / np.sum(y**2))


@functools.lru_cache(maxsize=8)
def stream(D, seed=1):
    return drift_stream(N, P, float(D), R2, seed)


@functools.lru_cache(maxsize=4)
def forgetting(D, seed=1):
    """Prequential R-squared after a warm-up of 1,000 steps for each forgetting factor, the truth's, and online SGD."""
    s = stream(D, seed)
    X, y = s["X"], s["y"]
    out = {lam: _r2(y[WARM:], prequential(RLS(P, lam), X, y)[WARM:]) for lam in LAMS}
    out["truth"] = _r2(y[WARM:], np.einsum("tp,tp->t", X, s["beta"])[WARM:])
    out["sgd"] = _r2(y[WARM:], prequential(OnlineSGD(P, 0.002), X, y)[WARM:])
    return out


def best_lambda(D, seed=1):
    f = forgetting(D, seed)
    return max(LAMS, key=lambda lam: f[lam])


# ---------------------------------------------------------------------------------------------------- detectors
FLIP, LEN = 2000, 4000


def _gains(seed, flip):
    """The deployed model (least squares on the first 1,000 steps) and its standardised gains prediction x outcome."""
    s = drift_stream(LEN if flip else 40000, P, 1e12, R2, seed, flip_at=FLIP if flip else None)
    X, y = s["X"], s["y"]
    b = np.linalg.lstsq(X[:WARM], y[:WARM], rcond=None)[0]
    g = (X @ b) * y
    g0 = g[:WARM]
    return (g[WARM:] - g0.mean()) / g0.std()


DETECTORS = {
    "CUSUM": (lambda th: CUSUM(0.0, 0.1, th), np.arange(2.0, 40.0, 0.5)),
    "Page-Hinkley": (lambda th: PageHinkley(0.1, th), np.arange(2.0, 60.0, 0.5)),
    "ADWIN": (lambda th: ADWIN(th, 2000), np.array([10.0 ** -e for e in np.arange(1.0, 12.0, 0.5)])),
}


@functools.lru_cache(maxsize=1)
def thresholds(rate=1 / 252):
    null = _gains(100, False)
    return {k: float(calibrate(make, grid, null, rate)) for k, (make, grid) in DETECTORS.items()}


@functools.lru_cache(maxsize=1)
def delays(n_streams=20):
    """Mean and median delay (steps after the flip) to the first alarm, over streams whose coefficients flip at step
    2,000; alarms before the flip counted as false."""
    th = thresholds()
    out = {}
    for name, (make, _) in DETECTORS.items():
        d, false = [], 0
        for sd in range(n_streams):
            g = _gains(200 + sd, True)
            al = alarm_times(lambda make=make, name=name: make(th[name]), g)
            flip = FLIP - WARM
            false += sum(1 for a in al if a < flip)
            after = [a - flip for a in al if a >= flip]
            d.append(after[0] if after else len(g) - flip)
        out[name] = {"mean": float(np.mean(d)), "median": float(np.median(d)), "false": false}
    return out


# ---------------------------------------------------------------------------------------------------- schedules
@functools.lru_cache(maxsize=1)
def schedules(D=2000, seed=3):
    s = drift_stream(N, P, float(D), R2, seed)
    X, y = s["X"], s["y"]
    th = thresholds()
    out = {}
    for name, kw in (("never", {"policy": "never"}), ("every 250 steps", {"policy": "calendar"}),
                     ("on a Page-Hinkley alarm", {"policy": "detector",
                                                  "make_detector": lambda: PageHinkley(0.1, th["Page-Hinkley"])})):
        pred, rt = retrain_schedule(X, y, warm=WARM, **kw)
        out[name] = (_r2(y[WARM:], pred[WARM:]), len(rt))
    lam = best_lambda(D)
    out[f"RLS, lambda {lam}"] = (_r2(y[WARM:], prequential(RLS(P, lam), X, y)[WARM:]), N - WARM)
    out["truth"] = (_r2(y[WARM:], np.einsum("tp,tp->t", X, s["beta"])[WARM:]), 0)
    return out
