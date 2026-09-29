"""One Quant Book 16, chapter 8: managing a book through drawdown.

Strategies with a Sharpe ratio of 1 and 10 per cent volatility on their capital, over ten years. Half the
population is alive throughout; the other half breaks at the start of year 4 (day 756), its Sharpe ratio falling
to 0 (the edge is gone, the risk is not). Rules: a 10 per cent stop-loss; a ladder that halves at 7.5 and stops at
12.5 per cent; a time stop after 18 months without a new high; a posterior rule that stops when the probability of
a break exceeds 0.9 (hazard of breaking: once in five years).
"""
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/ddrules"))
import firm_ddrules as dd  # noqa: E402

SR, VOL, SR_DEAD, YEARS = 1.0, 0.10, 0.0, 10
T = YEARS * dd.DAYS
BREAK = 3 * dd.DAYS
HAZARD = 1 / (5 * dd.DAYS)
CHARGE = 0.02        # capital charge per year run at full size, a fraction of capital (15% of 13%)
RULES = {"stop-loss 10%": dd.Rule("stop", 0.10), "ladder 7.5 / 12.5%": dd.Rule("ladder", 0.075, 0.125),
         "time stop 18 months": dd.Rule("time", 18 * 21), "posterior > 0.9": dd.Rule("posterior", 0.9)}


def population(n=2000, seed=8):
    rng = np.random.default_rng(seed)
    alive = dd.paths(n, T, SR, VOL, rng)
    dead = dd.paths(n, T, SR, VOL, rng, break_day=BREAK, sr_dead=SR_DEAD)
    return alive, dead


def table(n=2000, seed=8, charge=CHARGE):
    alive, dead = population(n, seed)
    pa = dd.posterior(alive, SR, SR_DEAD, VOL, HAZARD)
    pd = dd.posterior(dead, SR, SR_DEAD, VOL, HAZARD)
    return {k: dd.evaluate(r, alive, dead, BREAK, pa, pd, charge) for k, r in RULES.items()}


def at_drawdown(level=0.08, n=2000, seed=8):
    """Mean posterior probability of a break on the day each path's drawdown first exceeds `level`, for alive paths
    and for broken paths whose first such day falls after the break."""
    alive, dead = population(n, seed)
    out = {}
    for name, ret in (("alive", alive), ("broken", dead)):
        post = dd.posterior(ret, SR, SR_DEAD, VOL, HAZARD)
        eq = np.cumsum(ret, 1)
        ddn = np.maximum.accumulate(np.maximum(eq, 0.0), 1) - eq
        hit = ddn > level
        first = np.where(hit.any(1), hit.argmax(1), -1)
        ok = first >= (BREAK if name == "broken" else 0)
        out[name] = (float(post[ok, first[ok]].mean()), float(ok.mean()))
    return out


def lorden(arl_years=10.0, sr_dead=SR_DEAD, sr=SR):
    return dd.cusum_delay(sr, sr_dead, arl_years * dd.DAYS) / dd.DAYS


def drawdown_quantiles(n=2000, seed=8):
    """Maximum drawdown over ten years of a strategy that never breaks: median and 90th percentile."""
    alive, _ = population(n, seed)
    eq = np.cumsum(alive, 1)
    mdd = (np.maximum.accumulate(np.maximum(eq, 0.0), 1) - eq).max(1)
    return float(np.median(mdd)), float(np.quantile(mdd, 0.9))


def examples(seed=18):
    """One alive and one broken path (the broken one breaking at day 756), with their posteriors."""
    rng = np.random.default_rng(seed)
    a = dd.paths(1, T, SR, VOL, rng)
    b = dd.paths(1, T, SR, VOL, rng, break_day=BREAK, sr_dead=SR_DEAD)
    return (np.cumsum(a[0]), dd.posterior(a, SR, SR_DEAD, VOL, HAZARD)[0],
            np.cumsum(b[0]), dd.posterior(b, SR, SR_DEAD, VOL, HAZARD)[0])
