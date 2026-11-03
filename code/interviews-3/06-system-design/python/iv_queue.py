"""A single FIFO server, by Lindley's recursion: the next wait follows from the last one."""
import random


def mean_time_in_system(rho, service=1.0, n=400_000, seed=1, fixed_service=False):
    rng = random.Random(seed)
    arrival_rate = rho / service
    wait = total = 0.0
    for _ in range(n):
        s = service if fixed_service else rng.expovariate(1 / service)
        total += wait + s
        gap = rng.expovariate(arrival_rate)
        wait = max(0.0, wait + s - gap)
    return total / n
