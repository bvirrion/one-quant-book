"""firm.opsmetrics -- operations metrics: breaks, their queue, fails and their cost, collateral calls, key risk
indicators (build of One Quant Book 16, chapter 13).

Breaks arrive at rate lam (an hour) and are worked by c people, each resolving at rate mu: an M/M/c queue, whose
stationary law is computed with firm.queues (One Quant Book 4) on a truncated birth-death chain. A break is late if
its time in the system (wait plus work) exceeds the deadline D set by the settlement cycle; a late break may become a
settlement fail, charged at a penalty rate (basis points a day of the trade's value, an input) plus an internal cost.

API (stable):
    mmc_stationary(lam, mu, c, n_max) ; p_wait(lam, mu, c) ; erlang_c(lam, mu, c)   (closed form, for checks)
    p_late(lam, mu, c, D) ; staff_for(lam, mu, D, target) ; ageing(lam, mu, c, edges)
    fail_cost(n_fails, value, rate_bp, days, internal)
    Csa(threshold, mta) ; call(exposure, held, csa) ; disputed(ours, theirs, tolerance)
    kri(value, amber, red) -> "green" | "amber" | "red" ; report(metrics, limits) -> list of (name, value, status)
"""
import math
import pathlib
import sys
from dataclasses import dataclass

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "queues"))
import firm_queues as fq  # noqa: E402


def mmc_stationary(lam, mu, c, n_max=None):
    """Stationary law of the number of breaks in the system (M/M/c, truncated at n_max)."""
    if lam >= c * mu:
        raise ValueError("unstable queue: lam >= c mu")
    n_max = n_max or int(c + 60 * max(1.0, lam / mu))
    rates = np.zeros((n_max + 1, n_max + 1))
    for n in range(n_max):
        rates[n, n + 1] = lam
        rates[n + 1, n] = min(n + 1, c) * mu
    return fq.stationary(fq.generator(rates))


def p_wait(lam, mu, c):
    """Probability that an arriving break waits (PASTA: the stationary probability of c or more in the system)."""
    return float(mmc_stationary(lam, mu, c)[c:].sum())


def erlang_c(lam, mu, c):
    a = lam / mu
    rho = a / c
    top = a ** c / math.factorial(c) / (1 - rho)
    return top / (sum(a ** k / math.factorial(k) for k in range(c)) + top)


def p_late(lam, mu, c, D):
    """P(wait + work > D) for FCFS M/M/c: the wait is 0 with prob 1 - C, else exponential at rate c mu - lam."""
    C = p_wait(lam, mu, c)
    a = c * mu - lam
    tail_s = math.exp(-mu * D)
    tail_sum = math.exp(-mu * D) * (1 + mu * D) if abs(a - mu) < 1e-12 else \
        (a * math.exp(-mu * D) - mu * math.exp(-a * D)) / (a - mu)
    return (1 - C) * tail_s + C * tail_sum


def staff_for(lam, mu, D, target):
    """The smallest team that resolves a share `target` of breaks within D; none can if the work alone is too long."""
    if math.exp(-mu * D) > 1 - target:
        raise ValueError("target unreachable: the work time alone exceeds D too often")
    c = int(math.floor(lam / mu)) + 1
    while 1 - p_late(lam, mu, c, D) < target:
        c += 1
    return c


def ageing(lam, mu, c, edges):
    """Share of breaks resolved within each ageing bucket [edges[i], edges[i+1]) hours; the last bucket is open."""
    cdf = [0.0] + [1 - p_late(lam, mu, c, e) for e in edges[1:]] + [1.0]
    return [cdf[i + 1] - cdf[i] for i in range(len(edges))]


def fail_cost(n_fails, value, rate_bp, days, internal=0.0):
    return n_fails * (value * rate_bp * 1e-4 * days + internal)


@dataclass(frozen=True)
class Csa:
    threshold: float = 0.0
    mta: float = 0.0


def call(exposure, held, csa):
    """Collateral to call (positive) or return (negative) under a CSA's threshold and minimum transfer amount."""
    need = max(exposure - csa.threshold, 0.0) - held
    return need if abs(need) >= csa.mta else 0.0


def disputed(ours, theirs, tolerance):
    """A call is disputed when the two valuations differ by more than the tolerance (a fraction of the larger)."""
    return abs(ours - theirs) > tolerance * max(abs(ours), abs(theirs), 1e-12)


def kri(value, amber, red):
    """Traffic light of a key risk indicator; red below amber means lower values are worse (e.g. affirmation rate)."""
    if red < amber:
        return "red" if value <= red else ("amber" if value <= amber else "green")
    return "red" if value >= red else ("amber" if value >= amber else "green")


def report(metrics, limits):
    return [(k, v, kri(v, *limits[k])) for k, v in metrics.items()]
