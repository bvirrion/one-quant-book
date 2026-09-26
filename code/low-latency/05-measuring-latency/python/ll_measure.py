"""Chapter 5 of One Quant Book 13: coordinated omission, simulated deterministically (times in microseconds).

A service answers in about 100 us (lognormal, dispersion 0.2) and freezes for 10 ms at the start of every second.
Two testers intend one request per millisecond for 100 s:
  closed loop  sends the next request when the previous reply has come back, or at the next millisecond if later;
  open loop    sends at every millisecond whatever happens, and measures from the intended send time.
The closed-loop latencies are recorded raw and with firm.lathist's correction (expected interval 1 ms).
"""
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/lathist"))
from firm_lathist import LatHist  # noqa: E402

INTERVAL = 1000.0     # us between intended requests
STALL = 10_000.0      # us frozen at the start of every second
SECONDS = 100


def service_times(n, seed=5):
    return 100.0 * np.exp(0.2 * np.random.default_rng(seed).standard_normal(n))


def _stall_end(t, stall=STALL, period=1e6):
    """If t falls inside a freeze (the first `stall` us of every `period`), the time the freeze ends; otherwise t."""
    start = np.floor(t / period) * period
    return start + stall if t < start + stall else t


def open_loop(seconds=SECONDS, seed=5, stall=STALL, period=1e6):
    n = int(seconds * 1e6 / INTERVAL)
    s = service_times(n, seed)
    free, out = 0.0, np.empty(n)
    for k in range(n):
        t = k * INTERVAL
        begin = _stall_end(max(t, free), stall, period)
        free = begin + s[k]
        out[k] = free - t
    return out


def closed_loop(seconds=SECONDS, seed=5, stall=STALL, period=1e6):
    s = service_times(int(seconds * 1e6 / INTERVAL) + 1, seed)
    t, k, out = 0.0, 0, []
    while t < seconds * 1e6:
        done = _stall_end(t, stall, period) + s[k]
        out.append(done - t)
        k += 1
        t = max(done, np.ceil(done / INTERVAL) * INTERVAL if done > t + INTERVAL else t + INTERVAL)
    return np.array(out)


def histograms(seconds=SECONDS, seed=5, stall=STALL, period=1e6):
    raw, corrected, opened = LatHist(), LatHist(), LatHist()
    for v in closed_loop(seconds, seed, stall, period):
        raw.record(int(v * 1000))                       # ns
        corrected.record_corrected(int(v * 1000), int(INTERVAL * 1000))
    for v in open_loop(seconds, seed, stall, period):
        opened.record(int(v * 1000))
    return {"closed loop": raw, "corrected": corrected, "open loop": opened}


NINES = (0.5, 0.9, 0.99, 0.999, 0.9999)


def spectrum(seconds=SECONDS, seed=5, ps=NINES, stall=STALL, period=1e6):
    """{name: [quantile in us for p in ps]} and the sample counts."""
    h = histograms(seconds, seed, stall, period)
    return {k: [v.quantile(p) / 1000 for p in ps] for k, v in h.items()}, {k: v.count for k, v in h.items()}
