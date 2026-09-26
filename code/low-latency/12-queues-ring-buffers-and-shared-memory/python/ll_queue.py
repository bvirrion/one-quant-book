"""Chapter 12 of One Quant Book 13: sizing rings (the M/M/1 formulas of One Quant Book 4, chapter 8), the time before a
slow consumer is lapped, and conflation. Readers of the measured CSVs."""
import csv
import pathlib

FIG = pathlib.Path(__file__).resolve().parents[4] / "figdata/low-latency/12-queues-ring-buffers-and-shared-memory"


def mm1(lam, mu):
    """Utilisation, mean number in system, mean time in system and P(N >= n) for an M/M/1 queue."""
    rho = lam / mu
    return {"rho": rho, "L": rho / (1 - rho), "W": 1 / (mu - lam), "tail": lambda n: rho**n}


def ring_for(lam, mu, p_full):
    """Smallest power-of-two ring whose M/M/1 occupancy exceeds its size with probability below p_full."""
    rho = lam / mu
    n = 1
    while rho**n >= p_full:
        n *= 2
    return n


def time_to_overrun(slots, burst_rate, consumer_rate):
    """Seconds before a broadcast ring of `slots` laps a reader consuming more slowly than the burst."""
    return slots / (burst_rate - consumer_rate) if burst_rate > consumer_rate else float("inf")


def conflated_share(update_rate, reader_rate):
    """Share of updates a last-value reader never sees when updates outpace it."""
    return max(0.0, 1 - reader_rate / update_rate)


def rtt():
    with open(FIG / "measured_rtt.csv", newline="") as f:
        skip = ("transport", "placement", "key")
        return {(r["transport"], r["placement"]): {k: float(v) for k, v in r.items() if k not in skip}
                for r in csv.DictReader(f)}


def throughput():
    with open(FIG / "measured_throughput.csv", newline="") as f:
        return float(next(csv.DictReader(f))["msgs_per_s"])
