"""Chapter 29 of Book 6: a risk engine. A 1,000-trade book (swaps, swaptions, EUR/USD options) on the
Treasury curve of 23 September 2026, revalued under the 250 most recent daily historical scenarios (Treasury
par-yield changes, treated as zero-rate moves, and relative EUR/USD moves) by full revaluation, a revaluation
grid and a delta-gamma approximation, through Book 5's pricing library; VaR and ES by node of the risk
hierarchy, Euler contributions, limits, and the cost of each method in pricing calls."""
import datetime as dt
import functools
import pathlib
import sys

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/riskengine"))
from firm_riskengine import (  # noqa: E402
    METHODS,
    PILLARS,
    Counter,
    IRSwap,
    PillarCurve,
    Swaption,
    Trade,
    add_years,
    aggregate,
    check_limits,
    euler_es,
    fp,
    historical_scenarios,
    planned_revaluation,
    risk_report,
)

DATA = ROOT / "data/rates-credit-risk"
COLS = ["y1", "y2", "y3", "y5", "y7", "y10", "y20", "y30"]
N_SCEN = 250


@functools.cache
def history() -> pd.DataFrame:
    y = pd.read_csv(DATA / "treasury_par_yields.csv", parse_dates=["date"]).set_index("date")[COLS]
    fx = pd.read_csv(DATA / "ecb_fx_2016_2026.csv", parse_dates=["date"]).set_index("date")["usd_per_eur"]
    return y.join(fx, how="inner").dropna()


def market() -> fp.MarketData:
    h = history()
    last = h.iloc[-1]
    asof = h.index[-1].date()
    curve = PillarCurve(asof, tuple(float(last[c]) / 100.0 for c in COLS))
    return fp.MarketData(asof=asof, spots={"EURUSD": float(last["usd_per_eur"])}, curves={"USD": curve},
                         dividends={"EURUSD": fp.Dividends(div_yield=0.02)},
                         vols={"EURUSD": fp.FlatVol(0.08), "USD": fp.FlatVol(0.0090)},
                         funding={"EURUSD": "USD"})


@functools.cache
def scenarios(h: int = 1) -> tuple:
    """The N_SCEN most recent (overlapping) h-day changes of the factors."""
    x = history().iloc[-(N_SCEN + h):]
    dy = (x[COLS].shift(-h) - x[COLS]).iloc[:-h].to_numpy() / 100.0
    dfx = (x["usd_per_eur"].shift(-h) / x["usd_per_eur"] - 1.0).iloc[:-h].to_numpy()[:, None]
    factors = [f"CURVE:USD:{p}" for p in PILLARS] + ["SPOT:EURUSD"]
    names = [d.date().isoformat() for d in x.index[:-h]]
    return tuple(historical_scenarios(names, factors, np.hstack([dy, dfx]), [False] * 8 + [True]))


def par_rate(md: fp.MarketData, years: int) -> float:
    dfs = [md.df("USD", add_years(md.asof, i)) for i in range(1, years + 1)]
    return (1.0 - dfs[-1]) / sum(dfs)


@functools.cache
def book(n: int = 1000, seed: int = 29) -> tuple[Trade, ...]:
    """600 swaps, 200 swaptions, 200 EUR/USD options (short-dated ones mostly sold)."""
    rng = np.random.default_rng(seed)
    md = market()
    out = []
    for i in range(int(0.6 * n)):
        y = int(rng.choice([2, 3, 5, 7, 10, 20, 30]))
        k = par_rate(md, y) + float(rng.normal(0, 0.005))
        inst = IRSwap(id=f"SW{i}", underlying="USD", currency="USD", notional=float(rng.uniform(10, 100)) * 1e6,
                      years=y, fixed=k, payer=bool(rng.random() < 0.5))
        out.append(Trade(f"SW{i}", inst, 1.0, ("Firm", "Rates", "Swaps")))
    for i in range(int(0.2 * n)):
        e, t = int(rng.choice([1, 2, 3, 5])), int(rng.choice([5, 10]))
        exp = add_years(md.asof, e)
        inst = Swaption(id=f"SO{i}", underlying="USD", currency="USD", notional=float(rng.uniform(20, 200)) * 1e6,
                        expiry=exp, tenor=t, strike=0.045 + float(rng.normal(0, 0.004)), payer=bool(rng.random() < 0.5))
        out.append(Trade(f"SO{i}", inst, 1.0 if rng.random() < 0.4 else -1.0, ("Firm", "Rates", "Options")))
    s = md.spots["EURUSD"]
    for i in range(n - len(out)):
        days = int(rng.choice([7, 14, 30, 60, 90, 180, 365]))
        short = days <= 30
        inst = fp.EuropeanOption(id=f"FX{i}", underlying="EURUSD", currency="USD",
                                 notional=float(rng.uniform(10, 60)) * 1e6,
                                 strike=round(s * (1 + float(rng.normal(0, 0.01))), 4),
                                 expiry=md.asof + dt.timedelta(days=days), right="C" if rng.random() < 0.5 else "P")
        q = -1.0 if (short and rng.random() < 0.85) or (not short and rng.random() < 0.5) else 1.0
        out.append(Trade(f"FX{i}", inst, q, ("Firm", "FX", "Short-dated" if short else "Long-dated")))
    return tuple(out)


PLAN = {("Firm",): "grid", ("Firm", "Rates", "Options"): "full", ("Firm", "FX", "Long-dated"): "delta-gamma"}


@functools.cache
def revaluations(h: int = 1) -> dict:
    """P&L matrices and pricing calls of full, grid, delta-gamma and the planned revaluation."""
    md, sc, b = market(), scenarios(h), book()
    out = {}
    for name, f in METHODS.items():
        c = Counter()
        out[name] = {"pnl": f(b, md, sc, c), "calls": c.calls}
    c = Counter()
    out["plan"] = {"pnl": planned_revaluation(b, md, sc, c, PLAN), "calls": c.calls}
    return out


def reports(h: int = 1) -> dict:
    paths = [t.path for t in book()]
    return {k: risk_report(aggregate(v["pnl"], paths)) for k, v in revaluations(h).items()}


def errors(h: int = 1) -> dict:
    """Relative VaR and ES error of each approximation against full revaluation, per node."""
    r = reports(h)
    return {m: {node: {"var": r[m][node]["var"] / r["full"][node]["var"] - 1.0,
                       "es": r[m][node]["es"] / r["full"][node]["es"] - 1.0} for node in r["full"]}
            for m in ("grid", "delta-gamma", "plan")}


def worst(h: int = 1) -> dict:
    """Largest absolute relative VaR error over the nodes, per method."""
    return {m: max(abs(v["var"]) for v in e.values()) for m, e in errors(h).items()}


def euler(h: int = 10) -> dict:
    agg = aggregate(revaluations(h)["full"]["pnl"], [t.path for t in book()])
    return euler_es(agg[("Firm",)], {k: v for k, v in agg.items() if len(k) == 2})


LIMITS = {("Firm",): 60e6, ("Firm", "Rates"): 50e6, ("Firm", "FX"): 20e6, ("Firm", "FX", "Short-dated"): 12e6}


def limits(h: int = 10) -> list:
    return check_limits(reports(h)["full"], LIMITS)


def wall_clock(calls: int, trades: int = 1000, scale_trades: int = 50_000, ms_per_call: float = 20.0,
               cores: int = 16) -> float:
    """Hours to run a method on a book `scale_trades / trades` times larger, at a cost per pricing call."""
    return calls * scale_trades / trades * ms_per_call / 1000.0 / cores / 3600.0
