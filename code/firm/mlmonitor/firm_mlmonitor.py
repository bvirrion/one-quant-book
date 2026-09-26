"""firm.mlmonitor -- monitors for a model in production, alarms calibrated to a false-alarm rate, and the promotion and
rollback decisions they feed (Book 12, chapter 27).

Input monitors compare each day's feature values with the training reference (population stability index on the
reference's decile bins; the two-sample Kolmogorov-Smirnov statistic); output monitors do the same for the predictions
and watch their share inside the no-trade threshold; the outcome monitor runs a one-sided CUSUM on the daily
information coefficient against its expected level. Every threshold is set on simulated or historical days without
failures to a chosen false-alarm rate. A challenger is compared with the champion in shadow by Book 7's always-valid
sequential test (firm.abtest), and a rollback restores the previous production version in firm.exptrack's registry.
NumPy only.

API (stable):
    Reference(ref, bins) -> a reference sample prepared once (psi and ks take either)
    psi(ref, x, bins) -> population stability index of x against ref's quantile bins
    ks(ref, x) -> two-sample Kolmogorov-Smirnov statistic
    daily_ic(pred, y) -> rank correlation
    Cusum(target, k, h) .update(v) -> alarm (a fall of v below target by more than k on average)
    calibrate_daily(null_stats, rate) -> threshold with that daily false-alarm rate
    onsets(alarms) -> the days an alarm starts ; calibrate_pages(null_stats, rate) -> threshold paging at that rate
    first_alarm(stats, threshold, start) -> days from start to the first exceedance (None if never)
    shadow_verdict(ic_challenger, ic_champion, tau, min_days) -> always-valid p-value path of the daily IC differences
    rollback(registry, name, ts, reason) -> restores the previous production version in firm.exptrack's Registry
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "abtest"))
from firm_abtest import always_valid_p  # noqa: E402


class Reference:
    """A reference sample prepared once: sorted values, quantile bin edges and the reference's bin shares."""

    def __init__(self, ref, bins=10):
        self.sorted = np.sort(np.asarray(ref, dtype=float))
        self.bins = bins
        self.edges = np.quantile(self.sorted, np.linspace(0, 1, bins + 1)[1:-1])
        self.shares = np.bincount(np.searchsorted(self.edges, self.sorted), minlength=bins) / len(self.sorted)


def _ref(ref, bins=10):
    return ref if isinstance(ref, Reference) else Reference(ref, bins)


def psi(ref, x, bins=10):
    """sum (p_x - p_ref) log(p_x / p_ref) over the reference's quantile bins (open-ended at both ends). ref: a sample
    or a Reference."""
    r = _ref(ref, bins)
    px = np.bincount(np.searchsorted(r.edges, x), minlength=r.bins) / len(x)
    pr, px = np.maximum(r.shares, 1e-4), np.maximum(px, 1e-4)
    return float(np.sum((px - pr) * np.log(px / pr)))


def ks(ref, x):
    """sup |F_ref - F_x| (the statistic only; no p-value). Between two of x's points F_x is flat and F_ref rises, so
    the supremum is reached at x's points, just before or at each. ref: a sample or a Reference."""
    a, b = _ref(ref).sorted, np.sort(x)
    u = np.unique(b)
    at = np.searchsorted(a, u, "right") / len(a) - np.searchsorted(b, u, "right") / len(b)
    before = np.searchsorted(a, u, "left") / len(a) - np.searchsorted(b, u, "left") / len(b)
    return float(max(np.abs(at).max(), np.abs(before).max()))


def daily_ic(pred, y):
    """Spearman rank correlation (continuous data, so no ties)."""
    rp = np.argsort(np.argsort(pred)).astype(float)
    ry = np.argsort(np.argsort(y)).astype(float)
    return float(np.corrcoef(rp, ry)[0, 1])


class Cusum:
    """Accumulates target - v - k and alarms above h; resets after an alarm."""

    def __init__(self, target, k, h):
        self.target, self.k, self.h, self.s = target, k, h, 0.0

    def update(self, v):
        self.s = max(0.0, self.s + self.target - v - self.k)
        if self.s > self.h:
            self.s = 0.0
            return True
        return False


def calibrate_daily(null_stats, rate):
    """The (1 - rate) quantile of a daily statistic on days without failures."""
    return float(np.quantile(np.asarray(null_stats), 1 - rate))


def onsets(alarms):
    """Alarm onsets (pages): days in alarm whose previous day was not; alarms is a boolean array, days on the last
    axis."""
    a = np.asarray(alarms, dtype=bool)
    prev = np.concatenate([np.zeros(a.shape[:-1] + (1,), dtype=bool), a[..., :-1]], axis=-1)
    return a & ~prev


def calibrate_pages(null_stats, rate, grid=400):
    """The lowest threshold at which a statistic, on runs without failures (runs x days), pages at most `rate` times
    a day: a statistic pooled over many days stays above its threshold for days at a time, and each such spell is one
    page, so this threshold sits below the daily quantile of calibrate_daily."""
    z = np.asarray(null_stats, dtype=float)
    for c in np.quantile(z, np.linspace(0.5, 1.0, grid + 1)):
        if onsets(z > c).mean() <= rate:
            return float(c)
    return float(z.max())


def first_alarm(stats, threshold, start):
    hit = np.flatnonzero(np.asarray(stats)[start:] > threshold)
    return int(hit[0]) if len(hit) else None


def shadow_verdict(ic_challenger, ic_champion, tau=0.05, min_days=10):
    """Always-valid p-values (Book 7's mixture sequential test) of the running mean daily IC difference, look by look.
    The standard error is estimated from the days seen so far, so no verdict is given (p = 1) before min_days: on
    three days a small sample standard deviation makes any difference look certain."""
    d = np.asarray(ic_challenger) - np.asarray(ic_champion)
    n = np.arange(1, len(d) + 1)
    mean = np.cumsum(d) / n
    sd = np.array([d[:k].std(ddof=1) if k >= max(min_days, 2) else 1e6 for k in n])
    with np.errstate(over="ignore"):                                     # an overwhelming difference: p -> 0
        return always_valid_p(mean, sd / np.sqrt(n), tau)


def rollback(registry, name, ts, reason):
    """Put back in production the version that was there before the current one (firm.exptrack's Registry), from the
    stage histories; returns the restored version, or None when there is nothing to go back to."""
    cur = registry.current(name)
    if cur is None:
        return None
    t_cur = max(t for t, st, _ in cur["history"] if st == "production")
    prev = [(t, e["version"]) for e in registry.db[name] if e is not cur
            for t, st, _ in e["history"] if st == "production" and t < t_cur]
    if not prev:
        return None
    v = max(prev)[1]
    registry.promote(name, v, "production", ts, reason)
    return v
