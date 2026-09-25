"""firm.basistrade -- a leveraged Treasury cash-futures basis book (build of One Quant Book 9, chapter 11).

The book is long cash Treasuries financed in repo and short the futures, earning the gap between the futures'
implied repo rate and the repo rate it pays (a spread s a year on the face held). Its daily mark also moves with a
mean-reverting deviation of the basis; a planted funding stress pushes the basis against the book (the cash
cheapens against the futures), raises the repo haircut and the futures margin, and lifts the repo rate for a few
days, after which the basis recovers over two months. Capital must cover the haircut on the bonds and the margin on
the futures; when it does not, the book sells bonds and buys back futures at the stressed basis, paying a cost, and
cannot buy them back until the stress ends. It re-levers to its target at each quarterly roll. NumPy only.

API (stable):
    BasisConfig(...)                           parameters of the trade, the market and the stress
    simulate_basis(cfg)                        dict of daily basis deviation, haircut, margin and extra repo
    run_book(sim, cfg, leverage)               dict of capital (T + 1,), face held (T + 1,), forced sales, P&L parts
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

YEAR = 252


@dataclass(frozen=True)
class BasisConfig:
    days: int = 5 * YEAR
    seed: int = 109
    spread: float = 0.002         # implied repo minus repo, a year, on the face held
    dev_sd: float = 0.0003        # sd of the basis deviation, per unit of face (3 cents per 100)
    dev_phi: float = 0.95         # its daily persistence
    haircut: float = 0.01         # repo haircut on the bonds
    margin: float = 0.01          # initial margin on the futures, per unit of face
    stress_start: int = 630       # day the funding stress begins (year 2.5)
    stress_days: int = 10
    jump: float = 0.006           # the basis moves against the book by this much (60 cents per 100)
    recover_days: int = 60        # and comes back over this many days after the stress
    haircut_stress: float = 0.03
    margin_stress: float = 0.03
    repo_spike: float = 0.01      # extra repo rate during the stress
    sale_cost: float = 0.001      # cost of a forced sale, per unit of face (10 cents per 100)
    roll_every: int = 63


def simulate_basis(cfg: BasisConfig | None = None) -> dict:
    cfg = cfg or BasisConfig()
    rng = np.random.default_rng(cfg.seed)
    T = cfg.days
    dev = np.empty(T + 1)
    dev[0] = 0.0
    for t in range(T):
        dev[t + 1] = cfg.dev_phi * dev[t] + cfg.dev_sd * math.sqrt(1 - cfg.dev_phi**2) * rng.standard_normal()
    a, b = cfg.stress_start, cfg.stress_start + cfg.stress_days
    shock = np.zeros(T + 1)
    ramp, back = cfg.jump * np.linspace(0.3, 1.0, b - a), cfg.jump * np.linspace(1.0, 0.0, cfg.recover_days)
    shock[a:b] = ramp[:max(0, min(b, T + 1) - a)]
    shock[b:b + cfg.recover_days] = back[:max(0, min(b + cfg.recover_days, T + 1) - b)]
    hair, marg, repo = np.full(T + 1, cfg.haircut), np.full(T + 1, cfg.margin), np.zeros(T + 1)
    hair[a:b + cfg.recover_days] = cfg.haircut_stress
    marg[a:b + cfg.recover_days] = cfg.margin_stress
    repo[a:b] = cfg.repo_spike
    return {"dev": dev, "shock": shock, "haircut": hair, "margin": marg, "repo": repo, "stress": (a, b)}


def run_book(sim: dict, cfg: BasisConfig | None = None, leverage: float = 20.0) -> dict:
    """Capital starts at 1; face held is leverage x capital, reset at each roll, cut when funding falls short."""
    cfg = cfg or BasisConfig()
    T = cfg.days
    mark = sim["dev"] + sim["shock"]                                   # a rise is a loss to the long basis
    cap, face = np.ones(T + 1), np.zeros(T + 1)
    face[0] = leverage
    carry, marks, funding, costs = np.zeros(T), np.zeros(T), np.zeros(T), np.zeros(T)
    forced, (a, b) = 0, sim["stress"]
    stressed = range(a, b + cfg.recover_days)
    for t in range(T):
        n = face[t]
        carry[t] = n * cfg.spread / YEAR
        marks[t] = -n * (mark[t + 1] - mark[t])
        funding[t] = -n * (1 - sim["haircut"][t]) * sim["repo"][t] / YEAR
        cap[t + 1] = cap[t] + carry[t] + marks[t] + funding[t]
        need = sim["haircut"][t + 1] + sim["margin"][t + 1]
        n_next = n
        if cap[t + 1] <= 0:
            n_next, cap[t + 1] = 0.0, 0.0
        elif cap[t + 1] < n * need:                                    # margin call: sell down to what capital funds
            n_next = cap[t + 1] / need
            costs[t] = -(n - n_next) * cfg.sale_cost
            cap[t + 1] += costs[t]
            n_next = max(cap[t + 1], 0.0) / need
            forced += 1
        if (t + 1) % cfg.roll_every == 0 and t + 1 not in stressed and cap[t + 1] > 0:
            n_next = leverage * cap[t + 1] if leverage * need <= 1 else cap[t + 1] / need
        face[t + 1] = n_next
    return {"capital": cap, "face": face, "forced": forced, "carry": carry, "marks": marks, "funding": funding,
            "costs": costs}
