"""firm.careerpath -- what a move costs, and where a career goes (build of One Quant Book 17, chapter 28).

A move. A job pays a base and an expected annual award B, paid in `pay_month` for the previous year, of which a share d
is deferred into tranches vesting over V years at the following payment dates. In the steady state the unvested
deferred awards are worth d B (V + 1) / 2 whatever the month. Resigning in month m (1 = January) forfeits, as a bad
leaver: the unvested deferrals; the previous year's award if it has not been paid yet (m <= pay_month); and the award
accruing for the current year. The person is then out of the market for the notice period, any further garden leave and
any non-compete (paid or not), during which no award accrues. A new employer buys out the forfeited awards with
probability q (a share s of them). The move is neutral when a raise on the new package, over a horizon of H years,
repays the net cost. The notice, leave and non-compete lengths are inputs; Book 16's firm.gardenleave values them from
the employer's side, and firm.payoffer the package from the employee's side.

A career. A Markov chain over job states with annual transition probabilities and a pay per state (every number the
caller's, labelled as assumptions) gives the distribution of pay paths.

API (stable):
    Job(base, award, deferral, vest_years, pay_month)
    unvested(job) ; forfeited(job, month) -> dict(deferred, unpaid, accrued, total)
    move_cost(job, month, notice_m, garden_m, noncompete_m, paid_noncompete, q, s) -> dict
    breakeven_raise(job, month, horizon_y, **move) -> raise as a share of base + award
    Chain(states, P, pay) ; simulate(chain, start, years, n, rng) -> (n, years) state indices ; pay_paths(chain, states)
    spinouts(graph) -> edges of firm.lineage whose relation names a spin-out
"""
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Job:
    base: float
    award: float
    deferral: float
    vest_years: int
    pay_month: int          # month (1-12) in which the previous year's award is paid


def unvested(job):
    return job.deferral * job.award * (job.vest_years + 1) / 2.0


def forfeited(job, month):
    """Value forfeited by resigning at the start of `month` (1-12) as a bad leaver."""
    unpaid = job.award if month <= job.pay_month else 0.0
    accrued = job.award * (month - 1) / 12.0
    d = unvested(job)
    return {"deferred": d, "unpaid": unpaid, "accrued": accrued, "total": d + unpaid + accrued}


def move_cost(job, month, notice_m, garden_m=0, noncompete_m=0, paid_noncompete=True, q=0.0, s=1.0):
    f = forfeited(job, month)
    out_m = notice_m + garden_m + noncompete_m
    lost_award = job.award * out_m / 12.0
    lost_base = 0.0 if paid_noncompete else job.base * noncompete_m / 12.0
    buyout = q * s * (f["deferred"] + f["unpaid"])
    total = f["total"] + lost_award + lost_base - buyout
    return {"forfeited": f["total"], "out_months": out_m, "lost_award": lost_award, "lost_base": lost_base,
            "buyout": buyout, "net": total}


def breakeven_raise(job, month, horizon_y, **move):
    return move_cost(job, month, **move)["net"] / ((job.base + job.award) * horizon_y)


@dataclass(frozen=True)
class Chain:
    states: tuple
    P: tuple                # rows: from state; columns: to state; each row sums to one
    pay: tuple              # annual pay in each state


def simulate(chain, start, years, n, rng):
    P = np.asarray(chain.P, float)
    if not np.allclose(P.sum(axis=1), 1.0):
        raise ValueError("rows of P must sum to one")
    cum = P.cumsum(axis=1)
    s = np.full(n, chain.states.index(start))
    out = np.empty((n, years), int)
    for t in range(years):
        out[:, t] = s
        u = rng.random(n)
        s = (u[:, None] > cum[s]).sum(axis=1)
    return out


def pay_paths(chain, states):
    return np.asarray(chain.pay, float)[states]


def spinouts(graph):
    return [e for e in graph.edges if "spun out" in e.relation or "spin-out" in e.relation]
