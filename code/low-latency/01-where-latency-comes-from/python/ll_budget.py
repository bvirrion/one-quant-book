"""Chapter 1 of One Quant Book 13: latency budgets and races, on synthetic distributions (deterministic).

The stage model is illustrative, not a measurement: each stage has a lognormal body (median, dispersion) and a
small probability (0.3%) of a stall of exponential length, independently. No stage's p99 sees its stalls; the
path, with six chances, is stalled 1.8% of the time, so its p99 does.
"""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "code/firm/latbudget"))
import firm_latbudget as lb  # noqa: E402

# name, median ns, lognormal sigma
STAGES = (("receive", 900.0, 0.20), ("decode", 60.0, 0.25), ("book", 120.0, 0.30),
          ("strategy", 200.0, 0.25), ("risk", 50.0, 0.20), ("send", 800.0, 0.20))
STALL_P = 0.003      # probability that a stage (or the whole path) is stalled on a message
STALL_MEAN = 8000.0  # mean stall, ns


def stage_samples(n=400_000, seed=11, stall_p=STALL_P):
    """Per-stage samples (ns): lognormal body plus, with probability STALL_P, an exponential stall."""
    rng = np.random.default_rng(seed)
    out = {}
    for name, med, sig in STAGES:
        body = med * np.exp(sig * rng.standard_normal(n))
        out[name] = body + np.where(rng.random(n) < stall_p, rng.exponential(STALL_MEAN, n), 0.0)
    return out


def composition(n=400_000, seed=11, stall_p=STALL_P):
    """End-to-end mean, p50, p99, p99.9 against the sums of the stages' means and percentiles."""
    s = stage_samples(n, seed, stall_p)
    tot = lb.compose_joint(s)
    k = len(s)
    return {
        "mean_sum": sum(float(np.mean(v)) for v in s.values()), "mean": float(np.mean(tot)),
        "sum_p50": sum(lb.quantile(v, 0.5) for v in s.values()), "p50": lb.quantile(tot, 0.5),
        "sum_p99": sum(lb.quantile(v, 0.99) for v in s.values()), "p99": lb.quantile(tot, 0.99),
        "p999": lb.quantile(tot, 0.999), "level": lb.stage_level(0.99, k),
        "sum_union": sum(lb.quantile(v, lb.stage_level(0.99, k)) for v in s.values()),
    }


def ccdf_rows(n=400_000, seed=11, grid=None):
    """Rows (x_ns, P(total > x)) on a log grid."""
    grid = np.geomspace(1500, 60000, 60) if grid is None else grid
    tot = np.sort(lb.compose_joint(stage_samples(n, seed)))
    return [(round(float(x), 1), 1 - np.searchsorted(tot, x, "right") / n) for x in grid]


# ---- races ----------------------------------------------------------------------------------------------------

def firm_latency(n, rng, median, sigma=0.15, stall_p=0.0, stall_mean=30_000.0):
    body = median * np.exp(sigma * rng.standard_normal(n))
    return body + np.where(rng.random(n) < stall_p, rng.exponential(stall_mean, n), 0.0)


def win_probability(ours, theirs):
    return float(np.mean(ours < theirs) + 0.5 * np.mean(ours == theirs))


A = {"median": 2000.0, "stall_p": 0.02}     # our firm: faster body, more stalls
B = {"median": 2200.0, "stall_p": 0.005}    # the competitor


def race(n=1_000_000, seed=5, a=None, b=None):
    rng = np.random.default_rng(seed)
    a = dict(A, **(a or {}))
    b = dict(B, **(b or {}))
    xa = firm_latency(n, rng, **a)
    xb = firm_latency(n, rng, **b)
    return win_probability(xa, xb), lb.quantile(xa, 0.5), lb.quantile(xa, 0.99)


def race_results():
    base = race()
    half_median = race(a={"median": 1000.0})
    half_stalls = race(a={"stall_p": 0.01})
    no_stalls = race(a={"stall_p": 0.0})
    return {"base": base, "half_median": half_median, "half_stalls": half_stalls, "no_stalls": no_stalls}


def race_curve(shifts=None, n=400_000, seed=5):
    """P(win) against our median (ns), competitor fixed; with and without our stalls."""
    shifts = np.arange(1600, 2801, 50) if shifts is None else shifts
    rows = []
    for m in shifts:
        with_stalls = race(n, seed, a={"median": float(m)})[0]
        rows.append((int(m), with_stalls, race(n, seed, a={"median": float(m), "stall_p": 0.0})[0]))
    return rows


def fibre_ns_per_m(group_index=1.4620):
    return group_index / 299_792_458.0 * 1e9


def serialisation_ns(frame_bytes, gbps, overhead_bytes=20):
    """Time to put a frame on the wire: frame plus preamble, start delimiter and inter-frame gap (20 bytes)."""
    return (frame_bytes + overhead_bytes) * 8 / gbps
