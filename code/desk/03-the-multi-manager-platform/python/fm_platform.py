"""One Quant Book 16, chapter 3: the multi-manager platform.

The chapter's platform (illustrative): 50 pods, each with a Sharpe ratio of 1.0 and a volatility of 20 per cent
a year on its share of the fund's capital, pairwise correlation 0.1 through one shared factor; teams paid 20 per
cent of their own pod's profit with losses carried forward; pass-through costs of 3 per cent a year per pod and 1
per cent for the platform; a 20 per cent performance allocation to the manager. Twenty years, twenty seeds.
"""
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/podshop"))
import firm_podshop as ps  # noqa: E402

N, YEARS, SR, VOL, RHO = 50, 20, 1.0, 0.20, 0.10
TERMS = ps.Terms(payout_rate=0.20, pod_cost=0.03, platform_cost=0.01, mgr_perf=0.20)
SEEDS = range(1, 21)
FIRE = 0.10          # a team that loses more than 10 per cent of its capital in a year is replaced


def sim(seed, n=N, years=YEARS, sr=SR, vol=VOL, rho=RHO, beta=None):
    return ps.pods(n, years, sr, vol, rho, np.random.default_rng(seed), beta=beta)


def annuals(seeds=SEEDS, **kw):
    return [ps.annual(sim(s, **kw)["daily"]) for s in seeds]


def waterfall(seeds=SEEDS, terms=TERMS, fire=FIRE, **kw):
    """Mean waterfall per unit of fund capital (pods equal-weighted), over all seeds' years."""
    ws = [ps.waterfall(a, terms, fire) for a in annuals(seeds, **kw)]
    keys = ("gross", "payouts", "costs", "manager", "investor")
    out = {k: float(np.mean([w[k] for w in ws])) for k in keys}
    out["loss_years"] = sum(w["loss_years"] for w in ws)
    out["years"] = len(ws) * YEARS if "years" not in kw else len(ws) * kw["years"]
    return out


def classic(seeds=SEEDS, mgmt=0.02, perf=0.20, **kw):
    cs = [ps.classic(a, mgmt, perf) for a in annuals(seeds, **kw)]
    return {k: float(np.mean([c[k] for c in cs])) for k in ("gross", "fees", "investor")}


def netting_share(seeds=SEEDS, rate=0.20, carry=True, fire=FIRE, **kw):
    """Netting cost per unit of fund capital, and as a share of gross profit."""
    anns = annuals(seeds, **kw)
    nc = np.mean([ps.netting_cost(a, rate, carry, fire).mean() / a.shape[1] for a in anns])
    gross = np.mean([a.mean() for a in anns])
    return float(nc), float(nc / gross)


def netting_closed_form(sr, vol=VOL, rate=0.20):
    """Per pod, one year, no carry-forward, a fund that is always profitable: rate * (E[max(X,0)] - E[X])."""
    mu = sr * vol
    return rate * (ps.expected_positive(mu, vol) - mu)


def netting_vs_sr(srs=(0.25, 0.5, 0.75, 1.0, 1.5, 2.0), seeds=SEEDS):
    """Netting cost as a share of gross profit: simulated (carry-forward, teams replaced) and closed form."""
    return [(s, netting_share(seeds, sr=s)[1], netting_closed_form(s) / (s * VOL)) for s in srs]


def fund_stats(daily):
    f = daily.mean(1)
    mu, sd = f.mean() * 252, f.std() * math.sqrt(252)
    return mu, sd, mu / sd


def overlay_effect(seeds=SEEDS):
    """Fund volatility and Sharpe ratio before and after hedging the shared factor."""
    before, after = [], []
    for s in seeds:
        x = sim(s)
        before.append(fund_stats(x["daily"]))
        h = ps.overlay(x["daily"], x["beta"], x["factor"])
        after.append((h.mean() * 252, h.std() * math.sqrt(252), h.mean() / h.std() * math.sqrt(252)))
    return np.mean(before, 0), np.mean(after, 0)


def ladder_effect(cut=0.10, stop=0.15, seeds=SEEDS):
    """Share of pod-years cut and stopped, and the fund's mean return and volatility with and without the ladder."""
    cuts = stops = 0
    base, lad = [], []
    for s in seeds:
        d = sim(s)["daily"]
        out, ev = ps.ladder(d, cut, stop)
        cuts += sum(e[0] == "cut" for e in ev)
        stops += sum(e[0] == "stop" for e in ev)
        base.append(fund_stats(d))
        lad.append(fund_stats(out))
    py = len(list(seeds)) * YEARS * N
    return {"cut_share": cuts / py, "stop_share": stops / py, "base": np.mean(base, 0), "ladder": np.mean(lad, 0)}


def fund_sharpe(sr, n, rho):
    """Sharpe ratio of n equal-weighted pods with Sharpe ratio sr, equal volatility and pairwise correlation rho."""
    return sr * math.sqrt(n / (1 + (n - 1) * rho))


def diversification_table(ns=(10, 25, 50, 100), rhos=(0.05, 0.1, 0.2), sr=1.0):
    return {(n, r): fund_sharpe(sr, n, r) for n in ns for r in rhos}
