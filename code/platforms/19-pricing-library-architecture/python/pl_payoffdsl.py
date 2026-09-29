"""Pricing-library architecture (One Quant Book 15, chapter 19).

Five products are written as payoff scripts and priced by firm.payoffdsl's engine, registered in Book 5's library
(firm.pricing) like any other: a European call (against the library's analytic engine), an Asian call and a worst-of
Phoenix autocallable with memory coupons (against the library's own Monte Carlo engine, on common random numbers: the
same paths), a daily down-and-out call (against the library's closed form with the Broadie-Glasserman-Kou shift), and
the client's product of the chapter's hook -- the autocallable with a lookback on the knock-in, for which the library
has no class. The interpreter's cost is compared with the compiled version's, and a lazy price shows the observer
pattern at work.
"""
from __future__ import annotations

import datetime as dt
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/payoffdsl"))
import firm_payoffdsl as D  # noqa: E402

FP = D.FP
ASOF = dt.date(2026, 9, 28)
EXPIRY = ASOF + dt.timedelta(days=365)
OBS = D.dates_after(ASOF, 6, 6)                         # six half-yearly observations, three years
N_PATHS = 100_000


def market(rate: float = 0.03) -> FP.MarketData:
    return FP.MarketData(ASOF, {"A": 100.0, "B": 100.0}, {"USD": FP.FlatCurve(rate, ASOF)},
                         vols={"A": FP.FlatVol(0.25), "B": FP.FlatVol(0.30)},
                         correlations={frozenset(("A", "B")): 0.6})


AUTOCALL = """state missed = 0;
at all {
  if perf >= barrier { pay cpn + missed; missed = 0; }
  else { missed = missed + cpn; }
}
at calls { if perf >= trigger { pay 100; stop; } }
at last {
  if perf < protection { pay 100 * min(perf, 1); } else { pay 100; }
}"""

LOOKBACK = """state missed = 0;
state lowest = 10;
at all {
  lowest = min(lowest, perf);
  if perf >= barrier { pay cpn + missed; missed = 0; }
  else { missed = missed + cpn; }
}
at calls { if perf >= trigger { pay 100; stop; } }
at last {
  if lowest < protection { pay 100 * min(perf, 1); } else { pay 100; }
}"""

AC_PARAMS = (("barrier", 0.7), ("cpn", 4.0), ("trigger", 1.0), ("protection", 0.6))
AC_DATES = (("all", OBS), ("calls", OBS[:-1]), ("last", OBS[-1:]))


def daily_dates(expiry: dt.date) -> tuple:
    """The library's own daily grid for barriers (Book 5): 252 steps a year, the expiry last."""
    n = max(1, round(market().t(expiry) * 252))
    return tuple(ASOF + dt.timedelta(days=round(365.0 * (i + 1) / 252.0)) for i in range(n - 1)) + (expiry,)


def products() -> dict:
    s = D.ScriptedInstrument
    fixings = D.dates_after(ASOF, 1, 12)
    barrier_days = daily_dates(EXPIRY)
    return {
        "European call": (
            s(id="EU", underlying="A", currency="USD", script="at expiry { pay max(S - 100, 0); }",
              dates=(("expiry", (EXPIRY,)),)),
            FP.EuropeanOption(id="EU", underlying="A", currency="USD", strike=100.0, expiry=EXPIRY, right="C"),
            FP.AnalyticEngine()),
        "Asian call": (
            s(id="AS", underlying="A", currency="USD",
              script="state total = 0; at fix { total = total + S; } at last { pay max(total / 12 - 100, 0); }",
              dates=(("fix", fixings), ("last", fixings[-1:]))),
            FP.AsianOption(id="AS", underlying="A", currency="USD", strike=100.0, expiry=fixings[-1], right="C",
                           fixing_dates=fixings),
            FP.MonteCarloEngine(n_paths=N_PATHS)),
        "down-and-out call": (
            s(id="DO", underlying="A", currency="USD",
              script="state out = 0; at days { if S <= 80 { out = 1; } } "
                     "at last { if out == 0 { pay max(S - 100, 0); } }",
              dates=(("days", barrier_days), ("last", (EXPIRY,)))),
            FP.BarrierOption(id="DO", underlying="A", currency="USD", strike=100.0, expiry=EXPIRY, right="C",
                             barrier=80.0, kind="DO", monitoring="daily"),
            FP.ClosedFormEngine()),
        "autocallable": (
            s(id="AC", underlying="A", currency="USD", script=AUTOCALL, dates=AC_DATES, params=AC_PARAMS,
              underlyings=("A", "B"), initial=(100.0, 100.0)),
            FP.Autocallable(id="AC", underlying="A", currency="USD", underlyings=("A", "B"), initial=(100.0, 100.0),
                            obs_dates=OBS, trigger=1.0, coupon=4.0, coupon_barrier=0.7, memory=True, protection=0.6,
                            notional=100.0),
            FP.MonteCarloEngine(n_paths=N_PATHS)),
        "autocallable, lookback knock-in": (
            s(id="AC", underlying="A", currency="USD", script=LOOKBACK, dates=AC_DATES, params=AC_PARAMS,
              underlyings=("A", "B"), initial=(100.0, 100.0)),
            None, None),
    }


def validation() -> list[dict]:
    md, eng = market(), D.ScriptEngine(n_paths=N_PATHS)
    rows = []
    for name, (script, lib, lib_engine) in products().items():
        cf = eng.cashflows(script, FP.BlackScholes(), md)
        p, se = float(cf.mean()), float(cf.std(ddof=1) / np.sqrt(len(cf)))
        ref = FP.price(lib, md, engine=lib_engine).pv if lib is not None else float("nan")
        rows.append({"product": name, "script": p, "se": se, "library": ref, "diff_se": (p - ref) / se,
                     "engine": lib_engine.name if lib_engine is not None else "none"})
    return rows


def deltas() -> dict:
    md = market()
    scr, lib, eng = products()["autocallable"]
    g_s = FP.greeks(scr, md, which=("delta",))["delta"]
    g_l = FP.greeks(lib, md, engine=eng, which=("delta",))["delta"]
    return {"script": g_s, "library": g_l}


def lazy_demo() -> dict:
    """A European call's price observing a rate quote: three changes, one recalculation when read."""
    rate = D.Quote(0.03)
    call = products()["European call"][1]

    def compute(r):
        return FP.price(call, market(r), engine=FP.AnalyticEngine()).pv

    lazy = D.LazyPrice(compute, rate)
    first = lazy.value
    for r in (0.031, 0.032, 0.035):
        rate.set(r)
    after = lazy.value
    again = lazy.value
    return {"first": first, "after": after, "again": again, "calculations": lazy.calculations}


def lookback_levels(levels=(0.5, 0.6, 0.7)) -> dict:
    """Exercise 7: the lookback autocallable at several knock-in levels."""
    base = products()["autocallable, lookback knock-in"][0]
    eng, md, out = D.ScriptEngine(n_paths=N_PATHS), market(), {}
    for lv in levels:
        params = tuple((k, lv if k == "protection" else v) for k, v in AC_PARAMS)
        inst = D.ScriptedInstrument(id=base.id, underlying="A", currency="USD", script=LOOKBACK, dates=AC_DATES,
                                    params=params, underlyings=("A", "B"), initial=(100.0, 100.0))
        out[lv] = eng.price(inst, FP.BlackScholes(), md)
    return out
