"""Chapter 4 of One Quant Book 14: disciplining a server's clock, simulated with firm.clocksync.

    SETUPS                   four ways of disciplining one slave over the same loaded three-switch path
    run(name, hours, seed)   the true offset after each exchange
    summary(name)            maximum and standard deviation of |offset| after the first six minutes
    adev()                   Allan deviation of the free-running oscillator and of the disciplined clock
    asymmetry_bias(a)        the offset a path asymmetry of a ns leaves behind (simulation and formula)
    budget(parts)            an error budget: worst case (sum) and root-sum-square of independent parts
    holdover(limit, y, d)    time to breach from a residual frequency error and an ageing drift
Every parameter is a model value stated in the chapter, not a measurement of a particular clock or switch.
"""
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code" / "firm" / "clocksync"))
import firm_clocksync as cs  # noqa: E402

SW = cs.Path(stamp_ns=5_000.0)                  # software timestamps: 5 us of noise
HW = cs.Path(stamp_ns=8.0)                      # hardware timestamps: 8 ns of noise
SETUPS = {
    "software": dict(path=SW),
    "hardware": dict(path=HW),
    "hardware, min-delay filter": dict(path=HW, min_filter=8),
    "hardware, transparent clocks": dict(path=HW, transparent=True),
}
WARM_S = 360.0


def run(name, hours=1.0, seed=3):
    return cs.simulate(hours=hours, seed=seed, **SETUPS[name])


def summary(name, hours=1.0, seed=3):
    r = run(name, hours, seed)
    o = r["offset_ns"][r["t_s"] > WARM_S]
    return {"max_abs_ns": float(np.abs(o).max()), "std_ns": float(o.std()), "mean_ns": float(o.mean())}


def free_running(hours=1.0, interval_s=0.125, seed=3):
    osc = cs.Oscillator()
    rng = np.random.default_rng(osc.seed + seed)
    n = int(hours * 3600 / interval_s)
    y = osc.freq_ppm * 1e3 + np.cumsum(rng.normal(0.0, osc.walk_ppb * math.sqrt(interval_s), n))
    return np.cumsum(y * interval_s)


def adev(taus=(0.125, 0.5, 2, 8, 32, 128, 512)):
    free = cs.allan_deviation(free_running(), 0.125, taus)
    disc = cs.allan_deviation(run("hardware, transparent clocks")["offset_ns"], 0.125, taus)
    return free, disc


def asymmetry_bias(asym_ns, seed=3):
    r = cs.simulate(hours=0.25, seed=seed, transparent=True, path=cs.Path(stamp_ns=8.0, asym_ns=asym_ns))
    return float(r["offset_ns"][r["t_s"] > 300].mean()), -asym_ns / 2


def budget(parts):
    v = list(parts.values())
    return {"worst_ns": float(sum(v)), "rss_ns": float(math.sqrt(sum(x * x for x in v)))}


def holdover(limit_ns, freq_ppb, drift_ppb_per_s=0.0, offset0_ns=0.0):
    return cs.holdover_s(limit_ns, offset0_ns, freq_ppb, drift_ppb_per_s)
