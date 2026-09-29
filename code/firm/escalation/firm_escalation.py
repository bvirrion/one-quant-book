"""firm.escalation -- the breach register and escalation workflow as data (build of One Quant Book 16, chapter 12).

Input: a desk-by-day array of measured exposure, the desk-by-day effective hard limit (from firm.limitalloc's
framework, temporary increases included: `hard_path`), and the days on which a desk's risk model changed. A breach
is a run of days with exposure above the hard limit. The register records, for each breach, its peak excess,
duration, severity, whom the rules say to tell and by when, and how it was resolved on the day it closed:
    limit increase  -- the hard limit rose on the closing day
    model change    -- the desk's risk model changed on the closing day or the day before
    position cut    -- neither: exposure fell
    open            -- still open at the end of the data
Red flags (the pattern of the public record): a limit raised or a model changed while a breach is open; and
repeated temporary increases (`repeat_count` increases for one desk within `repeat_window` days).

API (stable):
    Rules(minor_excess, major_excess, minor_days, major_days, repeat_window, repeat_count, notify)
    severity(excess, days, rules) -> 1 | 2 | 3 ; notify(severity, rules) -> (who, within business days)
    hard_path(node, measure, n_days, increases) -> effective hard limit per day (firm.limitalloc.Node)
    register(expo, hard, model_days, rules) -> list of Breach ; stats(breaches) -> dict ; flagged(breaches)
    backdated(changes) -> the limit changes effective before they were approved
"""
from dataclasses import dataclass, field

import numpy as np

NOTIFY = {1: ("head of desk", 0), 2: ("chief risk officer", 1), 3: ("risk committee", 2)}


@dataclass(frozen=True)
class Rules:
    minor_excess: float = 0.05      # peak excess over the hard limit, as a fraction of it
    major_excess: float = 0.20
    minor_days: int = 2             # duration in days
    major_days: int = 5
    repeat_window: int = 60
    repeat_count: int = 2
    notify: dict = field(default_factory=lambda: dict(NOTIFY))


DEFAULT = Rules()


def severity(excess, days, rules=None):
    rules = rules or DEFAULT
    if excess > rules.major_excess or days > rules.major_days:
        return 3
    if excess > rules.minor_excess or days > rules.minor_days:
        return 2
    return 1


def notify(sev, rules=None):
    rules = rules or DEFAULT
    return rules.notify[sev]


def hard_path(node, measure, n_days, increases=()):
    """The node's effective hard limit each day (firm.limitalloc), plus dated increases ((extra, first, last), ...)
    granted during the year (limitalloc's own temporary increases run from day 0)."""
    return np.array([node.hard(measure, d) + sum(x for x, a, b in increases if a <= d <= b) for d in range(n_days)])


@dataclass
class Breach:
    desk: int
    opened: int
    closed: int          # first day back within the limit (n_days if still open)
    peak_excess: float
    resolution: str
    severity: int = 1
    flags: list = field(default_factory=list)

    @property
    def days(self):
        return self.closed - self.opened


def register(expo, hard, model_days=(), rules=None):
    rules = rules or DEFAULT
    expo, hard = np.asarray(expo, float), np.asarray(hard, float)
    n_desks, n_days = expo.shape
    models = set(model_days)
    out = []
    for d in range(n_desks):
        over = expo[d] > hard[d]
        t = 0
        while t < n_days:
            if not over[t]:
                t += 1
                continue
            s = t
            while t < n_days and over[t]:
                t += 1
            peak = float(np.max(expo[d, s:t] / hard[d, s:t]) - 1)
            if t == n_days:
                how = "open"
            elif hard[d, t] > hard[d, t - 1]:
                how = "limit increase"
            elif (d, t) in models or (d, t - 1) in models:
                how = "model change"
            else:
                how = "position cut"
            b = Breach(d, s, t, peak, how, severity(peak, t - s, rules))
            if any(hard[d, k] > hard[d, k - 1] for k in range(max(s, 1), min(t + 1, n_days))):
                b.flags.append("limit raised during breach")
            if any((d, k) in models for k in range(s, min(t + 1, n_days))):
                b.flags.append("model changed during breach")
            ups = [k for k in range(1, n_days) if hard[d, k] > hard[d, k - 1] and s - rules.repeat_window <= k <= t]
            if len(ups) >= rules.repeat_count:
                b.flags.append("repeated increases")
            out.append(b)
    return out


def stats(breaches):
    kinds = ("position cut", "limit increase", "model change", "open")
    n = len(breaches)
    closed = [b.days for b in breaches if b.resolution != "open"]
    return {"n": n, "share": {k: sum(b.resolution == k for b in breaches) / n for k in kinds},
            "median_days": float(np.median(closed)), "mean_days": float(np.mean(closed)),
            "p90_days": float(np.percentile(closed, 90)), "breach_days": int(sum(b.days for b in breaches)),
            "severity": {s: sum(b.severity == s for b in breaches) for s in (1, 2, 3)},
            "flagged": sum(bool(b.flags) for b in breaches)}


def flagged(breaches):
    return [b for b in breaches if b.flags]


def backdated(changes):
    """Limit changes whose effective day precedes their approval day: (desk, effective, approved, new_limit), ...
    A backdated increase rewrites the register's history; keep limits point in time (as known each day)."""
    return [c for c in changes if c[1] < c[2]]
