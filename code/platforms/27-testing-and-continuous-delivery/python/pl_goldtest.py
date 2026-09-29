"""Testing and continuous delivery (One Quant Book 15, chapter 27).

Golden values of Book 5's pricing library (firm.pricing) are frozen over a portfolio of sixty instruments -- European
options (analytic), American puts (finite differences), Asian calls (Monte Carlo) and down-and-out calls (closed
form) -- each with a tolerance derived from its engine's own error: a relative epsilon for closed forms, a multiple k
of the grid's convergence gap (200 against 400 points) for the PDE, a multiple k of the Monte Carlo standard error
(estimated from eight independent seeds) for Monte Carlo. Five builds are then compared with the golden file: a new
Monte Carlo seed (noise, no regression), an ACT/360 day count, a sign error in the rate of puts, an Asian average that
drops its last fixing, and a finer PDE grid (a genuine improvement). For each k: the share of affected instruments
flagged, and the probability that noise alone fails the test. Release trains, a deployment consistency check and the
pipeline's measured stage times (bench_goldtest.py) complete the chapter.
"""
from __future__ import annotations

import dataclasses
import datetime as dt
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for c in ("goldtest", "pricing"):
    sys.path.insert(0, str(ROOT / "code/firm" / c))
import firm_goldtest as G  # noqa: E402
import firm_pricing as FP  # noqa: E402

ASOF = dt.date(2026, 9, 28)
N_PATHS, N_SE_SEEDS = 20_000, 8
KS = (1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0, 6.0)
CHANGES = ("seed", "day count", "put sign", "Asian fixing", "finer grid")


def market(rate: float = 0.03) -> FP.MarketData:
    return FP.MarketData(ASOF, {"A": 100.0}, {"USD": FP.FlatCurve(rate, ASOF)}, vols={"A": FP.FlatVol(0.25)})


def _d(days: int) -> dt.date:
    return ASOF + dt.timedelta(days=days)


def portfolio(seed: int = 27) -> dict:
    """key -> (instrument, engine)."""
    rng = np.random.default_rng(seed)
    out = {}
    for i in range(20):
        right = "C" if i % 2 == 0 else "P"
        k, days = float(rng.integers(8, 13) * 10), int(rng.integers(90, 1100))
        out[f"european:{i:02d}"] = (FP.EuropeanOption(id=f"E{i}", underlying="A", currency="USD", strike=k,
                                                       expiry=_d(days), right=right), FP.AnalyticEngine())
    for i in range(10):
        k, days = float(rng.integers(9, 12) * 10), int(rng.integers(90, 1100))
        out[f"american:{i:02d}"] = (FP.EuropeanOption(id=f"U{i}", underlying="A", currency="USD", strike=k,
                                                       expiry=_d(days), right="P", exercise="american"),
                                    FP.PDEEngine())
    for i in range(20):
        k, months = float(rng.integers(9, 12) * 10), int(rng.integers(6, 25))
        fix = tuple(_d(round(30.4 * (j + 1))) for j in range(months))
        out[f"asian:{i:02d}"] = (FP.AsianOption(id=f"S{i}", underlying="A", currency="USD", strike=k, expiry=fix[-1],
                                                right="C", fixing_dates=fix), FP.MonteCarloEngine(n_paths=N_PATHS))
    for i in range(10):
        k, days = float(rng.integers(9, 12) * 10), int(rng.integers(90, 750))
        out[f"barrier:{i:02d}"] = (FP.BarrierOption(id=f"B{i}", underlying="A", currency="USD", strike=k,
                                                    expiry=_d(days), right="C", barrier=80.0, kind="DO",
                                                    monitoring="continuous"), FP.ClosedFormEngine())
    return out


def pv(inst, eng, md=None) -> float:
    return FP.price(inst, md or market(), engine=eng).pv


def tolerance(key: str, inst, eng, k: float) -> float:
    """The engine's own error, times k (closed forms: a relative 1e-10)."""
    if isinstance(eng, FP.MonteCarloEngine):
        xs = [pv(inst, dataclasses.replace(eng, seed_offset=100 + j))
              for j in range(N_SE_SEEDS)]
        return k * float(np.std(xs, ddof=1))
    if isinstance(eng, FP.PDEEngine):
        return k * abs(pv(inst, eng) - pv(inst, FP.PDEEngine(m=400, n_t=400)))
    return 1e-10 * max(1.0, abs(pv(inst, eng)))


def errors(port: dict) -> dict:
    """Each instrument's error unit (the tolerance for k = 1)."""
    return {key: tolerance(key, inst, eng, 1.0) for key, (inst, eng) in port.items()}


def golden(port: dict, errs: dict, k: float) -> G.GoldenStore:
    store = G.GoldenStore()
    for key, (inst, eng) in port.items():
        closed = not isinstance(eng, FP.MonteCarloEngine | FP.PDEEngine)
        store.put(G.Golden(key, pv(inst, eng), errs[key] if closed else k * errs[key],
                           {"engine": eng.name, "k": k, "library": "firm.pricing"}))
    return store


def _stretch(d: dt.date) -> dt.date:
    return ASOF + dt.timedelta(days=round((d - ASOF).days * 365 / 360))


def build(change: str, key: str, inst, eng, seed: int = 1) -> float:
    """The new build's price of one instrument, for each planted change."""
    if change == "seed" and isinstance(eng, FP.MonteCarloEngine):
        return pv(inst, dataclasses.replace(eng, seed_offset=seed))
    if change == "day count":
        kw = {"expiry": _stretch(inst.expiry)}
        if isinstance(inst, FP.AsianOption):
            kw["fixing_dates"] = tuple(_stretch(x) for x in inst.fixing_dates)
        return pv(dataclasses.replace(inst, **kw), eng)
    if change == "put sign" and getattr(inst, "right", "") == "P":
        return pv(inst, eng, market(rate=-0.03))
    if change == "Asian fixing" and isinstance(inst, FP.AsianOption):
        return pv(dataclasses.replace(inst, fixing_dates=inst.fixing_dates[:-1]), eng)
    if change == "finer grid" and isinstance(eng, FP.PDEEngine):
        return pv(inst, FP.PDEEngine(m=400, n_t=400))
    return pv(inst, eng)


def experiment(port: dict | None = None, seeds: int = 40) -> dict:
    """Base values, error units and each build's values; seeds 1..`seeds` for the noise build."""
    port = port or portfolio()
    base = {k: pv(i, e) for k, (i, e) in port.items()}
    errs = errors(port)
    builds = {c: {k: build(c, k, i, e) for k, (i, e) in port.items()} for c in CHANGES if c != "seed"}
    noise = [{k: build("seed", k, i, e, s) for k, (i, e) in port.items() if isinstance(e, FP.MonteCarloEngine)}
             for s in range(1, seeds + 1)]
    return {"port": port, "base": base, "errs": errs, "builds": builds, "noise": noise}


def rates(ex: dict, k: float, pinned: bool = False) -> dict:
    """For one k: share of affected instruments flagged per change, and the noise's per-instrument
    and per-run false-alarm rates. `pinned`: the seed is part of the build, so Monte Carlo values
    are compared at a closed form's tolerance (and a new seed is a change to approve)."""
    base, errs, port = ex["base"], ex["errs"], ex["port"]

    def tol(key):
        eng = port[key][1]
        if pinned and isinstance(eng, FP.MonteCarloEngine):
            return 1e-10 * max(1.0, abs(base[key]))
        closed = not isinstance(eng, FP.MonteCarloEngine | FP.PDEEngine)
        return errs[key] if closed else k * errs[key]
    out = {}
    for c, vals in ex["builds"].items():
        affected = [key for key in vals if abs(vals[key] - base[key]) > 1e-12]
        flagged = [key for key in affected if abs(vals[key] - base[key]) > tol(key)]
        out[c] = (len(flagged), len(affected))
    per_inst = [abs(run[key] - base[key]) > tol(key) for run in ex["noise"] for key in run]
    per_run = [any(abs(run[key] - base[key]) > tol(key) for key in run) for run in ex["noise"]]
    out["noise_instrument"] = float(np.mean(per_inst))
    out["noise_run"] = float(np.mean(per_run))
    asians = [key for key in port if key.startswith("asian")]
    dc = ex["builds"]["day count"]
    out["day_count_asian"] = (sum(abs(dc[key] - base[key]) > tol(key) for key in asians), len(asians))
    return out


def expected_cost(ex: dict, k: float, p_regression: float = 0.02, cost_miss: float = 500_000.0,
                  cost_false: float = 1_000.0) -> float:
    """Per run of the golden test: a false alarm costs an investigation; a regression in one
    Monte Carlo product (like the Asian-fixing bug, on one instrument) is missed with the share of
    such instruments the test does not flag, and costs `cost_miss` -- both costs are assumptions."""
    r = rates(ex, k)
    f, a = r["Asian fixing"]
    return (1 - p_regression) * r["noise_run"] * cost_false + p_regression * (1 - f / a) * cost_miss


def noise_theory(k: float) -> float:
    """Probability that two independent Monte Carlo estimates differ by more than k standard errors."""
    return math.erfc(k / 2)


# ------------------------------------------------------------ release trains and deployments
def arrivals(weeks: int = 52, per_week: float = 10.0, seed: int = 27) -> list[float]:
    rng = np.random.default_rng(seed)
    n = rng.poisson(per_week * weeks)
    return sorted(rng.uniform(0, 7 * weeks, n).tolist())


def trains() -> list[tuple]:
    a = arrivals()
    rows = []
    for cadence in (0, 1, 7, 14):
        s = G.release_train(a, cadence)
        rows.append((cadence, len(a), float(np.mean(s.lead_days)), float(np.mean(s.batch_sizes)), s.bisect_steps))
    return rows


def eight_servers() -> dict:
    """Seven hosts on the new build, one still on the old one: the hook's deployment."""
    new, old = {"router": "release 2", "flag": "new function"}, {"router": "release 1", "flag": "retired function"}
    cfg = {"venues": ["X"], "flag": "new function"}
    release = G.host_state(new, cfg)
    hosts = {f"router{i}": G.host_state(new, cfg) for i in range(1, 8)}
    hosts["router8"] = G.host_state(old, cfg)
    return {"release": release, "hosts": hosts, "refused": G.consistency(hosts, release)}


def doubled_paths(k: float = 5.0) -> dict:
    """Exercise 7: the portfolio with 40,000 Monte Carlo paths instead of 20,000."""
    port = {key: (i, dataclasses.replace(e, n_paths=2 * N_PATHS) if isinstance(e, FP.MonteCarloEngine) else e)
            for key, (i, e) in portfolio().items()}
    return rates(experiment(port), k)
