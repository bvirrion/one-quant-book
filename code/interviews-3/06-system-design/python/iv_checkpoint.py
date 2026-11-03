"""A long job that fails at random: how much time do checkpoints and lost work add?"""
import random


def overhead(interval, cost, mtbf, work=2_000_000.0, seed=1):
    """Simulated extra time per unit of work; `work`, `interval` and `cost` in seconds."""
    rng = random.Random(seed)
    now, done = 0.0, 0.0
    next_failure = rng.expovariate(1 / mtbf)
    while done < work:
        chunk = min(interval, work - done)
        end = now + chunk + cost
        if end > next_failure:               # back to the last checkpoint, no restart cost
            now = next_failure
            next_failure = now + rng.expovariate(1 / mtbf)
        else:
            now, done = end, done + chunk
    return now / work - 1
