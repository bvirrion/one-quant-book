"""Chapter 3 of One Quant Book 14: interrupts, coalescing and polling, as a model.

Packets arrive at rate lam (per microsecond, Poisson). With interrupt coalescing (usecs u, frames m) the card raises
an interrupt when m packets are pending or u microseconds after the first pending one, whichever comes first; the
host then pays c_irq of CPU and w of wake-up before processing the pending packets at c_pkt each, in order. With a
polling core the host checks the ring every loop of length p and processes what it finds; the core is always busy.
All costs are model parameters (defaults stated in the chapter), not measurements of a particular card.

    coalesce(lam, u, m, c_irq, w, c_pkt, n, seed) -> dict(mean_us, p99_us, cpu, irq_rate)
    poll(lam, p, c_pkt, n, seed) -> dict(mean_us, p99_us, cpu)
    crossover(u, m, c_irq, c_pkt) -> packets per microsecond at which interrupts' CPU reaches one core
    measured() -> rows of measured_rx.csv (the laptop's kernel path)
"""
import csv
import pathlib

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
FIG = ROOT / "figdata" / "networks" / "03-network-cards-and-kernel-bypass"
C_IRQ, WAKE, C_PKT = 2.0, 3.0, 0.3            # microseconds: model values


def coalesce(lam, u, m, c_irq=C_IRQ, w=WAKE, c_pkt=C_PKT, n=100_000, seed=1):
    rng = np.random.default_rng(seed)
    t = np.cumsum(rng.exponential(1.0 / lam, n))
    lat = np.empty(n)
    i, busy_until, irqs, cpu = 0, 0.0, 0, 0.0
    while i < n:
        first = t[i]
        deadline = first + u
        j = i
        while j < n and j - i < m and t[j] <= deadline:
            j += 1
        fire = t[j - 1] if j - i == m else deadline          # m-th packet or the timer
        start = max(fire + w, busy_until) + c_irq
        done = start + c_pkt * np.arange(1, j - i + 1)
        lat[i:j] = done - t[i:j]
        busy_until = done[-1]
        irqs += 1
        cpu += c_irq + c_pkt * (j - i)
        i = j
    span = t[-1] - t[0]
    return {"mean_us": float(lat.mean()), "p99_us": float(np.quantile(lat, 0.99)), "cpu": float(cpu / span),
            "irq_rate": float(irqs / span)}


def poll(lam, p=0.2, c_pkt=C_PKT, n=100_000, seed=1):
    rng = np.random.default_rng(seed)
    t = np.cumsum(rng.exponential(1.0 / lam, n))
    check = np.ceil(t / p) * p                                  # next check of the ring after the arrival
    lat = np.empty(n)
    free = 0.0
    for k in range(n):
        start = max(check[k], free)
        free = start + c_pkt
        lat[k] = free - t[k]
    return {"mean_us": float(lat.mean()), "p99_us": float(np.quantile(lat, 0.99)), "cpu": 1.0}


def crossover(u, m, c_irq=C_IRQ, c_pkt=C_PKT):
    """Rate (per us) at which interrupt-driven receive uses a whole core, when every interrupt carries m packets
    (the high-rate regime: the m-th packet arrives before the timer)."""
    return 1.0 / (c_irq / m + c_pkt)


def measured():
    with open(FIG / "measured_rx.csv") as f:
        return list(csv.DictReader(f))
