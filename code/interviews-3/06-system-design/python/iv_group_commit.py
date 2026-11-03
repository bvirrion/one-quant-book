"""A journal with one disk flush at a time: each flush takes everything that has arrived."""


def simulate(rate, flush, n=100_000, group=True):
    """Arrivals every 1/rate seconds. Returns (mean latency, mean batch, last completion)."""
    free_at = total = 0.0
    i = batches = 0
    while i < n:
        start = max(free_at, i / rate)
        waiting = 1
        if group:                            # all who arrived by the time the disk came free
            waiting = max(1, min(n, int(start * rate) + 1) - i)
        free_at = start + flush
        for k in range(i, i + waiting):
            total += free_at - k / rate
        i += waiting
        batches += 1
    return total / n, n / batches, free_at
