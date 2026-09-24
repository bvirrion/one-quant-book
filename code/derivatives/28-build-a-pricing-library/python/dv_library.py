"""Build: a pricing library (Book 5, Chapter 28): a small book priced through one call, cross-engine checks, bucketed
vega by bump-and-reprice, the Monte Carlo noise in one node with and without common random numbers, and a ten-scenario
grid."""
import datetime as dt
import functools
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/pricing"))
import firm_pricing as fp  # noqa: E402

T0 = dt.date(2026, 9, 24)
EXPIRIES = tuple(T0 + dt.timedelta(days=d) for d in (91, 182, 365, 730, 1095))
STRIKES = (70.0, 80.0, 90.0, 100.0, 110.0, 120.0, 130.0)
ONE_YEAR = EXPIRIES[2]
NODE = f"VOL:ABC:{ONE_YEAR.isoformat()}:90"


def surface() -> fp.GridSurface:
    """A skewed surface: 20 % at the money, 0.75 point lower per 10 % of strike at one year, steeper when shorter."""
    rows = []
    for e in EXPIRIES:
        t = (e - T0).days / 365.0
        rows.append(tuple(0.20 - 0.15 * (k / 100.0 - 1.0) / max(t, 0.25) ** 0.5 * 0.5 for k in STRIKES))
    fwds = tuple(100.0 * np.exp((0.03 - 0.015) * (e - T0).days / 365.0) for e in EXPIRIES)
    return fp.GridSurface(T0, EXPIRIES, STRIKES, tuple(rows), fwds)


def market() -> fp.MarketData:
    return fp.MarketData(asof=T0, spots={"ABC": 100.0}, curves={"USD": fp.FlatCurve(0.03, T0)},
                         vols={"ABC": surface()}, dividends={"ABC": fp.Dividends(div_yield=0.015)})


def book() -> list[tuple[fp.Instrument, float]]:
    obs = tuple(T0 + dt.timedelta(days=365 * i) for i in (1, 2, 3))
    return [
        (fp.EuropeanOption(id="CALL-1Y-100", underlying="ABC", currency="USD", strike=100.0, expiry=ONE_YEAR,
                           right="C"), 1_000.0),
        (fp.EuropeanOption(id="AMPUT-1Y-95", underlying="ABC", currency="USD", strike=95.0, expiry=ONE_YEAR, right="P",
                           exercise="american"), -500.0),
        (fp.BarrierOption(id="DOC-1Y-100-80", underlying="ABC", currency="USD", strike=100.0, expiry=ONE_YEAR,
                          right="C", barrier=80.0, kind="DO", monitoring="daily"), 800.0),
        (fp.VarianceSwap(id="VARSWAP-1Y", underlying="ABC", currency="USD", strike_vol=0.21, expiry=ONE_YEAR,
                         vega_notional=50_000.0), -1.0),
        (fp.Autocallable(id="AUTOCALL-3Y", underlying="ABC", currency="USD", notional=1_000_000.0, underlyings=("ABC",),
                         initial=(100.0,), obs_dates=obs, coupon=5.0, coupon_barrier=0.8, protection=0.8), -1.0),
    ]


@functools.cache
def book_prices() -> dict:
    md = market()
    out = {}
    for inst, q in book():
        r = fp.price(inst, md)
        out[inst.id] = {"pv": q * r.pv, "engine": r.engine, "unit": r.pv}
    out["total"] = sum(v["pv"] for v in out.values())
    return out


@functools.cache
def engine_table() -> dict:
    """The one-year 100 call and the 95 American put under every engine that supports them."""
    md = market()
    out = {}
    for inst, _ in book()[:2]:
        out[inst.id] = {e.name: fp.price(inst, md, engine=e).pv for e in fp.engines_for(inst, fp.BlackScholes())}
    return out


@functools.cache
def node_vega() -> dict:
    """Vega per point of each position to the (1y, 90) node, and the book's."""
    md = market()
    out = {inst.id: q * fp.sensitivities(inst, md, [NODE])[NODE] for inst, q in book()}
    out["total"] = sum(out.values())
    return out


@functools.cache
def crn_noise(seeds: int = 20) -> dict:
    """The autocallable's (1y, 90) vega from 20 independent seeds, with common random numbers (bumped and base prices
    share draws) and without (every snapshot draws afresh)."""
    md = market()
    ac, q = book()[-1]
    with_crn, without = [], []
    for s in range(seeds):
        for crn, dest in ((True, with_crn), (False, without)):
            eng = fp.MonteCarloEngine(seed_offset=s, crn=crn)
            dest.append(q * fp.sensitivities(ac, md, [NODE], engine=eng)[NODE])
    a, b = np.array(with_crn), np.array(without)
    return {"with": a, "without": b, "mean_with": float(a.mean()), "sd_with": float(a.std()),
            "mean_without": float(b.mean()), "sd_without": float(b.std()), "ratio": float(b.std() / a.std())}


@functools.cache
def bucket_profile() -> dict:
    """The book's vega per point by expiry (summed over strikes) from the full node grid."""
    md = market()
    total = {e: 0.0 for e in EXPIRIES}
    by_node = {}
    for inst, q in book():
        bv = fp.bucketed_vega(inst, md, EXPIRIES, STRIKES)
        for (e, k), v in bv.items():
            total[e] += q * v
            by_node[(e, k)] = by_node.get((e, k), 0.0) + q * v
    par = sum(q * fp.greeks(inst, md, which=("vega",))["vega"] for inst, q in book())
    return {"by_expiry": total, "by_node": by_node, "parallel": par}


SCENARIOS = (
    fp.Scenario("spot -20%", (fp.Bump("SPOT:ABC", -0.20, True),)),
    fp.Scenario("spot -10%", (fp.Bump("SPOT:ABC", -0.10, True),)),
    fp.Scenario("spot -5%", (fp.Bump("SPOT:ABC", -0.05, True),)),
    fp.Scenario("spot +5%", (fp.Bump("SPOT:ABC", 0.05, True),)),
    fp.Scenario("spot +10%", (fp.Bump("SPOT:ABC", 0.10, True),)),
    fp.Scenario("vol -5", (fp.Bump("VOL:ABC", -0.05),)),
    fp.Scenario("vol +5", (fp.Bump("VOL:ABC", 0.05),)),
    fp.Scenario("rates +100bp", (fp.Bump("CURVE:USD", 0.01),)),
    fp.Scenario("crash: -20%, +10 vol", (fp.Bump("SPOT:ABC", -0.20, True), fp.Bump("VOL:ABC", 0.10))),
    fp.Scenario("one month later", (fp.Bump("TIME", 30.0),)),
)


@functools.cache
def scenario_grid() -> dict:
    return fp.reprice(book(), market(), SCENARIOS)


@functools.cache
def crn_noise_big(seeds: int = 20, n_paths: int = 400_000) -> dict:
    """Exercise 7: the same node vega with four times the paths, common random numbers."""
    md = market()
    ac, q = book()[-1]
    engines = [fp.MonteCarloEngine(n_paths=n_paths, seed_offset=s) for s in range(seeds)]
    vals = np.array([q * fp.sensitivities(ac, md, [NODE], engine=e)[NODE] for e in engines])
    return {"mean": float(vals.mean()), "sd": float(vals.std())}
