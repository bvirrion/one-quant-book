"""Chapter 13 -- the arithmetic of interruptions: what gaps in a thread's running time cost a message that arrives
at a random moment, what the tick and real-time throttling take, and the weekend problem's tuned-host model.

A thread that should run continuously is interrupted by gaps g_1, ..., g_n during an observation of length T. A
message arriving at a uniformly random moment falls inside gap i with probability g_i / T and then waits for the rest
of it, uniformly distributed on [0, g_i]; hence (proposition in the chapter)
    stolen fraction        sum(g) / T
    mean added wait        sum(g^2) / (2 T)
    P(added wait > x)      sum(max(g - x, 0)) / T
"""
import numpy as np


def stolen_fraction(gaps, T):
    return float(np.sum(gaps)) / T


def mean_wait(gaps, T):
    g = np.asarray(gaps, dtype=float)
    return float(np.sum(g * g)) / (2 * T)


def p_wait_exceeds(gaps, T, x):
    g = np.asarray(gaps, dtype=float)
    return float(np.sum(np.maximum(g - x, 0.0))) / T


def wait_quantile(gaps, T, p):
    """Smallest x with P(added wait > x) <= 1 - p (0 when the thread is running at a fraction p of moments)."""
    g = np.sort(np.asarray(gaps, dtype=float))[::-1]
    target = 1 - p
    lo, hi = 0.0, float(g[0]) if len(g) else 0.0
    if p_wait_exceeds(g, T, 0.0) <= target:
        return 0.0
    for _ in range(100):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if p_wait_exceeds(g, T, mid) > target else (lo, mid)
    return hi


def periodic(rate_hz, cost_ns, T_ns=1e9):
    """Gaps of a periodic interruption (the tick) over T: rate x T gaps of cost_ns each."""
    return np.full(int(round(rate_hz * T_ns / 1e9)), float(cost_ns))


def rt_throttle_gap(period_us=1_000_000, runtime_us=950_000):
    """Worst gap forced on a spinning SCHED_FIFO thread by real-time throttling: the rest of each period, in ns."""
    return (period_us - runtime_us) * 1000.0


def share_of_cpu(runnable):
    """Share of a CPU a spinning thread gets beside runnable - 1 equal-weight spinners."""
    return 1.0 / runnable


# Weekend problem: the laptop's measured summary against a tuned host described by stated assumptions.
TUNED = dict(residual=[(1.0, 2_000.0)], mispinned=[])   # one 2 us interruption a second (assumed, not measured)


def problem():
    tuned = np.concatenate([periodic(r, c) for r, c in TUNED["residual"]])
    ticked = periodic(250, 2_000.0)        # the same host with a 250 Hz tick of 2 us (assumed cost)
    one = 1e9
    return dict(
        tick_fraction=stolen_fraction(ticked, one),
        tick_mean_wait=mean_wait(ticked, one),
        tick_p_wait_1us=p_wait_exceeds(ticked, one, 1_000.0),
        tuned_fraction=stolen_fraction(tuned, one),
        tuned_mean_wait=mean_wait(tuned, one),
        throttle_gap_ms=rt_throttle_gap() / 1e6,
        throttle_fraction=rt_throttle_gap() / one,
    )


if __name__ == "__main__":
    for k, v in problem().items():
        print(f"{k:18s}{v:.6g}")
