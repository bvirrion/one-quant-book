"""firm.algos -- the benchmark execution algorithms as schedulers, and the intraday volume forecasters (build of One
Quant Book 10, chapter 16).

A trading day is split into B bins; volumes are arrays of B bins (one day) or days x bins (a history). A volume model
forecasts the volume of the bins still to come from the bins seen so far today; a VWAP schedule trades in proportion
to the forecast, once at the start (static) or bin by bin as the day unfolds (dynamic).

API (stable):
    profile(history)                     the mean share of each bin in the day's volume
    Profile(prof, adv)                   static model: the remaining bins are adv x profile, whatever happened today
    LevelAR(prof, adv, rho, s_level, s_dev)  log volume = log(adv x profile) + the day's level + an AR(1) deviation:
                                         the bins seen today estimate the level (which lasts all day) and the last
                                         deviation (which fades at rate rho); LevelAR.fit(history) estimates all five
    PCAARMA(window, r=1)                 Bialkowski, Darolles and Le Fol's decomposition: window is days x bins x stocks
                                         of turnover; the common part (r principal components across stocks) is
                                         forecast by its average over the window's days, each stock's specific part by
                                         an AR(1); .model(j) is stock j's volume model
    model.remaining(observed)            forecast volumes of the bins after the observed ones
    vwap(Q, model, day, dynamic)         a VWAP schedule: quantities per bin
    twap(Q, bins)                        equal quantities
    pov(rate, others, own_counted)       participation `rate` of the volume, one bin late: rate x the last bin's whole
                                         volume (own_counted), or rate / (1 - rate) x the others' volume; both reach
                                         `rate` of the volume when it is steady
    shortfall(Q, bins, kT)               Almgren-Chriss quantities (firm.acexec) with urgency kT
    close(Q, model, moc_share, start)    a static VWAP over the bins from `start` for all but moc_share, the rest kept
                                         for the closing auction
    decompose(q, fills, v, vwaps)        VWAP slippage split exactly into an execution part, sum q_k (fill_k - vwap_k),
                                         and a schedule part, sum (q_k / Q - v_k / V) vwap_k, both per share
    tracking(q, v)                       sum over bins of (cumulative schedule share - cumulative volume share)^2: with
                                         prices a random walk of variance s2 a bin, the schedule part of the slippage
                                         has variance s2 x tracking
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "acexec"))
from firm_acexec import trajectory  # noqa: E402


def profile(history) -> np.ndarray:
    h = np.asarray(history, float)
    return (h / h.sum(axis=1, keepdims=True)).mean(axis=0)


class Profile:
    def __init__(self, prof, adv: float):
        self.p, self.adv = np.asarray(prof, float) / np.sum(prof), adv

    def remaining(self, observed) -> np.ndarray:
        return self.adv * self.p[len(observed):]


class LevelAR(Profile):
    """log v_k = log(adv p_k) + l + e_k: an unknown level l for the day (variance s_level^2) and an AR(1) deviation e
    (coefficient rho, stationary variance s_dev^2). After k bins, l is estimated by generalised least squares from
    the k deviations seen, e_k is what is left of the last one, and the forecast is adv p exp(l + rho^i e_k)."""

    def __init__(self, prof, adv: float, rho: float, s_level: float, s_dev: float):
        super().__init__(prof, adv)
        self.rho, self.s_level, self.s_dev = rho, s_level, s_dev

    @classmethod
    def fit(cls, history) -> LevelAR:
        h = np.asarray(history, float)
        prof, adv = profile(h), float(h.sum(axis=1).mean())
        dev = np.log(h / (adv * prof))
        lev = dev.mean(axis=1)
        e = dev - lev[:, None]
        rho = float(np.sum(e[:, 1:] * e[:, :-1]) / np.sum(e[:, :-1] ** 2))
        return cls(prof, adv, rho, float(lev.std(ddof=1)), float(e.std(ddof=1)))

    def remaining(self, observed) -> np.ndarray:
        k, base = len(observed), super().remaining(observed)
        if k == 0:
            return base
        y = np.log(np.maximum(np.asarray(observed, float), 1e-9) / (self.adv * self.p[:k]))
        i = np.arange(k)
        cov = self.s_dev**2 * self.rho ** np.abs(i[:, None] - i[None, :])
        w = np.linalg.solve(cov, np.ones(k))
        level = float(w @ y / (w.sum() + 1 / self.s_level**2))   # GLS, shrunk toward zero
        fade = self.rho ** np.arange(1, len(base) + 1)   # e fades, the level stays
        return base * np.exp(level + (y[-1] - level) * fade)


class PCAARMA:
    def __init__(self, window, r: int = 1):
        w = np.asarray(window, float)                           # days x bins x stocks
        d, b, n = w.shape
        x = w.reshape(d * b, n)
        u, s, vt = np.linalg.svd(x, full_matrices=False)
        common = (u[:, :r] * s[:r]) @ vt[:r]
        spec = x - common
        self.common = common.reshape(d, b, n).mean(axis=0)     # bins x stocks: tomorrow's common part
        self.ar = []
        for j in range(n):
            e = spec[:, j]
            beta = np.linalg.lstsq(np.c_[np.ones(len(e) - 1), e[:-1]], e[1:], rcond=None)[0]
            self.ar.append((float(beta[0]), float(beta[1]), float(e[-1])))
        self.bins = b

    def model(self, j: int) -> _Stock:
        return _Stock(self, j)


class _Stock:
    def __init__(self, fit: PCAARMA, j: int):
        self.c = fit.common[:, j]
        self.a, self.phi, self.last = fit.ar[j]

    def remaining(self, observed) -> np.ndarray:
        k = len(observed)
        e = self.last if k == 0 else float(observed[-1]) - self.c[k - 1]
        out = np.empty(len(self.c) - k)
        for i in range(len(out)):
            e = self.a + self.phi * e
            out[i] = self.c[k + i] + e
        return np.maximum(out, 1e-9)


def vwap(q_total: float, model, day, dynamic: bool) -> np.ndarray:
    day = np.asarray(day, float)
    if not dynamic:
        f = model.remaining(day[:0])
        return q_total * f / f.sum()
    q, left = np.zeros(len(day)), q_total
    for k in range(len(day)):
        f = model.remaining(day[:k])
        q[k] = left * f[0] / f.sum()
        left -= q[k]
    return q


def twap(q_total: float, bins: int) -> np.ndarray:
    return np.full(bins, q_total / bins)


def pov(rate: float, others, own_counted: bool = True) -> np.ndarray:
    """Trade in bin k to be `rate` of bin k-1's volume (the first bin trades nothing)."""
    others = np.asarray(others, float)
    q = np.zeros(len(others))
    for k in range(1, len(others)):
        if own_counted:
            q[k] = rate * (others[k - 1] + q[k - 1])
        else:
            q[k] = rate / (1 - rate) * others[k - 1]
    return q


def shortfall(q_total: float, bins: int, kt: float) -> np.ndarray:
    t = np.linspace(0.0, 1.0, bins + 1)
    return -np.diff(trajectory(q_total, 1.0, kt, t))


def close(q_total: float, model, moc_share: float, start: int = 0) -> tuple[np.ndarray, float]:
    f = model.remaining(np.zeros(0))
    f[:start] = 0.0
    return q_total * (1 - moc_share) * f / f.sum(), q_total * moc_share


def decompose(q, fills, v, vwaps) -> tuple[float, float]:
    q, f, v, w = (np.asarray(a, float) for a in (q, fills, v, vwaps))
    live = q > 0
    execution = float(q[live] @ (f[live] - w[live]) / q.sum())
    schedule = float((q / q.sum() - v / v.sum()) @ w)
    return execution, schedule


def tracking(q, v) -> float:
    q, v = np.asarray(q, float), np.asarray(v, float)
    return float(np.sum((np.cumsum(q) / q.sum() - np.cumsum(v) / v.sum())[:-1] ** 2))
