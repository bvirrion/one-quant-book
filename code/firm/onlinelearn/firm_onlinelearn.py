"""firm.onlinelearn -- online estimators, drift detectors and retraining schedules (Book 12, chapter 12).

Models that learn as data arrive (recursive least squares with a forgetting factor, online stochastic gradient descent),
detectors that say when what they learned has stopped being true (CUSUM, Page-Hinkley, a windowed ADWIN), thresholds
calibrated to a false-alarm rate on a stream with no change, and a synthetic stream whose coefficients switch between
regimes, to test them against a known truth. Everything is prequential: each step predicts, then learns.

API (stable):
    drift_stream(n, p, mean_regime, r2, seed, flip_at) -> dict(X, y, beta, changes)
                                 y_t = beta_t . x_t + noise; beta redrawn at exponential regime ends (mean mean_regime)
                                 or flipped in sign once at flip_at; signal share of variance r2
    RLS(p, lam, delta)           .predict(x), .update(x, y); forgetting factor lam (1 = ordinary least squares)
    OnlineSGD(p, lr)             .predict(x), .update(x, y)
    prequential(model, X, y) -> predictions made before each update
    CUSUM(k, h), PageHinkley(delta, lam), ADWIN(delta, max_window)   .update(value) -> True on an alarm (then reset)
    alarm_times(make_detector, values) -> list of alarm steps (the detector restarted after each)
    calibrate(make_for_threshold, thresholds, null_values, rate) -> the smallest threshold whose false-alarm rate on
                                 null_values is at most `rate` alarms per step
    retrain_schedule(X, y, policy, **kw) -> (predictions, retrain steps)   policies 'never', 'calendar', 'detector'
"""
from __future__ import annotations

import math

import numpy as np


def drift_stream(n=20000, p=5, mean_regime=500.0, r2=0.02, seed=0, flip_at=None):
    rng = np.random.default_rng(seed)
    X = rng.standard_normal((n, p))
    beta = np.empty((n, p))
    changes = []
    b = rng.standard_normal(p)
    nxt = rng.exponential(mean_regime) if flip_at is None else np.inf
    for t in range(n):
        if flip_at is not None and t == flip_at:
            b = -b
            changes.append(t)
        elif t >= nxt:
            b = rng.standard_normal(p)
            changes.append(t)
            nxt = t + rng.exponential(mean_regime)
        beta[t] = b
    f = np.einsum("tp,tp->t", X, beta)
    f *= math.sqrt(r2 / (1 - r2)) / f.std()                             # signal variance r2 / (1 - r2) of unit noise
    beta *= math.sqrt(r2 / (1 - r2)) / np.einsum("tp,tp->t", X, beta).std()
    y = f + rng.standard_normal(n)
    return {"X": X, "y": y, "beta": beta, "changes": changes}


class RLS:
    """Minimises sum_s lam^(t-s) (y_s - x_s' b)^2; the effective memory is about 1 / (1 - lam) observations."""

    def __init__(self, p, lam=0.99, delta=100.0):
        self.b = np.zeros(p)
        self.P = delta * np.eye(p)
        self.lam = lam

    def predict(self, x):
        return float(x @ self.b)

    def update(self, x, y):
        Px = self.P @ x
        k = Px / (self.lam + x @ Px)
        self.b = self.b + k * (y - x @ self.b)
        P = (self.P - np.outer(k, Px)) / self.lam
        self.P = 0.5 * (P + P.T)                                         # keep P symmetric: rounding breaks it


class OnlineSGD:
    def __init__(self, p, lr=0.001):
        self.b = np.zeros(p)
        self.lr = lr

    def predict(self, x):
        return float(x @ self.b)

    def update(self, x, y):
        self.b += self.lr * (y - x @ self.b) * x


def prequential(model, X, y):
    out = np.empty(len(y))
    for t in range(len(y)):
        out[t] = model.predict(X[t])
        model.update(X[t], y[t])
    return out


class CUSUM:
    """One-sided CUSUM for a fall in the mean of a monitored value from its reference mu0."""

    def __init__(self, mu0=0.0, k=0.0, h=5.0):
        self.mu0, self.k, self.h, self.s = mu0, k, h, 0.0

    def update(self, v):
        self.s = max(0.0, self.s + (self.mu0 - v - self.k))
        if self.s > self.h:
            self.s = 0.0
            return True
        return False


class PageHinkley:
    """Page-Hinkley test for a fall in the mean: cumulate the deviations below the running mean (less a tolerance
    delta) and alarm when the cumulated sum rises lam above its running minimum."""

    def __init__(self, delta=0.0, lam=10.0):
        self.delta, self.lam = delta, lam
        self.reset()

    def reset(self):
        self.n, self.mean, self.m, self.mmin = 0, 0.0, 0.0, 0.0

    def update(self, v):
        self.n += 1
        self.mean += (v - self.mean) / self.n
        self.m += self.mean - v - self.delta
        self.mmin = min(self.mmin, self.m)
        if self.m - self.mmin > self.lam:
            self.reset()
            return True
        return False


class ADWIN:
    """Adaptive windowing (after Bifet and Gavalda): keep a window of recent values; drop its older part whenever some
    split into an older and a newer sub-window has means differing by more than a Hoeffding-type bound. Windowed
    O(window) version: splits are checked every `check` steps."""

    def __init__(self, delta=0.002, max_window=2000, check=5, min_side=30):
        self.delta, self.max_window, self.check, self.min_side = delta, max_window, check, min_side
        self.w: list[float] = []
        self.t = 0

    def update(self, v):
        self.w.append(v)
        if len(self.w) > self.max_window:
            self.w.pop(0)
        self.t += 1
        if self.t % self.check or len(self.w) < 2 * self.min_side:
            return False
        a = np.asarray(self.w)
        n = len(a)
        c = np.cumsum(a)
        i = np.arange(self.min_side, n - self.min_side)
        m0, m1 = c[i - 1] / i, (c[-1] - c[i - 1]) / (n - i)
        hm = 1.0 / (1.0 / i + 1.0 / (n - i))
        eps = np.sqrt(np.log(4 * n / self.delta) / (2 * hm)) * a.std()
        hit = np.abs(m0 - m1) > eps
        if hit.any():
            cut = int(i[np.flatnonzero(hit)[-1]])
            self.w = self.w[cut:]
            return True
        return False


def alarm_times(make, values):
    d = make()
    out = []
    for t, v in enumerate(values):
        if d.update(v):
            out.append(t)
    return out


def calibrate(make_for, thresholds, null_values, rate):
    """make_for(threshold) -> a detector. The smallest threshold (in the order given, increasing) with at most
    `rate` alarms per step on the no-change values."""
    for th in thresholds:
        if len(alarm_times(lambda th=th: make_for(th), null_values)) / len(null_values) <= rate:
            return th
    return thresholds[-1]


def retrain_schedule(X, y, policy="calendar", every=250, window=500, warm=1000, make_detector=None, min_fit=100):
    """Batch least squares refitted on the last `window` observations: never after the warm-up ('never'), every
    `every` steps ('calendar'), or when a detector fed with the model's gains (prediction x outcome, standardised on
    the warm-up) alarms ('detector', refitted on the data since the alarm once min_fit observations exist)."""
    def fit(a, b):
        return np.linalg.lstsq(X[a:b], y[a:b], rcond=None)[0]

    beta = fit(0, warm)
    pred = np.full(len(y), np.nan)
    retrains = []
    det = make_detector() if make_detector else None
    since = None
    scale = None
    for t in range(warm, len(y)):
        pred[t] = X[t] @ beta
        if policy == "calendar" and (t - warm) % every == 0 and t > warm:
            beta = fit(max(0, t - window), t)
            retrains.append(t)
        elif policy == "detector":
            g = pred[t] * y[t]
            if scale is None:
                gw = np.einsum("tp,p->t", X[:warm], beta) * y[:warm]
                scale = (gw.mean(), gw.std())
            if det.update((g - scale[0]) / scale[1]):
                since = t
            if since is not None and t - since >= min_fit:
                beta = fit(since, t)
                retrains.append(t)
                since = None
    return pred, retrains
