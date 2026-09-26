"""firm.latbudget -- latency budgets as data (build of One Quant Book 13, chapter 1).

A budget lists the stages of a path and, for each, a target at one or more percentiles. Measured samples (one array
of nanoseconds per stage, aligned message by message when they come from one run) are checked against it, and the
end-to-end distribution is composed either jointly (the per-message sums: the truth when the samples are aligned) or
under an independence assumption (random pairing of the stages' samples).

Percentiles of a sum do not add. What does hold for any dependence (the union bound on tails):
    q_{1 - sum a_i}( sum X_i ) <= sum q_{1 - a_i}(X_i),
so an end-to-end target at level p is guaranteed by stage targets at level 1 - (1 - p)/n whose sum is within it.

API (stable):
    quantile(x, p)                      nearest-rank quantile (p in [0, 1])
    Stage(name, targets)                targets: {percentile level: ns}
    Budget(stages, end_to_end)          end_to_end: {level: ns}
    Budget.check(samples) -> list[dict] one row per (stage or 'end-to-end', level): target, measured, ok
    compose_joint(samples) -> ndarray   per-message sum of aligned stage samples
    compose_independent(samples, n, seed) -> ndarray  sum of independently resampled stages
    stage_level(p, n) -> float          the per-stage level that guarantees level p end to end (union bound)
    allocate(total_ns, weights) -> list[float]  split an end-to-end budget in proportion to weights
"""
import math
from dataclasses import dataclass, field

import numpy as np


def quantile(x, p):
    v = np.sort(np.asarray(x, dtype=float))
    return float(v[min(len(v) - 1, math.floor(p * len(v)))])


@dataclass(frozen=True)
class Stage:
    name: str
    targets: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Budget:
    stages: tuple
    end_to_end: dict = field(default_factory=dict)

    def check(self, samples):
        rows = []
        for s in self.stages:
            for p, target in sorted(s.targets.items()):
                m = quantile(samples[s.name], p)
                rows.append({"stage": s.name, "level": p, "target": target, "measured": m, "ok": m <= target})
        total = compose_joint({s.name: samples[s.name] for s in self.stages})
        for p, target in sorted(self.end_to_end.items()):
            m = quantile(total, p)
            rows.append({"stage": "end-to-end", "level": p, "target": target, "measured": m, "ok": m <= target})
        return rows


def compose_joint(samples):
    arrs = [np.asarray(v, dtype=float) for v in samples.values()]
    n = min(len(a) for a in arrs)
    return np.sum([a[:n] for a in arrs], axis=0)


def compose_independent(samples, n, seed=0):
    rng = np.random.default_rng(seed)
    return np.sum([rng.choice(np.asarray(v, dtype=float), size=n) for v in samples.values()], axis=0)


def stage_level(p, n):
    return 1.0 - (1.0 - p) / n


def allocate(total_ns, weights):
    w = np.asarray(weights, dtype=float)
    return list(total_ns * w / w.sum())
