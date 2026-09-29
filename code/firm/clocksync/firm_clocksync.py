"""firm.clocksync -- clocks, two-way time transfer and a servo (build of One Quant Book 14, chapter 4).

A slave clock with a frequency error is disciplined to a master (a grandmaster locked to UTC) by periodic two-way
exchanges: the master sends at t1 (master time), the slave receives at t2 (slave time), the slave sends at t3, the
master receives at t4. The offset estimate is ((t2 - t1) - (t4 - t3)) / 2; it is exact when the two directions take
equal time, and wrong by half the difference otherwise. Transparent clocks on the path add each switch's residence
time to a correction field, which the endpoints subtract. A PI servo steers the slave's phase and frequency.
All times in nanoseconds; the simulation is seeded and deterministic. The servo has a C++20 twin
(cpp/firm_clocksync.hpp) that reproduces data/fixture_servo.csv.

API (stable):
    Oscillator(freq_ppm, walk_ppb, seed)       fractional frequency offset (ppm) with a random walk (ppb per sqrt(s))
    Path(base_ns, asym_ns, queue_ns, hops, stamp_ns, seed)   one-way delays: base + asymmetry share + queueing per hop
    Servo(kp, ki)                               .update(offset_ns, interval_s) -> (phase_step_ns, freq_adj_ppb)
    exchange(rng, slave_offset, path, transparent) -> (offset estimate, round trip) (ns)
    simulate(hours, interval_s, osc, path, transparent, kp, ki, seed) -> dict(t_s, offset_ns)   true offset each step
    allan_deviation(phase_ns, tau0_s, taus) -> list[(tau_s, adev)]                              overlapping ADEV
    holdover_s(limit_ns, offset0_ns, freq_ppb, drift_ppb_per_s) -> float                         time to breach
    compliance(offset_ns, limit_ns) -> dict(max_abs_ns, share_within)
"""
import math
from dataclasses import dataclass

import numpy as np


@dataclass
class Oscillator:
    freq_ppm: float = 20.0
    walk_ppb: float = 2.0
    seed: int = 1


@dataclass
class Path:
    base_ns: float = 2_000.0        # propagation and fixed processing, each way
    asym_ns: float = 0.0            # master-to-slave minus slave-to-master fixed difference
    queue_ns: float = 5_000.0       # mean queueing per hop and direction (exponential)
    hops: int = 3                   # switches on the path
    stamp_ns: float = 8.0           # timestamp noise (standard deviation): hardware ~ns, software ~us
    seed: int = 2


class Servo:
    """PI controller on the measured offset: steps the phase by kp * offset and integrates ki * offset into the
    frequency correction (ppb per ns of offset per second of interval)."""

    def __init__(self, kp=0.7, ki=0.3):
        self.kp, self.ki, self.freq_ppb = kp, ki, 0.0

    def update(self, offset_ns, interval_s):
        self.freq_ppb += self.ki * offset_ns / interval_s
        return self.kp * offset_ns, self.freq_ppb


def exchange(rng, slave_offset, path, transparent):
    """One delay request-response exchange; returns (estimated offset (slave minus master), round trip), in ns."""
    q_ms = rng.exponential(path.queue_ns, path.hops).sum()
    q_sm = rng.exponential(path.queue_ns, path.hops).sum()
    d_ms = path.base_ns + path.asym_ns / 2 + q_ms
    d_sm = path.base_ns - path.asym_ns / 2 + q_sm
    n = rng.normal(0.0, path.stamp_ns, 4)
    t1 = 0.0
    t2 = d_ms + slave_offset + n[1] - n[0]
    t3 = t2 + 1_000.0
    t4 = t3 - slave_offset + d_sm + n[3] - n[2]
    corr_ms, corr_sm = (q_ms, q_sm) if transparent else (0.0, 0.0)
    return ((t2 - t1 - corr_ms) - (t4 - t3 - corr_sm)) / 2, (t4 - t1) - (t3 - t2)


def simulate(hours=1.0, interval_s=0.125, osc=None, path=None, transparent=False, kp=0.7, ki=0.3, seed=3,
             min_filter=1):
    """Discipline a slave for `hours`; returns the true offset after each exchange. With min_filter > 1 the servo acts
    every min_filter exchanges on the one with the smallest round trip (the idea of NTP's clock filter)."""
    osc, path = osc or Oscillator(), path or Path()
    rng_o, rng_p = np.random.default_rng(osc.seed + seed), np.random.default_rng(path.seed + seed)
    n = int(hours * 3600 / interval_s)
    servo = Servo(kp, ki)
    offset, y = 0.0, osc.freq_ppm * 1e3                   # ns; fractional frequency in ppb
    out, buf = np.empty(n), []
    for k in range(n):
        y += rng_o.normal(0.0, osc.walk_ppb * math.sqrt(interval_s))
        offset += (y - servo.freq_ppb) * interval_s          # ppb * s = ns
        buf.append(exchange(rng_p, offset, path, transparent))
        if len(buf) >= min_filter:
            use = min(buf, key=lambda e: e[1])[0]
            buf = []
            step, _ = servo.update(use, interval_s * min_filter)
            offset -= step
        out[k] = offset
    return {"t_s": np.arange(1, n + 1) * interval_s, "offset_ns": out}


def allan_deviation(phase_ns, tau0_s, taus):
    x = np.asarray(phase_ns, dtype=float) * 1e-9
    out = []
    for tau in taus:
        m = int(round(tau / tau0_s))
        if m < 1 or 2 * m >= len(x):
            continue
        d = x[2 * m:] - 2 * x[m:-m] + x[:-2 * m]
        out.append((m * tau0_s, float(math.sqrt(np.mean(d * d) / (2 * (m * tau0_s) ** 2)))))
    return out


def holdover_s(limit_ns, offset0_ns, freq_ppb, drift_ppb_per_s=0.0):
    """Time for |offset0 + y t + D t^2 / 2| to reach limit (ns), from a residual frequency error y (ppb) and an
    ageing drift D (ppb per second)."""
    a, b, c = drift_ppb_per_s / 2, freq_ppb, offset0_ns - math.copysign(limit_ns, freq_ppb or 1.0)
    if abs(a) < 1e-15:
        return abs((math.copysign(limit_ns, b) - offset0_ns) / b) if b else math.inf
    disc = b * b - 4 * a * c
    roots = [(-b + s * math.sqrt(disc)) / (2 * a) for s in (1, -1)] if disc >= 0 else []
    pos = [r for r in roots if r > 0]
    return min(pos) if pos else math.inf


def compliance(offset_ns, limit_ns):
    o = np.abs(np.asarray(offset_ns))
    return {"max_abs_ns": float(o.max()), "share_within": float((o <= limit_ns).mean())}
