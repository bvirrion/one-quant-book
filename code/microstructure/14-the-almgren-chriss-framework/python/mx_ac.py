"""One Quant Book 10, chapter 14: the Almgren-Chriss schedule, on paper and in the simulated market.

    BLOCK                          the chapter's block: sell 1,000,000 shares of a 50-dollar stock trading 10 million
                                   a day with 2% daily volatility, by the close; temporary impact linearised from the
                                   square-root law at 10% participation
    block_study(lam)               the optimal schedule's urgency, expected cost, standard deviation, time to sell
                                   95%, and the certainty-equivalent penalty of a schedule twice too patient or twice
                                   too hurried
    ScheduleAgent                  an execution agent that sells, at each interval, down to a scheduler's target
    sim_study(kts, seeds)          20,000 shares sold over 30 minutes in firm.agentmkt's market with urgencies kT;
                                   realised shortfall mean and standard deviation against the model's, with sigma and
                                   eta estimated from the same runs (cached)
All deterministic (fixed seeds).
"""
from __future__ import annotations

import functools
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for c in ("acexec", "agentmkt", "exchsim"):
    sys.path.insert(0, str(ROOT / "code" / "firm" / c))
from firm_acexec import ACScheduler, cost_var, discrete, kappa, time_to  # noqa: E402
from firm_agentmkt import SEC, T0, PopulationConfig, session  # noqa: E402
from firm_exchsim import Agent, Order  # noqa: E402

PRICE, ADV, DAILY_VOL, X = 50.0, 10_000_000, 0.02, 1_000_000
SIGMA = PRICE * DAILY_VOL                                    # dollars per share per square root of a day
ETA = 0.8 * DAILY_VOL * math.sqrt(0.1) * PRICE / (0.1 * ADV)  # dollars per share per (share a day)
N = 390                                                       # one-minute intervals


def _ce(holdings, lam):
    e, v = cost_var(holdings, 1.0, 0.0, ETA, SIGMA)
    return e, math.sqrt(v), e + lam * v


def block_study(lam: float = 1e-6) -> dict:
    k = kappa(ETA, SIGMA, lam)
    opt = discrete(X, 1.0, N, ETA, SIGMA, lam)
    e, sd, u = _ce(opt, lam)
    out = {"kappa": k, "cost": e, "sd": sd, "utility": u, "t95_hours": 6.5 * time_to(0.95, k, 1.0),
           "twap": _ce(discrete(X, 1.0, N, ETA, SIGMA, 0.0), lam)}
    t = np.arange(N + 1) / N
    for name, f in (("patient", 0.5), ("hurried", 2.0)):
        h = ACScheduler(X, 1.0, f * k).targets(t)
        out[name] = _ce(h, lam)
    return out


class ScheduleAgent(Agent):
    name = "exec"

    def __init__(self, scheduler, start_ns: int, interval_ns: int, n: int):
        self.s, self.start, self.dt, self.n = scheduler, start_ns, interval_ns, n
        self.sold = 0

    def on_start(self, ctx):
        for j in range(self.n):
            ctx.set_timer(self.start + j * self.dt - ctx.now_ns, j)

    def on_timer(self, ctx, j):
        target = float(self.s.targets([(j + 1) / self.n])[0])
        q = int(round((self.s.x - target - self.sold) / 100)) * 100
        if q > 0:
            ctx.send(Order(side="S", qty=q, price=0, tif="I"))
            self.sold += q


MARKET = PopulationConfig(lo_rate=3.0, near=0.3, cancel=0.05, depth=10, fund=0.05)
KTS = (0.0, 2.0, 6.0)
QTY, HORIZON_S, START_S = 20_000, 1800.0, 300.0


@functools.cache
def sim_study(kts=KTS, seeds=tuple(range(1, 9))) -> dict:
    out = {}
    slips, rates = [], []
    sig2 = []
    for kt in kts:
        sf = []
        for seed in seeds:
            sch = ACScheduler(QTY, 1.0, kt)
            res, _ = session(MARKET, START_S + HORIZON_S + 60, seed,
                             agents=[ScheduleAgent(sch, T0 + int(START_S * SEC), int(HORIZON_S / 30 * SEC), 30)])
            tp = res.tape()
            top = tp.top
            ok = (top["bid"] > 0) & (top["ask"] > 0)
            tt, mid = top["t"][ok], 0.5 * (top["bid"][ok] + top["ask"][ok])

            def m(t, tt=tt, mid=mid):
                return float(mid[max(np.searchsorted(tt, t, side="right") - 1, 0)])
            fills = res.agents["exec"].fills
            q = np.array([f[5] for f in fills], float)
            p = np.array([f[4] for f in fills], float) / 100.0             # ticks
            ft = np.array([(f[0] - T0) / SEC for f in fills])
            m0 = m(START_S - 1e-6)
            sf.append(float((m0 - p) @ q / QTY))                          # ticks per share
            if kt == kts[0]:
                g = np.arange(0.0, START_S + HORIZON_S, 60.0)
                sig2.append(float(np.var(np.diff([m(x) for x in g])) / 60.0))
            for tk in np.unique(np.round(ft, 3)):
                sel = np.round(ft, 3) == tk
                slips.append(float((m(tk - 1e-6) - p[sel]) @ q[sel] / q[sel].sum()))
                rates.append(float(q[sel].sum() / (HORIZON_S / 30)))
        sd = float(np.std(sf, ddof=1))
        out[kt] = {"mean": float(np.mean(sf)), "sd": sd, "se": sd / math.sqrt(len(sf))}
    eta = float(np.polyfit(rates, slips, 1)[0])                           # ticks per share per (share a second)
    sigma = math.sqrt(float(np.mean(sig2)))                              # ticks per share per root second
    for kt in kts:
        h = ACScheduler(QTY, HORIZON_S, kt / HORIZON_S).targets(np.linspace(0, HORIZON_S, 31))
        e, v = cost_var(h, HORIZON_S, 0.0, eta, sigma)
        out[kt] |= {"model_mean": e / QTY, "model_sd": math.sqrt(v) / QTY}
    out["eta"], out["sigma"] = eta, sigma
    return out
